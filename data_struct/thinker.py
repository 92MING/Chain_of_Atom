'''
Thinker is the main class for the whole running. Create a new instance of Thinker to start the thinking process.
'''
import re

from utils.AI_utils import ChatModel, get_chat
from atoms import *
from data_struct.atom import *

class Thinker:

    def __init__(self, model:ChatModel=ChatModel.GPT3_5, temperature=0.5):
        self.model = model
        self.temperature = temperature

    # region private methods
    def _get_quoted_strs(self, s:str):
        '''get the strings quoted by []. Otherwise return None'''
        return re.findall(r'.*?\[(.*?)\].*?', s)

    def _init_think_prompt(self, question: str):
        return f"""
        Suppose you are solving a problem using 'Chain of Thoughts' method, and now you have come to the last step of the chain(It means after this step, you will get the answer).
        For this last step, what method should you use to solve it? Give a brief description of the method or the name of the method.
        Try to think of what should have been done before the last step & what you will get after the last step so as to help you think of the last step.
        Quote the last step with '[ ]'.

        e.g.
        ------------------
        Q: The sum of the price of a pen and a ball is 11. The price of the pen is 10 more than the price of the ball. What is the price of the ball?
        A: Last step : [Solving system of linear equations]. I should have listed out the equations before solving the last step. After finish the last step, I will get the value of the unknowns.
        ------------------
        Now, think about the question and answer the last step of the chain of thoughts. Note that you don't need to answer the question.
        Q: {question}
        """
    # endregion

    def think(self, question:str):
        print("start thinking Q:", question)
        ret = get_chat(self._init_think_prompt(question), model=self.model, temperature=self.temperature)
        last_step = self._get_quoted_strs(ret)[0]
        print("AI thinks the last step is:", last_step)

        self.think_for_possible_func(last_step)

    def think_for_possible_func(self, purpose:str)->Atom:
        print('thinking for a suitable atom...')
        possible_atoms = k_similar_atoms(purpose)
        print('possible atoms:', [atom.AtomName() for atom in possible_atoms])
        all_func_prompts = ""
        for j, atom in enumerate(possible_atoms):
            atom_input_prompts = '\n'.join([f'Input {i + 1}: {param.full_prompt}' for i, param in enumerate(atom.inputs)])
            atom_output_prompts = '\n'.join([f'Output {i + 1}: {param.full_prompt}' for i, param in enumerate(atom.outputs)])
            atom_prompt = atom.prompt
            all_func_prompts += f"""
                    Function {j + 1}:
                        Usage: {atom_prompt}
                        {atom_input_prompts}
                        {atom_output_prompts}
                    """
        prompt = f"""
        Now you are given some functions, which ONE do you think is able for reaching a given purpose's answer DIRECTLY?
        Consider more about the outputs of the functions whether could give you the answer directly.
        If none of them is possible, answer 'no', otherwise answer the function's index. Quote your answer & reason with two '[]'s. 
        
        example 1:
        ------------------
        Function 1:
            Usage: Solving system of linear equations
            Input 1: A system of linear equations (e.g. [x + y = 1, x - y = 2])
            Output 1: The solution of the linear equation set (e.g. {{x: 1, y: 0}})
        Function 2:
            Usage: Gives out an algebraic equation to represent your given text.
            Input 1: A text (e.g. 'A pen is 10 more expensive than a ball.')
            Input 2: A dictionary of variables (e.g. {{'x': 'pen', 'y': 'ball'}})
            Output 1: An algebraic equation (e.g. 'x = y + 10')
        Q: Purpose: Find a solution for {{"x-y=1", "x+y=2"}}
        A: [1]. [Because the output of function 1 is the solution of the linear equation set, which is the answer of the question.]
        ------------------
        
        example 2:
        ------------------
        Function 1:
            Usage: Solving system of linear equations
            Input 1: A system of linear equations (e.g. [x + y = 1, x - y = 2])
            Output 1: The solution of the linear equation set (e.g. {{x: 1, y: 0}})
        Function 2:
            Usage: Gives out an algebraic equation to represent your given text.
            Input 1: A text (e.g. 'A pen is 10 more expensive than a ball.')
            Input 2: A dictionary of variables (e.g. {{'pen': 'x', 'ball': 'y'}})
            Output 1: An algebraic equation (e.g. 'x = y + 10')
        Q: Purpose: A pen is 10 more expensive than a ball, and the sum of the price of a pen and a ball is 11. What is the price of the ball?
        A: [no]. [No function could be used directly.]
        ------------------
        
        Now, you are given the following funcs and purpose:
        ------------------
        {all_func_prompts}
        Purpose: {purpose}
        ------------------
        Note that you just need to give out the index of the function(s) and separate them with comma (if multiple).
        """
        ret = self._get_quoted_strs(get_chat(prompt, model=self.model, temperature=self.temperature).strip())
        if len(ret)>1:
            ans, reason = ret[:2]
        else:
            ans, reason = ret[0], 'No reason.'
        if 'no' in ans.lower():
            print("AI thinks no function could be used directly.")
            return None
        else:
            atom = possible_atoms[IntConverter.convert(ans) - 1]
            print(f"AI thinks the function is: {atom.AtomName()}. "
                  f"Because: {reason}")
            return atom



