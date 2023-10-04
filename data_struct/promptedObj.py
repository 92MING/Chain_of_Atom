'''PromptedObj is those objects that having a prompt for describing itself.'''
from utils.global_value_utils import GetOrAddGlobalValue
from utils.neo4j_utils import neo4j_session
from utils.AI_utils import get_embedding_vector
from typing import Union

class PromptedObjMeta(type):
    BASE_CLS_NAME:str = None
    '''override this to determine the base class' name'''
    ADD_TO_KG:bool = True
    '''
    Override this to determine whether a subclass should be added as a node to the knowledge graph.
    Vector index will also be added to the knowledge graph if not exist.
    '''

    _SUBCLS_DICT = None
    @classmethod
    def cls_dict(cls):
        '''dict for saving all subclass of this class'''
        if cls._SUBCLS_DICT is None:
            cls._SUBCLS_DICT = GetOrAddGlobalValue(f'_{cls.BASE_CLS_NAME}_SUBCLS_DICT', dict())
        return cls._SUBCLS_DICT
    @classmethod
    def subcls_exist_in_kg(cls, subcls_name:str):
        '''check if a subclass exists in knowledge graph'''
        return neo4j_session().run(f'match (n:{cls.BASE_CLS_NAME}) where n.name="{subcls_name}" return n').single() is not None
    @classmethod
    def create_subcls_node_in_kg(cls, subcls:Union[type,'PromptedObj']):
        '''
        Override this to create a node for a subclass in knowledge graph.
        :param subcls: the subclass to be updated
        '''
        raise NotImplementedError
    @classmethod
    def update_subcls_node_in_kg(cls, subcls:Union[type,'PromptedObj']):
        '''
        Override this to update a node for a subclass in knowledge graph.
        This function will only be carry out when the prompt of the subclass is changed.
        :param subcls: the subclass to be updated
        '''
        raise NotImplementedError

    def __new__(self, *args, **kwargs):
        cls_name = args[0]
        if cls_name != self.BASE_CLS_NAME and cls_name not in self.cls_dict():
            cls:'PromptedObj' = super().__new__(self, *args, **kwargs)
            if not hasattr(cls, 'prompt') or cls.prompt is None:
                raise Exception(f"{self.BASE_CLS_NAME}'s subclass '{cls_name}' should have a prompt.")
            self.cls_dict()[cls_name] = cls
            if self.ADD_TO_KG:
                if not self.subcls_exist_in_kg(cls_name):
                    self.create_subcls_node_in_kg(cls_name)
                else:
                    current_node_prompt = neo4j_session().run(f'match (n:{self.BASE_CLS_NAME}) where n.name="{cls_name}" return n.prompt').single()[0]
                    if current_node_prompt != cls.prompt:
                        self.update_subcls_node_in_kg(cls)
            return cls
        if cls_name == self.BASE_CLS_NAME:
            return super().__new__(self, *args, **kwargs)
        else:
            return self.cls_dict()[cls_name]

class PromptedObj:
    prompt:str = None
    _kg_id = None # will be assigned during the creation of the node in knowledge graph

    @classmethod
    def cls_name(cls):
        return cls.__qualname__
    @classmethod
    def kg_id(cls):
        '''return the element id in KG.'''
        return cls._kg_id
    @classmethod
    def prompt_embedding(cls):
        '''return the embedding vector of the prompt'''
        return get_embedding_vector(cls.prompt)
    @classmethod
    def all_subcls(cls):
        '''return all subclass of this class'''
        return cls.__subclasses__()

__all__ = ['PromptedObjMeta', 'PromptedObj']

class A:
    pass