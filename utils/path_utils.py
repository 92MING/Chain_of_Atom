import os

CACHE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'cache'))
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

EMBEDDING_CACHE_DB_PATH = os.path.join(CACHE_DIR, 'embedding_cache.db')
if not os.path.exists(EMBEDDING_CACHE_DB_PATH):
    open(EMBEDDING_CACHE_DB_PATH, 'w').close()

NEO4J_BACKUP_DIR = os.path.join(CACHE_DIR, 'neo4j_backup')

