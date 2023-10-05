'''This is the module for containing for atom services.'''

from .math_atoms import *
from .text_atoms import *
from .combination_atom import *

# init the neo4j database
from utils.neo4j_utils import neo4j_session
from data_struct.promptedObj import _INIT_NODE_CYPHER_LINES
with neo4j_session().begin_transaction() as tx:
    priority_list = list(_INIT_NODE_CYPHER_LINES.keys())
    priority_list.sort()
    for priority in priority_list:
        for line in _INIT_NODE_CYPHER_LINES[priority]:
            tx.run(line)

# init _kg_id for all PromptedObj
from data_struct.promptedObj import PromptedObj
session = neo4j_session()
for subcls in PromptedObj.__subclasses__():
    if subcls.BASE_CLS_NAME != None:
        subcls.kg_id() # this will init the _kg_id variable
