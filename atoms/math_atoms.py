'''contains all the atoms related to math calculation'''
import sympy
import numpy as np
from data_struct.atom import Atom
from data_struct.param import Param
from data_struct.converter import *

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

class EquationWithOneUnknown(Atom):
    inputs = (Param('The equation', str), )
    outputs = (Param('Calculation result', list), )
    prompt = 'Solve a single unknown equation. e.g. x^2+2x+1=0 or x+3=0'
    @classmethod
    def run(cls, formula: str):
        equation = sympy.sympify("Eq(" + formula.replace("=", ",") + ")")
        ans = sympy.solve(equation)
        return ans

class SolveLinearEquations(Atom):
    inputs = (Param('The system of the linear equation', list), )
    outputs = (Param('Calculation result', list), )
    prompt = '''
    Solve the system of linear equation. 
    e.g. for three equations with three unknowns 
                ["8x + 3y− 2z = 9", 
                "−4x+ 7y+ 5z = 15", 
                "3x + 4y− 12z= 35"]
    '''

    @classmethod
    def run(cls,system: list):
        left_matrix = []
        right_matrix = []
        for line in system:
            left, right = line.split('=')
            left = re.findall(r'[\d\.\-\+]+', left)
            left = [int(x) for x in left]
            left_matrix.append(left)
            right_matrix.append(int(right))
        left_matrix = np.array(left_matrix)
        right_matrix = np.array(right_matrix)
        ans = np.linalg.solve(left_matrix, right_matrix)
        return ans

print(SolveLinearEquations.run(["8x + 3y− 2z = 9", "−4x+ 7y+ 5z = 15", "3x + 4y− 12z= 35"]))