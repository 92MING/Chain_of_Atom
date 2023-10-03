import os

CACHE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'cache'))
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

EMBEDDING_CACHE_DB_PATH = os.path.join(CACHE_DIR, 'embedding_cache.db')
if not os.path.exists(EMBEDDING_CACHE_DB_PATH):
    open(EMBEDDING_CACHE_DB_PATH, 'w').close()

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

ATOM_DATA_PATH = os.path.join(DATA_DIR, 'atom_data.db')
if not os.path.exists(ATOM_DATA_PATH):
    open(ATOM_DATA_PATH, 'w').close()

