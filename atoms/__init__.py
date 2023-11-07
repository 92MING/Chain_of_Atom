'''This is the module for containing for atom services.'''

from .math_atoms import *
from .text_atoms import *
from .combination_atom import *
from data_struct.converter import *
import os

# init the neo4j database
from utils.neo4j_utils import neo4j_session
from data_struct.promptedObj import _INIT_NODE_CYPHER_LINES
with neo4j_session().begin_transaction() as tx:
    priority_list = list(_INIT_NODE_CYPHER_LINES.keys())
    priority_list.sort()
    for priority in priority_list:
        for line in _INIT_NODE_CYPHER_LINES[priority]:
            tx.run(line)
_INIT_NODE_CYPHER_LINES = dict()

# init _kg_id for all PromptedObj
from data_struct.promptedObj import PromptedObj
session = neo4j_session()
for subcls in PromptedObj.all_subclses():
    if subcls.BASE_CLS_NAME != None:
        for subsubcls in subcls.all_subclses():
            subsubcls.kg_id() # this will init the _kg_id variable

dirpath = os.path.dirname(os.path.realpath(__file__))
filepath = os.path.join(dirpath, 'Storage.txt')
with neo4j_session().begin_transaction() as tx:
    with open(filepath, 'r') as store:
        line = 0
        mapping = {'str': str, 'int': int, 'float': float, 'list': list, 'dict': dict, 'bool': bool}
        while line < len(store.readlines()):
            temp = store.readlines()[line][:-1]
            if temp.lower() == 'value':
                sub_cls_name = store.readlines()[line+1][:-1]
                prompt = store.readlines()[line+2][:-1]
                expected_type = mapping[store.readlines()[line+3][:-1]]
                converter = Converter[expected_type]
                example_prompt = store.readlines()[line+5][:-1]
                TempPromptedObj = type(sub_cls_name, (Value,), {
                    "prompt": prompt,
                    "expected_type": expected_type,
                    "converter": converter,
                    "example_prompt": example_prompt
                })
                line += 6
                cypher = TempPromptedObj.create_subcls_cyphers()
                session.run(cypher)
                TempPromptedObj.kg_id()

            else:
                sub_cls_name = store.readlines()[line+1][:-1]
                prompt = store.readlines()[line + 2][:-1]
                inputs = tuple(store.readlines()[line + 3][:-1].split(","))
                outputs = tuple(store.readlines()[line + 4][:-1].split(","))
                length = int(store.readlines()[line + 5][:-1])
                line += 6
                run = exec(store.readlines()[line:line+length])
                line += length
                length = int(store.readlines()[line][:-1])
                function_create = exec(store.readlines()[line:line+length])
                TempPromptedObj = type(sub_cls_name, (Atom,), {
                    "prompt": prompt,
                    "inputs": inputs,
                    "outputs": outputs,

                    "run": run,
                    "function_create": function_create
                })
                cypher = TempPromptedObj.create_subcls_cyphers()
                session.run(cypher)
                TempPromptedObj.kg_id()
                cypher1 = TempPromptedObj.build_output_relationship_value()
                cypher2 = TempPromptedObj.build_input_relationship_value()
                session.run(cypher1)
                session.run(cypher2)