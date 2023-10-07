from data_struct.converter import Converter
from data_struct.promptedObj import *
import numpy as np
from utils.AI_utils import get_embedding_vector
from typing import Callable, Union
from utils.neo4j_utils import neo4j_session

class ValueMeta(PromptedObjMeta):
    BASE_CLS_NAME = 'Value'
    ADD_TO_KG = True

    # region override
    @classmethod
    def subcls_exist_in_kg(cls, subcls_name: str):
        exist = (neo4j_session().run(f'match (n:Value) where n.name="{subcls_name}" return n').single() is not None)
        if not exist:
            # check if it is included in a merged value node
            exist = (neo4j_session().run(f'match (n:MergedValue) where "{subcls_name}" in n.from return n').single() is not None)
        return exist
    @classmethod
    def subcls_need_update(cls, subcls: Union[type, 'PromptedObj']) -> bool:
        current_node_prompt = neo4j_session().run(f'match (n:{cls.BASE_CLS_NAME}) where n.name="{subcls.cls_name()}" return n.prompt').single()
        # if not found, current_node_prompt is None
        # if not found, means it is included in a merged value node. It will not be updated(currently not supported)
        if current_node_prompt is not None:
            current_node_prompt = current_node_prompt[0] # real n.prompt
        return current_node_prompt is not None and current_node_prompt != subcls.prompt
    @classmethod
    def create_subcls_cyphers(cls, subcls: Union['Value', type]):
        return f"""
        CREATE (n:{cls.BASE_CLS_NAME} 
        {{
            name: "{subcls.cls_name()}", 
            prompt: "{subcls.prompt}",
            expected_type: "{subcls._expected_type_name()}", 
            converter: "{subcls._converter_name()}", 
            default: "{subcls.default}",
            example_prompt: "{subcls.example_prompt}", 
            prompt_embed: {subcls.prompt_embedding().tolist()}
        }})
        """
    @classmethod
    def update_subcls_cyphers(cls, subcls: Union['Value', type]):
        return f"""
        MATCH (n:{cls.BASE_CLS_NAME} {{name: "{subcls.cls_name()}"}}) 
        SET 
            n.prompt = "{subcls.prompt}",
            n.expected_type = "{subcls._expected_type_name()}",
            n.converter = "{subcls._converter_name()}",
            n.default = "{subcls.default}",
            n.example_prompt = "{subcls.example_prompt}",
            n.prompt_embed = {subcls.prompt_embedding().tolist()}
        """
    # endregion

class Value(PromptedObj, metaclass=ValueMeta):
    '''
    Value is the base class of all input/ output params of an atom.
    Note that all Value subclasses should be static classes, with unique subclass name.
    '''

    expected_type: type = None
    '''Override this cls property to specify the expected type of the value.'''
    converter: Union[Converter, type] = None
    '''Override this cls property to specify the converter of the value.'''
    default: object = None
    '''Override this cls property to specify the default value of the value.'''
    example_prompt:str = None
    '''Override this cls property to specify the example prompt of the value. Example prompt is for teaching LM to know the format'''

    _value = None # store the real value of the param
    _prompt_embed : np.array = None # store the embedding of the prompt

    # region override
    @classmethod
    def kg_id(cls):
        '''override the original kg_id method to return the merged value node in some cases'''
        if cls._kg_id is None and cls.cls_name() not in ['Value',',PromptedObj']:
            node = neo4j_session().run(f'match (n:{cls.BASE_CLS_NAME}) where n.name="{cls.cls_name()}" return elementId(n)').single()
            if node is not None:
                cls._kg_id = node[0]
            else: # if it is included in a merged value node
                cls._kg_id = neo4j_session().run(f'match (n:MergedValue) where "{cls.cls_name()}" in n.from return elementId(n)').single()[0]
        return cls._kg_id
    # endregion

    # region private methods
    @classmethod
    def _converter(cls):
        '''the real converter'''
        if cls.converter is not None:
            if issubclass(cls.converter, Converter):
                return cls.converter
            elif isinstance(cls.converter, type):
                try:
                    return Converter[cls.converter]
                except KeyError:
                    return cls.converter
            else:
                return cls.expected_type
        else:
            try:
                return Converter[cls.expected_type]
            except KeyError:
                return cls.expected_type
    @classmethod
    def _convert(cls, value):
        '''try convert value to expected type or using given converter. If fail, return default value'''
        try:
            converter = cls._converter()
            if issubclass(converter, Converter):
                return converter.convert(value)
            else:
                return converter(value)
        except:
            return cls.default
    @classmethod
    def _converter_name(cls):
        '''try to return the converter's name. If no proper converter found, return "DIRECT_CONVERT"'''
        converter = cls._converter()
        if issubclass(converter, Converter):
            return converter.__qualname__
        else:
            return "DIRECT_CONVERT"
    @classmethod
    def _expected_type_name(cls):
        return cls.expected_type.__qualname__
    # endregion

    @classmethod
    def input(cls, value):
        if isinstance(value, cls.expected_type):  # no need to convert
            cls._value = value
        else:  # try to convert
            cls._value = cls._convert(value)
    @classmethod
    def value(cls):
        return cls._value if cls._value is not None else cls.default
    @classmethod
    def prompt_embed(cls, embeder:callable=None):
        if cls._prompt_embed is None:
            if embeder is not None:
                cls._prompt_embed = embeder(cls.prompt)
            else:
                cls._prompt_embed = get_embedding_vector(cls.prompt)
        return cls._prompt_embed
    @classmethod
    def full_prompt(cls):
        '''Return both prompt and example prompt(if exists)'''
        if cls.example_prompt is None:
            return cls.prompt
        else:
            return f'{cls.prompt} (e.g.:{cls.example_prompt})'