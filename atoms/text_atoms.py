'''Contains all atoms related to text processing'''
import re

from data_struct.atom import Atom
from data_struct.value import Value
from data_struct.converter import *
from utils.AI_utils import get_chat

'''TextToEquations Value Input Class'''
class WordExpressionEquations(Value):
    prompt = 'Expression of math equations in word'
    example_prompt = '6 apples and a orange cost 18 dollars, 4 apples and a orange cost 14 dollars'
    expected_type = str
    converter = StrConverter
    default = ''


'''TextToEquations Value Output Class'''
class ListOfEquations(Value):
    prompt = "Lists of system of linear equation"
    example_prompt = "['6x+y=18', '4x+y=14']"
    expected_type = list
    converter = ListConverter
    default = []


class TextToEquations(Atom):
    inputs = (WordExpressionEquations,)
    outputs = (ListOfEquations,)
    prompt = "Convert the word expression of math equation to lists of equations"
    @classmethod
    def run(cls, text: str):
        prompt_ = f"""
        
        Now you are exposed to a real life problem on systems of linear equation.
        You are given word expression of some mathematical linear equation
        Try to convert the text problem into mathematical equation.
        Please quotes the answer with '[ ]'
        
        e.g.
        ------------------
        Question:
        the prices of apple times 6 plus the prices of the orange equal 18 dollars and the prices of apple times 4 plus the prices of orange equal to 14 dollars
        
        Answer: ['6a+b=18', '4a+b=14' ,'{{a:'apple', b:'orange'}}']
        Under this example, a and b are used to present the variable of prices of apple and orange respectively.
        Then starting to construct the system of linear equation for a and b by those equations suggested.
        -----------------
        
        e.g
        -----------------
        Question:
        The sum of the price of a pen and a ball is 11. The price of the pen is 10 more than the price of the ball. What is the price of the ball?
        
        Answer: ['p+b=11', 'p=10b' ,'{{p:'pen', b:'ball'}}']
        Under this example, p and b are used to present the variable of prices of pen and ball respectively.
        Then starting to construct the system of linear equation for p and b by those equations suggested.
        ----------------
        
        To make it sample, you can clearly see first letter of the object name are used to represent that object.
        Like 'p' for 'pen', 'a' for 'apple', 'o' for 'orange'.
        
        Now, you are given the following funcs and purpose:
        ------------------
        Question:
        {text}
        Answer: (your answer)
        ------------------
        Note that you just need to give out the sets of equations in above format, no explains are required.
        """
        ret = get_chat(prompt_)
        return re.findall(r'.*?\[(.*?)\].*?', ret)[0]

