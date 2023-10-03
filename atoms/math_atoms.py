'''contains all the atoms related to math calculation'''
from data_struct.atom import Atom
from data_struct.param import Param
from data_struct.converter import *
import sympy

class CalculateFormula(Atom):
    inputs = (Param('Calculation formula', str),)
    outputs = (Param('Calculation result', float),)
    prompt = 'Calculate a formula, e.g. 1+2*3, and get the result.'
    @classmethod
    def run(cls, formula:str):
        _replace_dict = {
            'pi': 'sympy.pi',
            'π': 'sympy.pi',
            'e': 'sympy.E',
            '^': '**',
            'inf': 'sympy.oo',
            '∞': 'sympy.oo',
            '√': 'sympy.sqrt',
            'sqrt': 'sympy.sqrt',
            'sin': 'sympy.sin',
            'cos': 'sympy.cos',
            'tan': 'sympy.tan',
        }
        for key, value in _replace_dict.items():
            formula = formula.replace(key, value)
        result = eval(formula)
        if isinstance(result, sympy.Expr):
            return result.evalf()
        return result

class VerifyFormulaResult(Atom):
    inputs = (Param('Calculation formula', str), Param('expected result', float))
    outputs = (Param('Whether the expected result is equal to the formula', bool),)
    prompt = 'Verify if a formula is valid, e.g. 1+2*3.'
    @classmethod
    def run(cls, formula:str, expected_result:float):
        try:
            value = eval(formula)
            return value == expected_result
        except:
            return False

class Permutations(Atom):
    inputs = (Param('List of elements for permutation', list), )
    outputs = (Param('List of permutations with your given elements', list), )
    prompt = 'Get all permutations with a list of elements. e.g. [1,2,3] => [(1,2,3), (1,3,2), (2,1,3), ...]'
    @classmethod
    def run(cls, elements:list):
        from itertools import permutations
        return list(permutations(elements, len(elements)))

class Sort(Atom):
    inputs = (Param('List of numbers for sorting', list, converter=NumListConverter), Param('Whether to sort in descending order', bool, default=False))
    outputs = (Param('Sorted list of numbers', list), )
    prompt = 'Sort a list of numbers. e.g. [3,2,1] => [1,2,3]. You can also sort in descending order.'
    @classmethod
    def run(cls, elements:list, descending:bool=False):
        return sorted(elements, reverse=descending)


