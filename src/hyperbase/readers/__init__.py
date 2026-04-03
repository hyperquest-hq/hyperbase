from hyperbase.readers.reader import Reader, get_reader, list_readers, register_reader

from hyperbase.readers import wikipedia  # noqa: F401
from hyperbase.readers import url        # noqa: F401
from hyperbase.readers import txt        # noqa: F401

__all__ = ['Reader', 'get_reader', 'list_readers', 'register_reader']
