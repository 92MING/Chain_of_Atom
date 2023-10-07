'''PromptedObj is those objects that having a prompt for describing itself.'''
from utils.global_value_utils import GetOrAddGlobalValue
from utils.neo4j_utils import neo4j_session
from utils.AI_utils import get_embedding_vector, DEFAULT_EMBED_DIMENSION
from typing import Union
import numpy as np

class PromptedObjMetaMeta(type):
    def __new__(self, *args, **kwargs):
        metacls:'PromptedObjMeta' = super().__new__(self, *args, **kwargs)
        if metacls.BASE_CLS_NAME is not None and metacls.ADD_TO_KG:
            # try to create vector index if not exist
            session = neo4j_session()
            if not session.has_index(f'{metacls.BASE_CLS_NAME}_INDEX'):
                session.create_vector_index(name=f'{metacls.BASE_CLS_NAME}_INDEX', label=metacls.BASE_CLS_NAME,
                                            propertyKey='prompt_embed', vector_dimension=DEFAULT_EMBED_DIMENSION,
                                            similarity_function='cosine', overwrite=False)
        return metacls

_INIT_NODE_CYPHER_LINES:dict = GetOrAddGlobalValue('_CREATE_NODE_CYPHER_LINES', dict())
'''Saving all commands during the definition of PromptedObj. They will be executed after all PromptedObj are defined.'''
class PromptedObjMeta(type, metaclass=PromptedObjMetaMeta):
    BASE_CLS_NAME:str = None
    '''override this to determine the base class' name'''
    ADD_TO_KG:bool = True
    '''
    Override this to determine whether a subclass should be added as a node to the knowledge graph.
    Vector index will also be added to the knowledge graph if not exist.
    '''
    INIT_PRIORITY:int = 0
    '''Override this to determine the priority of executing the initialization cyphers. The larger the later.'''

    @classmethod
    def cls_dict(cls):
        '''dict for saving all subclass of this class'''
        return GetOrAddGlobalValue(f'_{cls.BASE_CLS_NAME}_SUBCLS_DICT', dict())
    @classmethod
    def cls_id_dict(cls):
        '''dict saving all subclass and use their id as key'''
        return GetOrAddGlobalValue(f'_{cls.BASE_CLS_NAME}_SUBCLS_ID_DICT', dict())
    @classmethod
    def subcls_exist_in_kg(cls, subcls_name:str):
        '''check if a subclass exists in knowledge graph. You can also override this to customize the checking method.'''
        return neo4j_session().run(f'match (n:{cls.BASE_CLS_NAME}) where n.name="{subcls_name}" return n').single() is not None
    @classmethod
    def subcls_need_update(cls, subcls:Union[type, 'PromptedObj'])->bool:
        '''Check if a subclass need to be updated in knowledge graph. You can also override this to customize the checking method.'''
        current_node_prompt = neo4j_session().run(f'match (n:{cls.BASE_CLS_NAME}) where n.name="{subcls.cls_name()}" return n.prompt').single()[0]
        return current_node_prompt != subcls.prompt
    @classmethod
    def create_subcls_cyphers(cls, subcls:Union[type,'PromptedObj'])->Union[list, str]:
        '''
        Override this to create a node for a subclass in knowledge graph.
        :param subcls: the subclass to be updated
        :return: You MUST return a list/str of cypher lines for creating the node.
        '''
        raise NotImplementedError
    @classmethod
    def update_subcls_cyphers(cls, subcls:Union[type,'PromptedObj'])->Union[list, str]:
        '''
        Override this to update a node for a subclass in knowledge graph.
        This function will only be carry out when the prompt of the subclass is changed.
        :param subcls: the subclass to be updated
        :return: You MUST return a list/str of cypher lines for updating the node.
        '''
        raise NotImplementedError

    def __new__(self, *args, **kwargs):
        global _CREATE_NODE_CYPHER_LINES, _UPDATE_NODE_CYPHER_LINES
        cls_name = args[0]
        if cls_name != self.BASE_CLS_NAME and cls_name not in self.cls_dict() and cls_name!='TempPromptedObject':
            cls:'PromptedObj' = super().__new__(self, *args, **kwargs)
            if not hasattr(cls, 'prompt') or cls.prompt is None:
                raise Exception(f"{self.BASE_CLS_NAME}'s subclass '{cls_name}' should have a prompt.")
            self.cls_dict()[cls_name] = cls
            if self.ADD_TO_KG:
                if cls.INIT_PRIORITY not in _INIT_NODE_CYPHER_LINES:
                    _INIT_NODE_CYPHER_LINES[cls.INIT_PRIORITY] = []
                if not self.subcls_exist_in_kg(cls_name):
                    cyphers = self.create_subcls_cyphers(cls)
                    if isinstance(cyphers, str):
                        _INIT_NODE_CYPHER_LINES[cls.INIT_PRIORITY].append(cyphers)
                    else:
                        _INIT_NODE_CYPHER_LINES[cls.INIT_PRIORITY].extend(self.create_subcls_cyphers(cls))
                    if self.BASE_CLS_NAME == 'Atom':
                        cyphers1 = self.build_output_relationship_value(cls)
                        cyphers2 = self.build_input_relationship_value(cls)
                        _INIT_NODE_CYPHER_LINES[cls.INIT_PRIORITY].append(cyphers1)
                        _INIT_NODE_CYPHER_LINES[cls.INIT_PRIORITY].append(cyphers2)

                elif self.subcls_need_update(cls):
                    cyphers = self.update_subcls_cyphers(cls)
                    if isinstance(cyphers, str):
                        _INIT_NODE_CYPHER_LINES[cls.INIT_PRIORITY].append(cyphers)
                    else:
                        _INIT_NODE_CYPHER_LINES[cls.INIT_PRIORITY].extend(self.update_subcls_cyphers(cls))
            return cls
        if cls_name == self.BASE_CLS_NAME:
            return super().__new__(self, *args, **kwargs)
        else:
            return self.cls_dict()[cls_name]

class PromptedObj:
    '''
    Base class of all prompted object. You should use this class combined with your custom PromptedObjMeta.
    e.g.::
        class MyPromptedObjMeta(metaclass=PromptedObjMeta):
            ...
        class MyPromptedObj(PromptedObj, metaclass=MyPromptedObjMeta):
            ...
    '''

    prompt:str = None
    '''the prompt for describing the object. Override this in subclass'''

    _prompt_embedding:np.array = None # for caching the embedding vector of the prompt
    _kg_id = None # will be assigned during the creation of the node in knowledge graph

    @classmethod
    def cls_name(cls):
        return cls.__qualname__
    @classmethod
    def kg_id(cls: Union['PromptedObjMeta', 'PromptedObj']):
        '''return the element id in KG.'''
        if cls._kg_id is None and cls.cls_name() != 'PromptedObj':
            cls._kg_id = neo4j_session().run(f'match (n:{cls.BASE_CLS_NAME}) where n.name="{cls.cls_name()}" return elementId(n)').single()[0]
        return cls._kg_id
    @classmethod
    def find_subcls_byID(cls, id):
        '''find subclass by id'''
        cls_id_dict = cls.cls_id_dict()
        if id in cls_id_dict:
            return cls_id_dict[id]
        for subcls in cls.all_subclses():
            if subcls.kg_id() == id:
                cls_id_dict[id] = subcls
                return subcls
        raise KeyError(f'Cannot find subclass with id {id}')
    @classmethod
    def prompt_embedding(cls)->np.array:
        '''return the embedding vector of the prompt'''
        if cls._prompt_embedding is None:
            cls._prompt_embedding = get_embedding_vector(cls.prompt)
        return cls._prompt_embedding
    @classmethod
    def all_subclses(cls):
        '''return all subclass of this class'''
        return cls.__subclasses__()

__all__ = ['PromptedObjMeta', 'PromptedObj']
