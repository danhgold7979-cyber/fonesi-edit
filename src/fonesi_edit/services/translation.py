"""Opt-in LibreTranslate adapter, durable quota reservation and uncertain-outcome safety."""
from dataclasses import dataclass, replace
from urllib.parse import urlparse
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
import json
import os
import time
from ..core.model import Cue,digest,uid
from ..core.storage import Store


class TranslationUncertain(RuntimeError):pass
class TranslationConfiguration(ValueError):pass


@dataclass(frozen=True)
class TranslationConfig:
    endpoint:str
    source:str
    target:str='vi'
    provider_version:str='configured'
    enabled:bool=False
    consent_remote:bool=False
    credential_env:str='FONESI_TRANSLATION_KEY'
    character_limit:int=0
    timeout:int=30

    def validate(self):
        if not self.enabled or not self.consent_remote:raise TranslationConfiguration('Translation is not enabled/consented; no request was sent')
        parsed=urlparse(self.endpoint)
        if parsed.scheme!='https' and not (parsed.scheme=='http' and parsed.hostname in {'127.0.0.1','localhost','::1'}):raise TranslationConfiguration('HTTPS required except explicit localhost provider')
        if parsed.username or parsed.password or parsed.query or parsed.fragment:raise TranslationConfiguration('Endpoint must not contain credentials/query/fragment')
        if self.character_limit<=0:raise TranslationConfiguration('Set an explicit character budget before translation')


class Translator:
    def __init__(self,store:Store,config:TranslationConfig):self.store=store;self.config=config

    def translate(self,cues:list[Cue],selected:set[str]|None=None) -> list[Cue]:
        self.config.validate();out=[replace(c) for c in cues]
        todo=[]
        scope=digest({'endpoint':self.config.endpoint,'version':self.config.provider_version,'source':self.config.source,'target':self.config.target})
        for c in out:
            if c.locked or selected is not None and c.id not in selected:continue
            key=digest({'text':c.text,'source':self.config.source,'target':self.config.target,'version':self.config.provider_version})
            cached=self.store.cache_get('translation:'+scope,key)
            if cached is not None:c.translation=cached['text']
            else:todo.append((c,key))
        if not todo:return out
        chars=sum(len(c.text) for c,_ in todo);request_id=uid()
        with self.store.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT payload FROM objects WHERE namespace=? AND id=?',('translation_budget',scope)).fetchone()
            budget=json.loads(row[0]) if row else {'reserved':0,'completed':0,'uncertain':0}
            if budget['reserved']+budget['completed']+budget['uncertain']+chars>self.config.character_limit:raise TranslationConfiguration('Character budget reached; no new request sent')
            budget['reserved']+=chars
            db.execute('INSERT INTO objects VALUES(?,?,?) ON CONFLICT(namespace,id) DO UPDATE SET payload=excluded.payload',('translation_budget',scope,json.dumps(budget)))
        self.store.put('translation_request',request_id,{'state':'reserved','scope':scope,'characters':chars})
        payload={'q':[c.text for c,_ in todo],'source':self.config.source,'target':self.config.target,'format':'text'}
        key=os.environ.get(self.config.credential_env)
        if key:payload['api_key']=key
        request=Request(self.config.endpoint.rstrip('/')+'/translate',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','X-Request-ID':request_id},method='POST')
        state='uncertain'
        try:
            with urlopen(request,timeout=self.config.timeout) as response:
                body=response.read(8*1024*1024)
            data=json.loads(body);values=data.get('translatedText')
            if isinstance(values,str) and len(todo)==1:values=[values]
            if not isinstance(values,list) or len(values)!=len(todo) or not all(isinstance(x,str) and x.strip() for x in values):raise TranslationUncertain('Provider returned incomplete/unmappable response; not cached')
            for (c,cache_key),value in zip(todo,values):
                c.translation=value;self.store.cache_put('translation:'+scope,cache_key,{'text':value})
            state='completed';return out
        except HTTPError as exc:
            if exc.code in {400,401,403,429}:state='rejected'
            raise TranslationUncertain(f'Provider HTTP {exc.code}; request {request_id}; no automatic retry') from None
        except (TimeoutError,URLError,json.JSONDecodeError) as exc:
            raise TranslationUncertain(f'Request {request_id} may have been processed; reconcile before retry ({type(exc).__name__})') from None
        finally:
            with self.store.connection() as db:
                db.execute('BEGIN IMMEDIATE');row=db.execute('SELECT payload FROM objects WHERE namespace=? AND id=?',('translation_budget',scope)).fetchone();budget=json.loads(row[0]);budget['reserved']-=chars
                if state in {'completed','uncertain'}:budget[state]+=chars
                db.execute('UPDATE objects SET payload=? WHERE namespace=? AND id=?',(json.dumps(budget),'translation_budget',scope))
            self.store.put('translation_request',request_id,{'state':state,'scope':scope,'characters':chars})
