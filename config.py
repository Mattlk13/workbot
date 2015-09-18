import os
import tempfile

DEBUG = True
SECRET_KEY = '...'

CACHE_DIR = tempfile.gettempdir()
GIT_CACHE_FILE = os.path.join(CACHE_DIR, 'gitdirs.json')