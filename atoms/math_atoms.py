'''contains all the atoms related to math calculation'''

from data_struct.atom import Atom
from data_struct.param import Param

class CalculateFormula(Atom):
    inputs = (Param('Calculation formula', str),)
    outputs = (Param('Calculation result', float),)
    prompt = 'Calculate a formula, e.g. 1+2*3, and get the result.'
    @classmethod
    def run(cls, formula:str):
        result = eval(formula)
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
    inputs = (Param('List of elements', list), )
    outputs = (Param('List of permutations', list),)
    prompt = 'Get all permutations with a list of elements. e.g. [1,2,3] => [(1,2,3), (1,3,2), (2,1,3), ...]'
    @classmethod
    def run(cls, elements:list):
        from itertools import permutations
        return list(permutations(elements, len(elements)))
