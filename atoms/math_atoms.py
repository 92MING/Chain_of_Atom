# -*- coding: utf-8 -*-
'''contains all the atoms related to math calculation'''
import sympy

from data_struct.atom import Atom
from data_struct.value import Value
from data_struct.converter import *
from utils.AI_utils import get_chat

'''CalculateFormula Value Input Class'''
class CalculationFormula(Value):
    prompt = "mathematics formula to be calculated"
    example_prompt = '1+1'
    expected_type = str
    converter = StrConverter
    default = 0

'''CalculateFormula Value Output Class'''
class CalculationResult(Value):
    prompt = "calculation Result of a formula"
    example_prompt = '0'
    expected_type = float
    converter = FloatConverter
    default = 0


class CalculateFormula(Atom):
    inputs = (CalculationFormula,)
    outputs = (CalculationResult,)
    prompt = 'Calculate a math formula and get the result.'
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

'''VerifyFormulaResult Value Input Class'''
class CalculationFormulaVerify(Value):
    prompt ="calculation formula to be verified"
    example_prompt = '1+1=2'
    expected_type = str
    converter = StrConverter
    default = ''


'''VerifyFormulaResult Value Output Class'''
class VerifyingAnswer(Value):
    prompt = "correctness of the expected result equaling to the formula"
    example_prompt = 'True'
    expected_type = bool
    converter = BoolConverter
    default = True


class VerifyFormulaResult(Atom):
    inputs = (CalculationFormulaVerify,)
    outputs = (VerifyingAnswer,)
    prompt = 'Verify if a formula is valid with a given result'
    @classmethod
    def run(cls, formula:str, expected_result:float):
        try:
            value = eval(formula)
            return value == expected_result
        except:
            return False

'''Permutations Value Input Class'''
class PermutationsNumListStorage(Value):
    prompt = 'a list of number that will undergo Permutations'
    example_prompt = '[1, 2, 3]'
    expected_type = list
    converter = NumListConverter
    default = []


'''Permutations Value Output Class'''
class PermutationsResultStorage(Value):
    prompt = 'a list of number after undergoing Permutations'
    example_prompt = '[[a, b, c], [a, c, b], [b, a, c], [b, c, a], [c, a, b], [c, b, a]]'
    expected_type = list
    converter = NumListConverter
    default = []


class Permutations(Atom):
    inputs = (PermutationsNumListStorage,)
    outputs = (PermutationsResultStorage,)
    prompt = 'Get all permutations with a list of elements. '
    @classmethod
    def run(cls, elements:list):
        from itertools import permutations
        return list(permutations(elements, len(elements)))

'''Sort Value Input Class'''
class SortOrder (Value):
    prompt = 'order of sorting'
    example_prompt = "1(ascending)"
    expected_type = bool
    converter = BoolConverter
    default = 0


'''Sort Value Input Class'''
class SortNumListStorage(Value):
    prompt = 'a list of number for sorting'
    example_prompt = '[a, b, c]'
    expected_type = list
    converter = NumListConverter
    default = []


'''Sort Value Output Class'''
class SortedNumListStorage(Value):
    prompt = 'a sorted list of number'
    example_prompt = '[a, b, c]'
    expected_type = list
    converter = NumListConverter
    default = []


class Sort(Atom):
    inputs = (SortNumListStorage,SortOrder,)
    outputs = (SortedNumListStorage,)
    prompt = 'Sort a list of numbers. e.g. [3,2,1] => [1,2,3]. You can also sort in descending order.'
    @classmethod
    def run(cls, elements:list, descending:bool=False):
        return sorted(elements, reverse=descending)

'''SolveOneUnknownEquation Value Input Class'''
class EquationStorage(Value):
    prompt = 'the equation to solve'
    example_prompt = 'x^2 + 2x + 1 = 0'
    expected_type = str
    converter = StrConverter
    default = ''

'''SolveOneUnknownEquation Value Output Class'''
class EquationSolution(Value):
    prompt = 'the solution of a single unknown equation'
    example_prompt = '[-1,1]'
    expected_type = list
    converter = NumListConverter
    default = []

class SolveOneUnknownEquation(Atom):
    inputs = (EquationStorage,)
    outputs = (EquationSolution,)
    prompt = 'Solve a single unknown equation.'
    @classmethod
    def run(cls, formula: str):
        equation = sympy.parse_expr(formula, transformations=sympy.parsing.sympy_parser.T[:11])
        equation = sympy.sympify(equation)
        ans = sympy.solve(equation)
        return ans

'''SolveLinearEquations Value Input Class'''
class SystemOfEquationsStoraget(Value):
    prompt = "the system of the linear equation in mathematical format"
    example_prompt = '[\'8x + 3y− 2z = 9\', \'−4x+ 7y+ 5z = 15\', \'3x + 4y− 12z= 35\']'
    expected_type = list
    converter = ListConverter
    default = []


'''SolveLinearEquations Value Output Class'''
class CalculationResultForLinearEquation(Value):
    prompt = "the solution of system of linear equation"
    example_prompt = '{\'x\': 1, \'y\': 2, \'z\': 3}'
    expected_type = dict
    converter = DictConverter
    default = {}


class SolveLinearEquations(Atom):
    inputs = (SystemOfEquationsStoraget,)
    outputs = (CalculationResultForLinearEquation,)
    prompt = '''Solve a system of linear equation.'''
    @classmethod
    def run(cls, system: list):
        # To prevent some chr problems when parsing the equation
        _replace = {
            chr(0x2212): '-',
        }
        for key, value in _replace.items():
            system = [equation.replace(key, value) for equation in system]
        system = [sympy.parse_expr(equation, transformations=sympy.parsing.sympy_parser.T[:11]) for equation in system]
        system = [sympy.sympify(equation) for equation in system]
        ans = sympy.solve(system)
        return ans
