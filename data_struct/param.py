from .converter import Converter
import numpy as np
from utils.AI_utils import get_embedding_vector
from typing import Callable

class Param:
    '''Param is a class that stores info for input/output of an atom.'''
    def __init__(self, prompt, expected_type:type, converter=None, default=None):
        '''
        :param prompt: The prompt for searching.
        :param expected_type: The expected type of the input/output.
        :param converter: The converter for converting the input/output. If not specified, will try to convert the input/output to the expected type.
        :param default: default value for the input/output when type conversion failed.
        '''
        self.prompt = prompt
        self.expected_type = expected_type
        self.converter = converter
        self.default = default
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