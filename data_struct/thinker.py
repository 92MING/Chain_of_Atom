'''
Thinker is the main class for the whole running. Create a new instance of Thinker to start the thinking process.
'''
import re
from utils.AI_utils import ChatModel, get_chat, get_embedding_vector
from atoms import *
from data_struct.atom import *
from data_struct.value import *
from data_struct.converter import IntListConverter
from typing import Union
from data_struct.tree import Node, Tree
from utils.neo4j_utils import neo4j_session


class Thinker:

    def __init__(self, model:ChatModel=ChatModel.GPT3_5, temperature=0.5):
        self.model = model
        self.temperature = temperature

    # region private methods
    def _get_quoted_strs(self, s:str):
        '''get the strings quoted by []'''
        return re.findall(r'.*?\[(.*?)\].*?', s)

    def _init_think_output(self, question: str):
        prompt = f"""
        Suppose you are solving a problem using 'Chain of Thoughts' method, and you are now thinking the final outputs of the problem,
        which means that you are now reaching the solution of the problem.
        No calculation is required in this task. You are required to identify what types of final outputs should be
        Quote the final output with '[ ]'.

        e.g.
        ------------------
        Q: The sum of the price of a pen and a ball is 11. The price of the pen is 10 more than the price of the ball. What is the price of the ball?
        A: Final output : [Solution of system of linear equations of this problem].  
        ------------------
        Now, think about the final output of this question. You do
        Q: {question}
        Note that no explanation are required, just the final output is needed.
        """
        ret = get_chat(prompt, model=self.model, temperature=self.temperature)
        return self._get_quoted_strs(ret)[0]

    def _step_think_atom(self, question: str, situation: int, finishing_chain: list[Atom] = None):
        prompt = f"""
        Suppose you are solving a problem using 'Chain of Thoughts' method, and you will face two situation according the question stated.
        For the first situation (1), you have come to the last step of the chain(It means after this step, you will get the answer).
        During the last step, what method should you use to solve it? Give a brief description of the method or the name of the method as well as the inputs of the method.
        Try to think of what should have been done before the last step & what you will get after the last step so as to help you think of the last step.
        Quote the last step and corresponding inputs with '[ ][ ]'.
        
        -----------------
        For the second situation (2), you have given a group of finishing chains(It means after these chains or steps, you will get the answer and solve the problem).
        However, There are some missing chains connecting the finishing chains and initial chain.(Initial chain refers to the original problem, not the first step of the solution).
        You have to think the nearest chain to connect the finishing chains, so that the missing chains could be slowly found and whole problem could be solved.
        During this nearest step or chain, what method should you use to connect to the finishing chains?  Give a brief description of the method or the name of the method as well as the inputs of the method.
        Try to think what should be done before getting those finishing chains & what you will get after the nearest chain so the output of the nearest chain can be suited to the input of the head of finishing chains.
        Quote the nearest step and corresponding inputs with '[ ][ ]'.

        example 1:
        ------------------
        Q: 
        Problem: The sum of the price of a pen and a ball is 11. The price of the pen is 10 more than the price of the ball. What is the price of the ball?
        Situation: 1
        A: Last step : [Solving system of linear equations][System of linear equations]. I should have listed out the equations before solving the last step. After finish the last step, I will get the value of the unknowns.
        ------------------
        
        example 2:
        ------------------
        Q:
        Problem: The sum of the price of a pen and a ball is 11. The price of the pen is 10 more than the price of the ball. What is the price of the ball?
        Situation: 2
        Groups of Finishing Chains: [Solving system of linear equation][System of linear equation]<-? 
        A: The nearest step: [Construct the system of linear equation][Short text describing the details of the equation]. 
        The final steps of this problem shown in finishing chains is solving system of linear equation with the required inputs, the sets of linear equation.
        I should have tried to figure out the text related to equation and then build up the equation sets for connecting the chain, fulfilling the inputs and then solve the linear equation later on.
        ------------------
        
        example 3:
        ------------------
        Q:
        Problem: 4 Cups of milk and 2 Coffee cost 70. 5 Cups of milk and 1 Coffee cost 60. Given that david have 70 dollars, How many possible cups of milk he can buy?
        Situation: 2
        Groups of Finishing Chains: [Calculation on a Formula][Formula of the integer division on 70 and Prices of cup of milk]<-[Solving system of linear equation][System of linear equation]<-?
        A: The nearest step: [Construct the system of linear equation][Short text describing the details of the equation].
        Two steps are given in the groups of the finishing chains. Final step of this problem is to do a calculation on integer division after we have solved the linear equation. Therefore, the chain of thought should be solving the linear equation and then do the calculation to know maximum number of milk David can buy.
        Therefore, to solve the linear equation and stated in the inputs part, we need to have the sets of equation first. Therefore, constructing the system of linear equation help connected the chains.
        ------------------
        Now, think about the question and answer the nearest step and input(s) of the chain of thoughts. Note that you don't need to answer the question and input(s) could be multiple if they can be summarized in single term and separated by a comma inside the same [ ].
        Q: {question}
        Situation: {situation}
        """
        if situation == 2:
            prompt += "Groups of Finishing Chains: "
            for chain in finishing_chain:
                prompt += f"[{chain.prompt}]["
                for i in range(len(chain.inputs)):
                    prompt += f"{chain.inputs[i].prompt}"
                    if i != len(chain.inputs)-1:
                        prompt += ","
                prompt += "]<-"
            prompt += "?"
        ret = get_chat(prompt, model=self.model, temperature=self.temperature)
        return self._get_quoted_strs(ret)

    def _information_match(self, problem: str, input_prompts: list):
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

    def _create_promptedobject(self, promptetype: Union[Atom,Value], prompt_: str, sub_cls_name: str, input_value: list, output_value: list):
        if promptetype == Atom:
            class TempPromptedObject(promptetype):
                prompt = prompt_
                inputs = tuple(*input_value)
                outputs = tuple(*output_value)
        elif promptetype == Value:
            class TempPromptedObject(promptetype):
                prompt = prompt_
        else:
            return None

        TempPromptedObject.__qualname__ = sub_cls_name
        TempPromptedObject.cls_dict()[sub_cls_name] = TempPromptedObject
        return TempPromptedObject

    # endregion

    def thinking_process_ipo(self, question: str):

        '''
        Explain on some variables in this function
        output_value: usually the output_value of a atom
        input_value : usually the input_value of a atom
        output_prompt: prompt of the output of a atom given by chat_model
        input_prompt(s): prompt of the input of a atom given by chat_model
        atom_prompt: prompt of the atom given by chat_model
        output_embed: embedding form of the prompt
        input_embed(s): embedding form of the prompt
        atom_embed: embedding form of the prompt
        thought: PromptedObj that will be used in solving this problem
        lists_of_thought: the list of storing unprocessed thought
        chains_of_thought: Representing all the PromptedObj involved in this problem
        list_of_atom: the descending list of atoms that will be involved in this problem
        '''

        lists_of_thought: list[Node,...] = []
        lists_of_value: list[Value,...] = []
        print("start thinking Q:", question)
        output = self._init_think_prompt(question)
        print("AI thinks the final output is:", output)
        output_embed = get_embedding_vector(output).tolist()
        ret = session.query_vector_index(f'{Value.BASE_CLS_NAME}_INDEX', 1, output_embed)

        if ret[0][1] >= 0.9:
            output_value = ret[0][0]

        else:
            output_value = self.create_promptedobject(Value, output, output)
            cypher = output.create_subcls_cyphers()
            session.run(cypher)
            output_value.kg_id()

        # print(output_value.prompt)
        lists_of_value.append(output_value)
        thought = Node(output_value)
        lists_of_thought.append(thought)
        chains_of_thought = Tree(thought)
        list_of_atom = []
        self.information_match(question, lists_of_value)

        while len(lists_of_thought) > 0:
            value = lists_of_value.pop(0)
            atom = Atom.cls_dict().get[session.query_linked_relationship(value.BASE_CLS_NAME, value.cls_name(), 'OUTPUT'), None]

            if atom is None:
                if len(list_of_atom) == 0:
                    [atom_prompt, input_value_prompts] = self._step_think_prompt(question, 1)
                else:
                    [atom_prompt, input_value_prompts] = self._step_think_prompt(question, 2, list_of_atom)

                input_value_prompts = re.split(r'\s*,\s*', input_value_prompts)

                input_value_lists = []
                for input_value_prompt in input_value_prompts:
                    input_value = self.create_promptedobject(Value, input_value_prompt, input_value_prompt)
                    cypher = input_value.create_subcls_cyphers()
                    session.run(cypher)
                    input_value_lists.append(input_value)

                    # new_thought = Node(input_value)
                    # thought.insert_child(new_thought)
                    # lists_of_thought.append(new_thought)

                atom = self.create_promptedobject(Atom, atom_prompt, atom_prompt, input_value_lists, [value])
                cypher = atom.create_subcls_cyphers()
                session.run(cypher)
                cypher1 = Atom.build_output_relationship_value(atom)
                cypher2 = Atom.build_input_relationship_value(atom)
                session.run(cypher1)
                session.run(cypher2)

            else:
                input_value_lists = session.query_linked_relationship(atom.BASE_CLS_NAME, atom.cls_name(), 'INPUT')
                if input_value_lists is not None:
                    lists_of_value.extend(input_value_lists)
                else:
                    raise Exception("Something wrong happen")



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
            pass

    def think(self, question:str):
        print("start thinking Q:", question)
        ret = get_chat(self._init_think_prompt(question), model=self.model, temperature=self.temperature)
        last_step = self._get_quoted_strs(ret)[0]
        print("AI thinks the last step is:", last_step)
        self.think_for_possible_func(last_step)

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



