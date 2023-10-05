'''
Thinker is the main class for the whole running. Create a new instance of Thinker to start the thinking process.
'''
import re

from utils.AI_utils import ChatModel, get_chat, get_embedding_vector
from atoms import *
from data_struct.atom import *
from data_struct.value import *
from data_struct.converter import IntListConverter
from utils.neo4j_utils import neo4j_session

class Thinker:

    def __init__(self, model:ChatModel=ChatModel.GPT3_5, temperature=0.5):
        self.model = model
        self.temperature = temperature

    # region private methods
    def _get_quoted_strs(self, s:str):
        '''get the strings quoted by []. Otherwise return None'''
        return re.findall(r'.*?\[(.*?)\].*?', s)

    def _init_think_prompt(self, question: str):
        # return f"""
        # Suppose you are solving a problem using 'Chain of Thoughts' method, and now you have come to the last step of the chain(It means after this step, you will get the answer).
        # For this last step, what method should you use to solve it? Give a brief description of the method or the name of the method.
        # Try to think of what should have been done before the last step & what you will get after the last step so as to help you think of the last step.
        # Quote the last step with '[ ]'.
        #
        # e.g.
        # ------------------
        # Q: The sum of the price of a pen and a ball is 11. The price of the pen is 10 more than the price of the ball. What is the price of the ball?
        # A: Last step : [Solving system of linear equations]. I should have listed out the equations before solving the last step. After finish the last step, I will get the value of the unknowns.
        # ------------------
        # Now, think about the question and answer the last step of the chain of thoughts. Note that you don't need to answer the question.
        # Q: {question}
        # """

        return f"""
        Suppose you are solving a problem using 'Chain of Thoughts' method, and you are now thinking the final outputs of the problem,
        which means that you are now reaching the solution of the problem.
        No calculation are required in this task. You are required to identify what type of answers needed to be the outputs of this problem.
        Quote the last step with '[ ]'.

        e.g.
        ------------------
        Q: The sum of the price of a pen and a ball is 11. The price of the pen is 10 more than the price of the ball. What is the price of the ball?
        A: Last step : [Solution of system of linear equations]. I should have listed out the equations before solving the last step. After finish the last step, I will get the value of the unknowns. And the solution would be the output.
        ------------------
        Now, think about the question and answer the last step of the chain of thoughts. Note that you don't need to answer the question.
        Q: {question}
        """
    # endregion

    def Information_match(self, problem: str, input_prompts: list):
        check = ""
        for i, input_prompt in enumerate(input_prompts):
            check += f"{i+1}. {input_prompt} "
        prompt_ = f"""
        Suppose you are playing a matching game now. 
        You receive a problem in this game. Under this problems, you can just simply extract some basic information from the problem without any calculation.
        Alongside you receive a list of input requirements. You are required to determine whether the basic information you extracted can simply fulfil the 
        requirement one by one. During the matching for basic information and requirements, no logical deduction can be involved.
        Answer 1 if you think information could successfully match the requirement, else 0.
        Quote the answer with '[ ]'.
        
        example 1:
        ------------------
        Q: 
        Problem: The sum of the price of a pen and a ball is 11. The price of the pen is 10 more than the price of the ball. What is the price of the ball?
        Input Requirement: 1. Shows the system of the linear equation solve the problems. 2. Shows the text for building up systems of linear equation
        
        A: [0,1]
        
        Reason: 
        1. The problem content just does not directly relate to system of the linear equation. 
        Only after deductions made on problem, system of linear equation can be built 
        2. The given problems has given the text information for pen and ball prices. Satisfy the basic requirement
        ------------------
        
        example 2:
        Q:
        Problem: using addition/subtraction/multiplication/division, how can we get 24 from 3,4,5,6?
        Input Requirement: Shows the list of integer to build 24.
        
        A: [1]
        
        Reason:
        The problem has given four numbers already, 3,4,5,6. Therefore, this basic information could be extracted to satisfy the requirement.
        -----------------
        
        Now, think on this matching game.
        Q: 
        Problem: {problem}
        Input Requirement: {check}
        
        A:(Your answer)
        -----------------
        Note that only number 0,1 should be given in your answer. The Reason in the example just explain how the answer is chosen.
        """

        ret = get_chat(prompt_,model=self.model,temperature=self.temperature)
        ret = self._get_quoted_strs(ret)[0]
        ret = IntListConverter(ret)
        for index in sorted(ret, reverse=True):
            del input_prompts[index]

    def create_value(self, value_prompt: str, class_name: str):
        class temp_Value(Value):

        return

    def outputvalue_to_atomprompt(self, value_prompt: str):

        pass

    def atomprompt_to_inputvalue(self, atom_prompt: str):
        pass

    def thinking_process_IPO(self, question: str):
        print("start thinking Q:", question)
        ret = get_chat(self._init_think_prompt(question), model=self.model, temperature=self.temperature)
        output = self._get_quoted_strs(ret)[0]
        print("AI thinks the final output is:", output)
        output_embed = get_embedding_vector(output)
        ret = session.query_vector_index(f'{Value.BASE_CLS_NAME}_INDEX',1,output_embed)
        values: list[Value,...] = []
        if ret[0][1]>=0.9:
            output = ret[0][0]
            values.append(output)
            'TREE structure implement'
        else:


        '''
        prototype:
        use neo4j to search k closest output_value 
        values = [input/outputs to be check]
        if (chatgpt think is ok):
            values.append(output)
            tree = parent(output) 'later change to KG one'
        else:
            output = create_new_output_value in KG
            values.append(output)
            tree = parent(output)
        
        Information_match(question,values)
        while len(values): until chatgpt think directly match occur for all value
            value = values[0]
            values.pop(0)
            linked_atom = values.output_linked_atom (search for atom linked with this output in output relationship)
            if (linked_atom is null):
                linked_atom = create_new_atom in KG, build relationship for this atom and that output
                linked_atom->parent = value
                value->child = linked_atom
                search for required input atoms existed in KG
                if (input_atoms not in KG):
                    inputs_atom = create_new_value in KG, build
                    values.append(input_atoms)
            else:
                linked_atom->parent = value
                value->child = linked_atom
                input_atoms = linked_atom.inputs()
                values.append(intput_atoms)
    
        if out the loop -> all oldest input value are found:
        ask chatgpt to follow the tree structure to solve the problem
        and send out the final ans
        '''
        while not self.Information_match(question, output):



    # def think(self, question:str):
    #     print("start thinking Q:", question)
    #     ret = get_chat(self._init_think_prompt(question), model=self.model, temperature=self.temperature)
    #     last_step = self._get_quoted_strs(ret)[0]
    #     print("AI thinks the last step is:", last_step)
    #
    #     self.think_for_possible_func(last_step)

    def think_for_possible_func(self, purpose:str)->Atom:
        print('thinking for a suitable atom...')
        possible_atoms = k_similar_atoms(purpose)
        print('possible atoms:', [atom.atom_name() for atom in possible_atoms])
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
            print(f"AI thinks the function is: {atom.atom_name()}. "
                  f"Because: {reason}")
            return atom



