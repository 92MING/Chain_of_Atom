'''You need to set OPENAI_API_KEY in environment variables before running this script.'''
from utils.classes.defer import DeferrableFunc
from utils.path_utils import NEO4J_BACKUP_DIR
from utils.neo4j_utils import *
connect_to_neo4j()

from atoms import *
from data_struct.atom import *

@DeferrableFunc
def run(backup_neo4j=True):
    DeferrableFunc.defer(lambda :neo4j_session().close() if neo4j_session() is not None else None)
    if backup_neo4j:
        DeferrableFunc.defer(lambda :neo4j_driver(False).backup(dir_path=NEO4J_BACKUP_DIR) if neo4j_driver(False) is not None and os.path.exists(NEO4J_BACKUP_DIR) else None)

    from data_struct.thinker import Thinker
    thinker = Thinker()
    # thinker.thinking_process_ipo('With only +, -, *, /, how to get 24 from 4, 5, 6, 10?')
    thinker.thinking_process_ipo('7 orange and 3 apple cost 44 dollars and 6 orange and 6 apple cost 48 dollars, what are the prices of apple and orange?')

if __name__ == '__main__':
    run()
