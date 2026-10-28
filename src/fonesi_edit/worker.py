"""Process entry; handlers are loaded lazily so jobs stay independent of Qt."""
from argparse import ArgumentParser
from pathlib import Path
import re
from threading import Thread,Event
from urllib.parse import urlsplit, urlunsplit

from .storage import Store


_SENSITIVE_ASSIGNMENT = re.compile(
    r"""(?i)\b(password|passwd|pwd|cookie|cookies|api[_-]?key|api[_-]?secret|access[_-]?token|refresh[_-]?token|session[_-]?cookie|session[_-]?token|session[_-]?id|session[_-]?key|client[_-]?secret|secret|signature|sig|signed[_-]?url|authorization|x-api-key|bearer[_-]?token|auth[_-]?token|private[_-]?key|csrf[_-]?token|jwt(?:[_-]?token)?)\b(\s*[:=]\s*)(?:"[^"]*"|'[^']*'|[^\s,;&]+)"""
)
_BEARER_CREDENTIAL = re.compile(r"(?i)\b(Bearer|Basic)\s+[A-Za-z0-9._~+/=-]+")


def sanitize_error_message(message, limit=3000):
    """Remove common credential values and signed URL query strings from worker errors."""
    text = str(message)
    text = _BEARER_CREDENTIAL.sub(r"\1 [redacted]", text)
    text = _SENSITIVE_ASSIGNMENT.sub(r"\1\2[redacted]", text)

    def safe_url(match):
        value = match.group(0)
        trailing = ""
        while value and value[-1] in ".,);]}":
            trailing = value[-1] + trailing
            value = value[:-1]
        try:
            parts = urlsplit(value)
            hostname = parts.hostname
            if not hostname:
                return "[URL redacted]" + trailing
            host = f"[{hostname}]" if ":" in hostname and not hostname.startswith("[") else hostname
            try:
                port = parts.port
            except ValueError:
                port = None
            if port is not None:
                host = f"{host}:{port}"
            safe = urlunsplit((parts.scheme, host, parts.path, "", ""))
            return safe + trailing
        except (TypeError, ValueError):
            return "[URL redacted]" + trailing

    text = re.sub(r"https?://[^\s<>\"']+", safe_url, text)
    return text[:max(0, int(limit))]


class Cancel:
    def __init__(self, store, job_id):
        self.store, self.job_id = store, job_id

    def is_set(self):
        return bool(self.store.job(self.job_id)["cancel_requested"])


def execute(store, job):
    kind, payload = job["kind"], job["payload"]
    from .prototypes.tools import configure_tools
    configure_tools(payload.get('_tools',{}))
    cancel = Cancel(store, job["id"])
    progress = lambda value: store.progress(job["id"], value)
    if cancel.is_set():
        raise RuntimeError("Canceled")
    if kind == "render":
        if "composition" in payload:
            from .render import render_composition
            from .domain import Composition
            return render_composition(Composition.from_dict(payload["composition"]), Path(payload["output"]), progress, cancel)
        from .prototypes.media import RenderSpec, render
        settings = payload.get("settings", {})
        for key in ("font", "logo", "subtitles"):
            if settings.get(key):
                settings[key] = Path(settings[key])
        return render(Path(payload["source"]), Path(payload["output"]), RenderSpec(**settings), progress, cancel)
    if kind in {"scan", "download"}:
        from .downloads import execute_download_job
        return execute_download_job(store, job, progress, cancel)
    if kind == "translate":
        from .subtitles import execute_translation
        return execute_translation(store, payload, progress, cancel)
    raise ValueError(f"Unknown job type: {kind}")


def main(argv=None):
    parser = ArgumentParser()
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--job", required=True)
    args = parser.parse_args(argv)
    store = Store(args.db)
    job = store.job(args.job)
    done=Event()
    def heartbeat():
        while not done.wait(5):store.heartbeat(args.job)
    watcher=Thread(target=heartbeat,daemon=True);watcher.start()
    try:
        store.finish(args.job, execute(store, job))
        return 0
    except Exception as exc:
        message = sanitize_error_message(exc)
        store.fail(args.job, message, blocked=isinstance(exc, (PermissionError, FileNotFoundError)))
        return 1
    finally:done.set()


if __name__ == "__main__":
    raise SystemExit(main())
