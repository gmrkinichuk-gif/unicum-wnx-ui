"""Recoverable replacement with the file operations available in WoT Python."""
import json
import os
import tempfile


def replace(source, target):
    # Windows Python 2 cannot rename over an existing file. A restart can
    # recover the committed file if it lands between the two renames.
    if os.name != 'nt' or not os.path.exists(target):
        os.rename(source, target)
        return
    previous = target + '.previous'
    if os.path.exists(previous):
        os.unlink(previous)
    os.rename(target, previous)
    try:
        os.rename(source, target)
    except OSError:
        os.rename(previous, target)
        raise


def recover(path):
    previous = path + '.previous'
    if not os.path.exists(path) and os.path.exists(previous):
        os.rename(previous, path)


def write_json(path, data):
    directory = os.path.dirname(path) or '.'
    if not os.path.isdir(directory):
        os.makedirs(directory)
    recover(path)
    descriptor, temporary = tempfile.mkstemp(dir=directory, suffix='.tmp')
    try:
        with os.fdopen(descriptor, 'wb') as handle:
            json.dump(data, handle, indent=2, sort_keys=True)
            handle.flush()
            os.fsync(handle.fileno())
        replace(temporary, path)
    finally:
        _remove(temporary)
    _remove(path + '.previous')


def _remove(path):
    try:
        os.unlink(path)
    except OSError:
        pass
