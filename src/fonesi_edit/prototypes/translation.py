"""Official Google Translation v2 adapter proof; live use requires user config."""
from dataclasses import replace
import html
import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .subtitles import Cue


class TranslationNotConfigured(RuntimeError):
    pass


def translate(cues: list[Cue], target: str = "vi", source: str = "zh") -> list[Cue]:
    key = os.environ.get("FONESI_GOOGLE_TRANSLATE_API_KEY")
    if not key:
        raise TranslationNotConfigured("Thiếu cấu hình FONESI_GOOGLE_TRANSLATE_API_KEY; chưa gọi API")
    if not cues:
        return []
    if len(cues) > 32:
        raise ValueError("P02 chỉ thử tối đa 32 cue/lần; batch/cache/quota thuộc P06")
    body = json.dumps({"q": [c.text for c in cues], "target": target,
                       "source": source, "format": "text"}).encode("utf-8")
    request = Request("https://translation.googleapis.com/language/translate/v2", data=body,
                      headers={"Content-Type": "application/json", "X-Goog-Api-Key": key}, method="POST")
    try:
        with urlopen(request, timeout=30) as response:
            data = json.load(response)
    except HTTPError as exc:
        raise RuntimeError(f"Translation API HTTP {exc.code}; không tự retry request có thể đã tính phí") from None
    except (URLError, TimeoutError):
        raise RuntimeError("Không xác nhận kết quả API; cần đối chiếu trước khi thử lại") from None
    translations = data.get("data", {}).get("translations", [])
    if len(translations) != len(cues):
        raise RuntimeError("API trả số lượng cue không khớp")
    result = []
    for cue, item in zip(cues, translations, strict=True):
        text = html.unescape(item.get("translatedText", "")).strip()
        if not text:
            raise RuntimeError("API trả cue rỗng")
        result.append(replace(cue, text=text))
    return result
