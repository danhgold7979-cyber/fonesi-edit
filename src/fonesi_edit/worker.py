"""Process entry; handlers are loaded lazily so jobs stay independent of Qt."""
from argparse import ArgumentParser
from pathlib import Path
import re
from threading import Thread,Event

from .storage import Store


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
        message = re.sub(r"(?i)(token|key|password|cookie|secret)=([^\s&]+)", r"\1=[redacted]", str(exc))
        store.fail(args.job, message, blocked=isinstance(exc, (PermissionError, FileNotFoundError)))
        return 1
    finally:done.set()


if __name__ == "__main__":
    raise SystemExit(main())
