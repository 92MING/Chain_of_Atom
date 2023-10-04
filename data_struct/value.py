from data_struct.converter import Converter
from data_struct.promptedObj import *
import numpy as np
from utils.AI_utils import get_embedding_vector
from typing import Callable, Union
from utils.neo4j_utils import neo4j_session

class ValueMeta(PromptedObjMeta):
    BASE_CLS_NAME = 'Value'
    ADD_TO_KG = True

    @classmethod
    def create_subcls_node_in_kg(cls, subcls: 'Value'):
        cypher = f"""CREATE (n:{cls.BASE_CLS_NAME} {{name: "{subcls.cls_name()}", prompt: "{subcls.prompt}"}})"""

    @classmethod
    def update_subcls_node_in_kg(cls, subcls: type):
        raise NotImplementedError()

class Value(metaclass=ValueMeta):
    self.prompt = prompt
    self.expected_type = expected_type
    self.converter = converter
        self.default = default
        self.example_prompt = example_prompt
        self._value = None # store the value of the param
        self._prompt_embed : np.array = None # store the embedding of the prompt

    def input(self, value):
        if isinstance(value, self.expected_type): # no need to convert
            self._value = value
        else: # try to convert
            try:
                if self.converter is not None:
                    if isinstance(self.converter, Converter):
                        self._value = self.converter.convert(value)
                    elif isinstance(self.converter, Callable):
                        self._value = self.converter(value)
                    elif isinstance(self.converter, type):
                        self._value = self.converter(value)
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