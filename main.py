'''You need to set OPENAI_API_KEY in environment variables before running this script.'''
from utils.classes.defer import DeferrableFunc
@DeferrableFunc
def run(backup_neo4j=True):
    import os
    from utils.path_utils import NEO4J_BACKUP_DIR
    from utils.neo4j_utils import neo4j_session, neo4j_driver,connect_to_neo4j
    connect_to_neo4j(port=7687)
    DeferrableFunc.defer(lambda :neo4j_session().close() if neo4j_session() is not None else None)
    if backup_neo4j:
        DeferrableFunc.defer(lambda :neo4j_driver(False).backup(dir_path=NEO4J_BACKUP_DIR) if neo4j_driver(False) is not None and os.path.exists(NEO4J_BACKUP_DIR) else None)

    from data_struct.thinker import Thinker
    thinker = Thinker()
    thinker.think('With only +, -, *, /, how to get 24 from 4, 5, 6, 10?')

if __name__ == '__main__':
    run()
