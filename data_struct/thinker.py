'''
Thinker is the main class for the whole running. Create a new instance of Thinker to start the thinking process.
'''
import re

from utils.AI_utils import ChatModel, get_chat, get_embedding_vector
from atoms import *
from data_struct.atom import *

INIT_THINK_PROMPT = """
    Suppose you are solving a problem using 'Chain of Thoughts' method, and now you have come to the last step of the chain. 
    For this last step, what method should you use to solve it? Give a brief description of the method or the name of the method.
    Try to think of what should have been done before the last step to make sure the last step is really the last step.
    Quote the last step with '[ ]'.
    
    e.g.
    ------------------
    Q: The sum of the price of a pen and a ball is 11. The price of the pen is 10 more than the price of the ball. What is the price of the ball?
    A: Last step : [Solving algebraic equations]. I should have listed out the equations before solving the last step.
    ------------------
"""

STEP_BEFORE_PROMPT = """
    Suppose you are solving a problem using 'Chain of Thoughts' method, and now you have think reversely.
    You currently know the problem overflew and last few steps, you have to try to think on one previous step on top of those prvoided steps.
    Try to think to ensure the this previous step could combine with the later on steps.
    Quote the previous step with '[]'
    
    e.g.
    ------------------
    Q:
    Problem_overview: The sum of the price of a pen and a ball is 11. The price of the pen is 10 more than the price of the ball. What is the price of the ball?
    Final_step: Solving algebraic equations
    A: 
    Previous_step: [Building up lists of equations for solving from the text]. I should have read through the text to set a system of linear equation with varaiable.
    ------------------
"""

def _get_init_think_prompt(question:str):
    return f"""
    {INIT_THINK_PROMPT}
    Now, think about the question and answer the last step of the chain of thoughts. Note that you don't need to answer the question.
    Q: {question}
    """

def _get_step_before_prompt(question: str):
    return f"""
    {STEP_BEFORE_PROMPT}
    Now think about the question and answer the previous step of the chain of thoughts. Note that you don't need to answer the question.
    """

class Thinker:

    def __init__(self, model:ChatModel=ChatModel.GPT3_5, temperature=0.5):
        self.model = model
        self.temperature = temperature

    def think(self, question:str):
        print("start thinking Q:", question)
        current = f'Problem_overview: {question}'
        ret = get_chat(_get_init_think_prompt(question), model=self.model, temperature=self.temperature)
        last_step = re.match(r'.*\[(.*)\].*', ret).group(1)
        print("AI thinks the last step is:", last_step)
        current += f'Final_step: {last_step}'
        self.ask_for_possible_funcs(last_step)

        ret = get_chat(_get_step_before_prompt(question), model=self.model, temperature=self.temperature)
        previous_step = re.match(r'.*\[(.*)\].*', ret).group(1)
        print("AI thinks the previous step is:", previous_step)
        self.ask_for_possible_funcs(previous_step)

    def ask_for_possible_funcs(self, purpose:str):
        possible_atoms = k_similar_atoms(purpose)
        all_func_prompts = ""
        for j, atom in enumerate(possible_atoms):
            atom_input_prompts = '\n'.join([f'Input {i + 1}: {param.prompt}' for i, param in enumerate(atom.inputs)])
            atom_output_prompts = '\n'.join([f'Output {i + 1}: {param.prompt}' for i, param in enumerate(atom.outputs)])
            atom_prompt = atom.prompt
            all_func_prompts += f"""
                    Function {j + 1}:
                        Usage: {atom_prompt}
                        {atom_input_prompts}
                        {atom_output_prompts}
                    """
        prompt = f"""
        Now you are given some functions, which one/which of them do you think is/are the most possible functions for reaching a given purpose?
        Answer the index of the function(s) and separate them with comma (if multiple).
        
        e.g.
        ------------------
        Function 1:
            Usage: Solving algebraic equations
            Input 1: A set of algebraic equations
            Output 1: The solution of the equation set
        Function 2:
            Usage: Gives out an algebraic equation to represent a given text
            Input 1: A text
            Input 2: A dictionary of variables, e.g. {{'x': 'apple', 'y': 'banana'}}
            Output 1: An algebraic equation
        
        Q: Purpose: Find a solution of the equation set
        A: 1
        ------------------
        
        Now, you are given the following funcs and purpose:
        ------------------
        {all_func_prompts}
        Purpose: {purpose}
        A: (your answer)
        ------------------
        Note that you just need to give out the index of the function(s) and separate them with comma (if multiple).
        """
        ret = get_chat(prompt, model=self.model, temperature=self.temperature).strip()
        if ':' in ret:
            ret = re.split(r'\s*:\s*', ret)[1].strip()
        if ',' in ret:
            ret = re.split(r'\s*,\s*', ret)
        else:
            ret = [ret]
        ret = [int(i) - 1 for i in ret]
        print("AI thinks the possible functions are:", [possible_atoms[i].prompt for i in ret])

    def run_for_possible_function(self, purpose: Atom):

        pass

    def back_track(self):
        pass



