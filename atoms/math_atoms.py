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
    @classmethod
    def run(cls,formula: str):
        pass

'''CalculateFormula Value Output Class'''
class CalculationResult(Value):
    prompt = "calculation Result of a formula"
    @classmethod
    def run(cls,formula: float):
        pass

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
    prompt ="Shows calculation formula to be verified"
    example_prompt = 'formula: 1+1,result: 2'
    @classmethod
    def run(cls, formula: str,expected_result:float):
        pass

'''VerifyFormulaResult Value Output Class'''
class VerifyingAnswer(Value):
    prompt = "Shows whether the expected result is equal to the formula"
    @classmethod
    def run(cls,answer: bool):
        pass

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

'''Permutations Value Input Class / Permutations Value Output Class (thinking)'''
class PermutationsNumListStorage(Value):
    prompt = 'Shows a list of number'
    example_prompt = '[a, b, c]'
    @classmethod
    def run(cls, numlist:list):
        pass

class Permutations(Atom):
    inputs = (PermutationsNumListStorage,)
    outputs = (PermutationsNumListStorage,)
    prompt = 'Get all permutations with a list of elements. '
    @classmethod
    def run(cls, elements:list):
        from itertools import permutations
        return list(permutations(elements, len(elements)))

'''Sort Value Input Class'''
class SortOrder (Value):
    prompt = 'Shows order of sort'
    @classmethod
    def run(cls, order:bool, default=False):
        pass

'''Sort Value Input Class'''
class SortNumListStorage(Value):
    prompt = 'Shows a list of number for sorting'
    example_prompt = '[a, b, c]'
    @classmethod
    def run(cls, numlist:list):
        pass

'''Sort Value Output Class'''
class SortedNumListStorage(Value):
    prompt = 'Shows a sorted list of number'
    example_prompt = '[a, b, c]'
    @classmethod
    def run(cls, numlist:list):
        pass

class Sort(Atom):
    inputs = (SortNumListStorage,SortOrder,)
    outputs = (SortedNumListStorage,)
    prompt = 'Sort a list of numbers. e.g. [3,2,1] => [1,2,3]. You can also sort in descending order.'
    @classmethod
    def run(cls, elements:list, descending:bool=False):
        return sorted(elements, reverse=descending)

class EquationStorage(Value):
    prompt = 'Shows the equation to solve'
    example_prompt = 'x^2 + 2x + 1 = 0'
    @classmethod
    def run(cls, formula:str):
        pass

class SolveOneUnknownEquation(Atom):
    inputs = (EquationStorage,)
    outputs = (CalculationResult,)
    prompt = 'Solve a single unknown equation.'
    @classmethod
    def run(cls, formula: str):
        equation = sympy.parse_expr(formula, transformations=sympy.parsing.sympy_parser.T[:11])
        equation = sympy.sympify(equation)
        ans = sympy.solve(equation)
        return ans[0]

'''SolveLinearEquations Value Input Class'''
class SystemOfEquationsAnswer(Value):
    prompt = "Shows the system of the linear equation"
    example_prompt = '["8x + 3y− 2z = 9", "−4x+ 7y+ 5z = 15", "3x + 4y− 12z= 35"]'
    @classmethod
    def run(cls,formula: list):
        pass

'''SolveLinearEquations Value Output Class'''
class CalculationResultForLinearEquation(Value):
    prompt = "Shows the answer mapping from linear equation"
    example_prompt = '{"x": 1, "y": 2, "z": 3}'
    @classmethod
    def run(cls, answer: dict):
        pass

class SolveLinearEquations(Atom):
    inputs = SystemOfEquationsAnswer
    outputs = CalculationResultForLinearEquation
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