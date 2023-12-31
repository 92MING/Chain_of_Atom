# -*- coding: utf-8 -*-
'''contains all the atoms related to math calculation'''
import sympy

from data_struct.atom import Atom
from data_struct.value import Value
from data_struct.converter import *
from utils.AI_utils import get_chat

'''CalculateFormula Value Input Class'''
class CalculationFormula(Value):
    prompt = "arithmetic question to be calculated"
    example_prompt = '1+1'
    expected_type = str
    converter = StrConverter
    default = 0

'''CalculateFormula Value Output Class'''
class CalculationResult(Value):
    prompt = "calculation Result of a arithmetic question"
    example_prompt = '0'
    expected_type = float
    converter = FloatConverter
    default = 0


class CalculateFormula(Atom):
    inputs = (CalculationFormula,)
    outputs = (CalculationResult,)
    prompt = 'Calculate a arithmetic question and get the result.'
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
    example_prompt = '[\'1+1=2\',\'1+1=3\']'
    expected_type = list
    converter = ListConverter
    default = ''


'''VerifyFormulaResult Value Output Class'''
class VerifyingAnswer(Value):
    prompt = "verified math formula equalling with a certain number"
    example_prompt = '[\'1+1=2\']'
    expected_type = list
    converter = ListConverter
    default = True


class VerifyFormulaResult(Atom):
    inputs = (CalculationFormulaVerify,)
    outputs = (VerifyingAnswer,)
    prompt = 'Verify if some formula is valid with their given result'
    @classmethod
    def run(cls, formulas: list):
            answer = []
            for formula in formulas:
                check = formula.split('=')
                lhs = check[0]
                rhs = check[1]
                if eval(lhs) == eval(rhs):
                    answer.append(formula)
            return answer

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
    example_prompt = '[\'8x + 3y− 2z = 9\', \'−4x+ 7y+ 5z = 15\', \'3x + 4y− 12z= 35\'] if no renaming of variable, [\'8x + 3y− 2z = 9\', \'−4x+ 7y+ 5z = 15\', \'3x + 4y− 12z= 35\', {x:apple, y:banana, z:orange}]'
    expected_type = list
    converter = ListConverter
    default = []


'''SolveLinearEquations Value Output Class'''
class CalculationResultForLinearEquation(Value):
    prompt = "the solution of the system of linear equation"
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
        print(system)
        appendix = None
        if isinstance(system[-1], dict):
            appendix = system[-1]
            system = system[:-1]
        for key, value in _replace.items():
            system = [equation.replace(key, value) for equation in system]
        system = [sympy.parse_expr(equation, transformations=sympy.parsing.sympy_parser.T[:11]) for equation in system]
        system = [sympy.sympify(equation) for equation in system]
        ans = sympy.solve(system)
        for old_key, new_key in dict(ans).items():
            ans[str(old_key)] = int(ans.pop(old_key))
        if appendix is not None:
            for old_key, new_key in appendix.items():
                ans[new_key] = ans.pop(old_key)
        return ans
