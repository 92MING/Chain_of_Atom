import numpy as np
from promptedObj import PromptedObjMeta, PromptedObj
from value import Value
from typing import Tuple, Union
from utils.AI_utils import get_embedding_vector
from utils.global_value_utils import GetOrAddGlobalValue
from utils.neo4j_utils import neo4j_session

class AtomMeta(PromptedObjMeta):
    '''AtomMeta is a baseclass for Atom. It is for doing some initialization work when a Atom subclass is defined.'''
    BASE_CLS_NAME = 'Atom'
    ADD_TO_KG = True
    INIT_PRIORITY = 1 # atom should be initialized after all values are initialized

    @classmethod
    def create_subcls_cyphers(cls, subcls):
        # TODO: update atom prompt
        ...
    @classmethod
    def update_subcls_cyphers(cls, subcls) ->Union[list, str]:
        # TODO: update atom prompt
        ...

class Atom(metaclass=AtomMeta, PromptedObj):
    '''
    Atom is 1 single action with clear param/ result description. It is a basic unit of a step.
    Override this class to define your own atom.
    Note that all atoms should be static classes, with unique class name.
    '''

    inputs:Tuple[Value,...] = None
    '''Override this cls property to specify the input params of the atom.'''
    outputs:Tuple[Value,...] = None
    '''Override this cls property to specify the output params of the atom.'''

    def __init__(self):
        raise Exception("Atom is a static class, don't initialize it. You should herit to define your own atom with input/ output params and run method.")
    @classmethod
    def inputVals(cls):
        '''Get the inputted values of this atom. Note that "call" method should be called in advance.'''
        return tuple(val.value() for val in cls.inputs)
    @classmethod
    def input_prompt_embeds(cls):
        '''Get the prompt embed of each param this atom. '''
        return tuple(val.prompt_embed() for val in cls.inputs)
    @classmethod
    def outputVals(cls):
        '''Get the outputted values of this atom. Note that "call" method should be called in advance.'''
        return tuple(val.value() for val in cls.outputs)
    @classmethod
    def output_prompt_embeds(cls):
        '''Get the prompt embed of each param this atom. '''
        return tuple(val.prompt_embed() for val in cls.outputs)

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
def all_atom_prompts()->Tuple[str, ...]:
    '''Get all atom prompts.'''
    return tuple(atom.prompt for atom in Atom.all_subclses())
def all_atom_inputs()->Tuple[Tuple[Value, ...], ...]:
    '''Get all atom input params.'''
    return tuple(atom.inputs for atom in Atom.all_subclses())
def all_atom_outputs()->Tuple[Tuple[Value, ...], ...]:
    '''Get all atom output params.'''
    return tuple(atom.outputs for atom in Atom.all_subclses())

def k_similar_atoms(prompt:str, k=5):
    '''Get k similar atoms with the input prompt.'''
    # TODO: use fine-tuned BERT to get embedding vectors
    # TODO: use KNN to get k similar atoms
    prompt_embed = get_embedding_vector(prompt)
    # print(sorted(_ATOM_CLSES.values(), key=lambda atom: np.dot(atom.prompt_embed(), prompt_embed)))
    return sorted(Atom.all_subclses(), key=lambda atom: np.arccos(np.dot(atom.prompt_embed(), prompt_embed)))[:k]
