import numpy as np
from .param import Param
from typing import Tuple
from utils.AI_utils import get_embedding_vector
from utils.global_value_utils import GetOrAddGlobalValue
from utils.path_utils import ATOM_DATA_PATH
from utils.sqlite_utils import Database, NotFoundError

# region database
_ATOM_DATA_DB = Database(ATOM_DATA_PATH)
_PREDEFINED_ATOM_CLSES_TABLE = _ATOM_DATA_DB.create_table(name='predefined_atom_clses',
                                                         columns={'id':int, 'cls_name':str, 'prompt':str,},
                                                         pk='id',
                                                         autoincrement='id',
                                                         if_not_exists=True)
'''All predefined atom classes(predefined atom means atoms written in .py). Mainly use for saving their id.'''
_PREDEFINED_ATOM_CLSES_TABLE.create_index(columns='cls_name', if_not_exists=True)

# endregion

# region atom base class
_ATOM_CLSES = GetOrAddGlobalValue('_ATOM_CLSES', dict()) # cls name : atom cls
class AtomMeta(type):
    '''AtomMeta is a metaclass for Atom. It will save all atom prompts for searching process.'''
    def __new__(self, *args, **kwargs):
        cls_name = args[0]
        if cls_name != 'Atom' and cls_name not in _ATOM_CLSES:
            cls = super().__new__(self, *args, **kwargs)
            if cls.prompt is None:
                raise Exception(f'Atom {cls_name} should have a prompt.')
            _ATOM_CLSES[cls_name] = cls
            if _PREDEFINED_ATOM_CLSES_TABLE.find_first(f'cls_name="{cls_name}"') is None:
                _PREDEFINED_ATOM_CLSES_TABLE.insert({'cls_name':cls_name, 'prompt':cls.prompt})
                cls._id = _PREDEFINED_ATOM_CLSES_TABLE.find_first(f'cls_name="{cls_name}"')['id']
            else:
                cls._id = _PREDEFINED_ATOM_CLSES_TABLE.find_first(f'cls_name="{cls_name}"')['id']
                _PREDEFINED_ATOM_CLSES_TABLE.update({'id':cls._id, 'cls_name':cls_name, 'prompt':cls.prompt})
            return cls
        if cls_name == 'Atom':
            return super().__new__(self, *args, **kwargs)
        else:
            return _ATOM_CLSES[cls_name]
class Atom(metaclass=AtomMeta):
    '''
    Atom is 1 single action with clear param/ result description. It is a basic unit of a step.
    Override this class to define your own atom.
    Note that all atoms should be static classes, with unique class name.
    '''

    inputs:Tuple[Param, ...] = None
    '''Override this cls property to specify the input params of the atom.'''
    outputs:Tuple[Param, ...] = None
    '''Override this cls property to specify the output params of the atom.'''
    prompt:str = None
    '''Override this to describe the atom function.'''

    _prompt_embed : np.array = None
    _id :int = None # the unique id of this atom in sql table

    def __init__(self):
        raise Exception("Atom is a static class, don't initialize it. You should herit to define your own atom with input/ output params and run method.")
    @classmethod
    def AtomName(cls):
        return cls.__qualname__
    @classmethod
    def id(cls):
        '''Get the unique id of this atom.'''
        return cls._id
    @classmethod
    def inputVals(cls):
        '''Get the inputted values of this atom. Note that "call" method should be called in advance.'''
        return tuple(param.value for param in cls.inputs)
    @classmethod
    def input_prompt_embeds(cls):
        '''Get the prompt embed of each param this atom. '''
        return tuple(param.prompt_embed for param in cls.inputs)
    @classmethod
    def outputVals(cls):
        '''Get the outputted values of this atom. Note that "call" method should be called in advance.'''
        return tuple(param.value for param in cls.outputs)
    @classmethod
    def output_prompt_embeds(cls):
        '''Get the prompt embed of each param this atom. '''
        return tuple(param.prompt_embed for param in cls.outputs)
    @classmethod
    def prompt_embed(self, embeder:callable=None):
        '''Get the prompt embed of this atom. '''
        if self._prompt_embed is None:
            if embeder is not None:
                self._prompt_embed = embeder(self.prompt)
            else:
                self._prompt_embed = get_embedding_vector(self.prompt)
        return self._prompt_embed

    @classmethod
    def call(cls, *values):
        '''
        Call this atoms' function.
        Inputted values will be stored in each input param. You could access by self.inputVals.
        Outputted values will be stored in each output param. You could access by self.outputVals.
        '''

        # input values
        for i, value in enumerate(values):
            cls.inputs[i].input(value)

        # run the atom
        result = cls.run(*cls.inputVals())

        # save the result into output params
        if len(cls.outputs) > 1:
            for i, value in enumerate(result):
                cls.outputs[i].input(value)
        else:
            cls.outputs[0].input(result)
        return cls

    @classmethod
    def run(self, *inputs):
        '''Run the atom. Override this method to implement the atom's function.'''
        raise NotImplementedError
# endregion

# region static methods
def all_atom_clses():
    '''Get all atom classes.'''
    return _ATOM_CLSES.values()
def all_atom_prompts()->Tuple[str, ...]:
    '''Get all atom prompts.'''
    return tuple(atom.prompt for atom in all_atom_clses())
def all_atom_inputs()->Tuple[Tuple[Param, ...], ...]:
    '''Get all atom input params.'''
    return tuple(atom.inputs for atom in all_atom_clses())
def all_atom_outputs()->Tuple[Tuple[Param, ...], ...]:
    '''Get all atom output params.'''
    return tuple(atom.outputs for atom in all_atom_clses())

def k_similar_atoms(prompt:str, k=5):
    '''Get k similar atoms with the input prompt.'''
    # TODO: use fine-tuned BERT to get embedding vectors
    # TODO: use KNN to get k similar atoms
    prompt_embed = get_embedding_vector(prompt)
    return sorted(_ATOM_CLSES.values(), key=lambda atom: np.dot(atom.prompt_embed(), prompt_embed))[:k]

# endregion