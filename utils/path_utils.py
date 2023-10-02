import os

CACHE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'cache'))

EMBEDDING_CACHE_DB_PATH = os.path.join(CACHE_DIR, 'embedding_cache.db')