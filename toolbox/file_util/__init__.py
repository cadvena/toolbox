from datetime import datetime as dtdt
from toolbox.pathlib import Path, copyfile


def timestamp_str(utc=True):
    f = dtdt.utcnow if utc else dtdt.now
    if utc:
        return f().isoformat()[:19].replace(".", "_").replace(":", "-")
    else:
        return f().isoformat()[:19].replace(".", "_").replace(":", "-")


def backup_file(orig_file):
    orig = Path(orig_file)
    if not orig.exists():
        pass
    elif not orig.is_file():
        raise FileNotFoundError(f'File System Object "ora_snippets_file" exists but is not a file.')
    else:
        bck = timestamp_str()
        bck = orig.with_name(orig.stem + "_" + bck + orig.suffix)
        copyfile(src=orig_file, dst=bck)
