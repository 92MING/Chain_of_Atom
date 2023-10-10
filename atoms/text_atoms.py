'''Contains all atoms related to text processing'''
import re

from data_struct.atom import Atom
from data_struct.value import Value
from data_struct.converter import *
from utils.AI_utils import get_chat

'''TextToEquations Value Input Class'''
class TextDescribeEquations(Value):
    prompt = 'Text information of some mathematical equations'
    example_prompt = '6 apples and a orange cost 18 dollars, 4 apples and a orange cost 14 dollars'
    expected_type = str
    converter = StrConverter
    default = ''
    @classmethod
    def run(cls, text:str):
        pass

'''TextToEquations Value Output Class'''
class ListOfEquations(Value):
    prompt = "Lists of system of linear equation"
    example_prompt = "['6x+y=18', '4x+y=14']"
    expected_type = list
    converter = ListConverter
    default = []
    @classmethod
    def run(cls, formula:list):
        pass

class TextToEquations(Atom):
    inputs = (TextDescribeEquations,)
    outputs = (ListOfEquations,)
    prompt = "Convert the text to lists of equations"
    @classmethod
    def run(cls, text: str):
        prompt_ = f"""
        
        Now you are exposed to a real life problem on systems of linear equation.
        You are given text of some mathematical linear equation
        Try to convert the text problem into mathematical equation.
        
        e.g.
        ------------------
        Question:
        Solve the maths problem, the prices of apple times 6 plus the prices of the orange equal 18 dollars 
        and the prices of apple times 4 plus the prices of orange equal to 14 dollars, what are the prices of apple and orange?
        
        Answer:
        "6a+b=18, 4a+b=14"
        -----------------
        Under previous example, a and b are used to present the variable of prices of apple and orange respectively
        Now, you are given the following funcs and purpose:
        ------------------
        Question:
        {text}
        A: (your answer)
        ------------------
        Note that you just need to give out the sets of equations in above format, no explains are required.
        """
        ret = get_chat(prompt_).strip()
        ret = ret.replace('"', '')
        if ',' in ret:
            ret = re.split(r'\s*,\s*', ret)
        else:
            ret = [ret]
        return ret
