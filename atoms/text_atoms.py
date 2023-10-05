'''Contains all atoms related to text processing'''
import re

from data_struct.atom import Atom
from data_struct.value import Value
from data_struct.converter import *
from utils.AI_utils import get_chat

'''TextToEquations Value Input Class'''
class TextDescribeEquations(Value):
    prompt = "Shows a short passage describing the problems of sets of equation in real life"

    @classmethod
    def run(cls, text:str):
        pass

'''TextToEquations Value Output Class'''
class ListOfEquations(Value):
    prompt = "Stores Lists of equations to solve the problems"
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
        
        Now you are given a short passage about real life application on systems of linear equation.
        Try to convert the text problem into mathematical equation.
        
        e.g.
        ------------------
        Question:
        Solve the maths problem, the prices of apple times 6 plus the prices of the orange equal 18 dollars 
        and the prices of apple times 4 plus the prices of orange equal to 14 dollars
        
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
