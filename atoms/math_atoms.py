# -*- coding: utf-8 -*-
'''contains all the atoms related to math calculation'''
import sympy
from data_struct.atom import Atom
from data_struct.param import Param
from data_struct.converter import *

class CalculateFormula(Atom):
    inputs = (Param('Calculation formula', str, example_prompt='1+1'),)
    outputs = (Param('Calculation result', float),)
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

class VerifyFormulaResult(Atom):
    inputs = (Param('Calculation formula', str, example_prompt='1+1'), Param('Expected result', float))
    outputs = (Param('Whether the expected result is equal to the formula', bool),)
    prompt = 'Verify if a formula is valid with a given result'
    @classmethod
    def run(cls, formula:str, expected_result:float):
        try:
            value = eval(formula)
            return value == expected_result
        except:
            return False

class Permutations(Atom):
    inputs = (Param('List of elements for permutation', list, example_prompt='[a, b, c]'), )
    outputs = (Param('List of permutations with your given elements', list), )
    prompt = 'Get all permutations with a list of elements. '
    @classmethod
    def run(cls, elements:list):
        from itertools import permutations
        return list(permutations(elements, len(elements)))

class Sort(Atom):
    inputs = (Param('List of numbers for sorting', list, converter=NumListConverter, example_prompt='[3,2,1]'),
              Param('Whether to sort in descending order', bool, default=False))
    outputs = (Param('Sorted list of numbers', list), )
    prompt = 'Sort a list of numbers. e.g. [3,2,1] => [1,2,3]. You can also sort in descending order.'
    @classmethod
    def run(cls, elements:list, descending:bool=False):
        return sorted(elements, reverse=descending)

class SolveOneUnknownEquation(Atom):
    inputs = (Param('The equation to solve', str, example_prompt='x^2 + 2x + 1 = 0'), )
    outputs = (Param('Calculation result', float), )
    prompt = 'Solve a single unknown equation.'
    @classmethod
    def run(cls, formula: str):
        equation = sympy.parse_expr(formula, transformations=sympy.parsing.sympy_parser.T[:11])
        equation = sympy.sympify(equation)
        ans = sympy.solve(equation)
        return ans[0]

class SolveLinearEquations(Atom):
    inputs = (Param('The system of the linear equation', list, example_prompt='["8x + 3y− 2z = 9", "−4x+ 7y+ 5z = 15", "3x + 4y− 12z= 35"]'), )
    outputs = (Param('Calculation result', dict, example_prompt='{"x": 1, "y": 2, "z": 3}'), )
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
