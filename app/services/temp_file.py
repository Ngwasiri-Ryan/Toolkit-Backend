import tempfile
import os
from contextlib import contextmanager

@contextmanager
def temp_file(suffix: str = "") -> str:
    """Context manager for creating a temporary file and ensuring its deletion."""
    fd, path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    try:
        yield path
    finally:
        if os.path.exists(path):
            try:
                os.unlink(path)
            except OSError:
                pass
