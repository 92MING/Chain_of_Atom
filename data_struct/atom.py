from .param import Param
from typing import Tuple, Iterable

from utils.global_value_utils import GetOrAddGlobalValue

# region atom base class
_ATOM_CLSES = GetOrAddGlobalValue('_ATOM_CLSES', dict()) # cls name : atom cls
def AtomMeta(type):
    '''AtomMeta is a metaclass for Atom. It will save all atom prompts for searching process.'''
    def __new__(self, *args, **kwargs):
        cls_name = args[0]
        if cls_name != 'Atom' and cls_name not in _ATOM_CLSES:
            cls = super().__new__(self, *args, **kwargs)
            _ATOM_CLSES[cls_name] = cls
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

    def __init__(self):
        raise Exception("Atom is a static class, don't initialize it. You should herit to define your own atom with input/ output params and run method.")

    @classmethod
    def inputVals(cls):
        '''Get the inputted values of this atom. Note that "call" method should be called in advance.'''
        return tuple(param.value for param in cls.inputs)
    @classmethod
    def outputVals(cls):
        '''Get the outputted values of this atom. Note that "call" method should be called in advance.'''
        return tuple(param.value for param in cls.outputs)

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
        if isinstance(result, Iterable) and not isinstance(result, str):
            for i, value in enumerate(result):
                cls.outputs[i].input(value)
        else:
            cls.outputs[0].input(result)

    @classmethod
    def run(self, *inputs):
        '''Run the atom. Override this method to implement the atom's function.'''
        raise NotImplementedError
# endregion

# region static methods
def AllAtomClses():
    '''Get all atom classes.'''
    return _ATOM_CLSES.values()
def AllAtomInputs()->Tuple[Tuple[Param, ...], ...]:
    '''Get all atom input params.'''
    return tuple(atom.inputs for atom in AllAtomClses())
def AllAtomOutputs()->Tuple[Tuple[Param, ...], ...]:
    '''Get all atom output params.'''
    return tuple(atom.outputs for atom in AllAtomClses())
# endregion