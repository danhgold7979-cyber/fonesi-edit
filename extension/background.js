'use strict';
const domains={YouTube:['youtube.com','google.com'],Facebook:['facebook.com'],TikTok:['tiktok.com'],Instagram:['instagram.com'],Threads:['threads.com','threads.net','instagram.com'],X:['x.com','twitter.com'],Bilibili:['bilibili.com'],Douyin:['douyin.com'],Xiaohongshu:['xiaohongshu.com'],Kuaishou:['kuaishou.com']};
const pending=new Map();
async function sync(platform){
  const {bridgeToken,syncPlatforms=[]}=await chrome.storage.local.get(['bridgeToken','syncPlatforms']);
  if(!bridgeToken||!syncPlatforms.includes(platform)||!domains[platform])return;
  const cookies=[];for(const domain of domains[platform])cookies.push(...await chrome.cookies.getAll({domain}));
  try{await chrome.runtime.sendNativeMessage('com.fonesi.bridge',{type:'snapshot',platform,token:bridgeToken,cookies});}
  catch(error){/* No raw session or error payload is logged. User can inspect state in the app. */}
}
chrome.cookies.onChanged.addListener(async change=>{
  const {syncPlatforms=[]}=await chrome.storage.local.get('syncPlatforms');const host=change.cookie.domain.replace(/^\./,'');
  for(const platform of syncPlatforms){if(!(domains[platform]||[]).some(d=>host===d||host.endsWith('.'+d)))continue;
    clearTimeout(pending.get(platform));pending.set(platform,setTimeout(()=>{pending.delete(platform);sync(platform);},2000));}
});
chrome.alarms.create('fonesi-session-sync',{periodInMinutes:10});
chrome.alarms.onAlarm.addListener(async alarm=>{if(alarm.name==='fonesi-session-sync'){const {syncPlatforms=[]}=await chrome.storage.local.get('syncPlatforms');for(const platform of syncPlatforms)await sync(platform);}});
