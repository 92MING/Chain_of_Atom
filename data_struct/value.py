from data_struct.converter import Converter
from data_struct.promptedObj import *
import numpy as np
from utils.AI_utils import get_embedding_vector
from typing import Callable, Union
from utils.neo4j_utils import neo4j_session

class ValueMeta(PromptedObjMeta):
    BASE_CLS_NAME = 'Value'
    ADD_TO_KG = True

    # override
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
    def create_subcls_node_in_kg(cls, subcls: Union['Value', type]):
        return f"""
        CREATE (n:{cls.BASE_CLS_NAME} {{name: "{subcls.cls_name()}", prompt: "{subcls.prompt}",
                expected_type: "{subcls.expected_type}", converter: "{subcls.converter}", default: "{subcls.default}",
                example_prompt: "{subcls.example_prompt}", prompt_embed: "{subcls.prompt_embedding().tolist()}"}})
        """
    @classmethod
    def update_subcls_node_in_kg(cls, subcls: Union['Value', type]):
        raise NotImplementedError()

class Value(metaclass=ValueMeta, PromptedObj):
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

    @classmethod
    def input(cls, value):
        if isinstance(value, cls.expected_type): # no need to convert
            cls._value = value
        else: # try to convert
            try:
                if cls.converter is not None:
                    if isinstance(cls.converter, Converter):
                        cls._value = cls.converter.convert(value)
                    elif isinstance(cls.converter, Callable):
                        cls._value = cls.converter(value)
                    elif isinstance(cls.converter, type):
                        cls._value = cls.converter(value)
                    else:
                        raise Exception(f'Cannot convert {value} to {self.expected_type} with converter: {self.converter}.')
                else:
                    try:
                        converter = Converter[self.expected_type]
                        self._value = converter.convert(value)
                    except KeyError:
                        self._value = self.expected_type(value)
            except:
                self._value = self.default

    @property
    def value(self):
        return self._value if self._value is not None else self.default

    @property
    def prompt_embed(self, embeder:callable=None):
        if self._prompt_embed is None:
            if embeder is not None:
                self._prompt_embed = embeder(self.prompt)
            else:
                self._prompt_embed = get_embedding_vector(self.prompt)
        return self._prompt_embed

    @property
    def full_prompt(self):
        '''Return both prompt and example prompt(if exists)'''
        if self.example_prompt is None:
            return self.prompt
        else:
            return f'{self.prompt} (e.g.:{self.example_prompt})'