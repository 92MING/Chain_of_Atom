'''
Thinker is the main class for the whole running. Create a new instance of Thinker to start the thinking process.
'''
import re
from utils.AI_utils import ChatModel, get_chat, get_embedding_vector
from atoms import *
from data_struct.atom import *
from data_struct.value import *
from data_struct.converter import IntListConverter, Converter
from typing import Union
from data_struct.graph import Node, Graph
import ast
import copy
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
        '''This function aims to get the final output of the problem'''
        prompt = f"""
        Suppose you are solving a problem using 'Chain of Thoughts' method, and you are now thinking the final outputs of the problem,
        which means that you are now reaching the solution of the problem.
        No calculation is required in this task. You are required to identify what types of final outputs should be
        Quote the final output with '[ ]'.

        e.g.
        ------------------
        Q: The sum of the price of a pen and a ball is 11. The price of the pen is 10 more than the price of the ball. What are the prices of the ball and pen?
        A: Final output : [Solution of system of linear equations of this problem].  
        ------------------
        Now, think about the final output of this question. You do
        Q: {question}
        Note that no explanation are required, just the final output is needed.
        """
        ret = get_chat(prompt, model=self.model, temperature=self.temperature)
        return self._get_quoted_strs(ret)[0]

    def _step_think_atom(self, question: str, situation: int, thought: Node = None):
        '''As COA aims to think inversely, this function will inversely think further atoms and output needed step by step'''
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
        Note that finishing chains are connected by a symbol '<-' 
        Quote the nearest step and corresponding inputs with '[ ][ ]'.

        example 1:
        ------------------
        Q: 
        Problem: The sum of the price of a pen and a ball is 11. The price of the pen is 10 more than the price of the ball. What are the price of the ball and pen?
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
        Now, think about the question and answer the nearest step and input(s) of the chain of thoughts. Note that you don't need to answer the question and input(s) could be multiple if they cant be summarized in single term and separated by a comma inside the same [ ].
        Q: {question}
        Situation: {situation}
        """
        if situation == 2:
            extra = "?"
            parent_atom = thought.parents[0]
            while len(thought.parents) == 0:
                extra = f"[{parent_atom.promptedobj.prompt}][{thought.promptedobj.prompt}]<-" + extra
                thought = parent_atom.parents[0]
            extra = "Groups of Finishing Chains: " + extra
            prompt += extra
        ret = get_chat(prompt, model=self.model, temperature=self.temperature)
        atom_prompt, input_value_prompts = self._get_quoted_strs(ret)
        if ',' in input_value_prompts:
            input_value_prompts = re.split(r'\s*,\s*', input_value_prompts)
        else:
            input_value_prompts = [input_value_prompts]
        return [atom_prompt,input_value_prompts]

    def _information_match(self, problem: str, input_prompts: list):
        '''This function aims to check whether current information are needed to solve the problem'''
        check = ""
        for i, input_prompt in enumerate(input_prompts):
            check += f"Information {i+1}. Is {input_prompt.prompt} provided in the problem?\n"
        prompt_ = f"""
        Suppose you are solving a problem using 'Chain of Thoughts' method.
        Each chain under this problem is called a step, and the problem could be solved step by step (chain by chain). For each chain, only a tiny step should be processed.
        You now receive a text called problem which to be solved using chain of thoughts method and some questions the existence of the information.
        Current situation is you are now located in the first chain, steps to solve the problem.
        For the first step of the chain of thought, you should extract some useful information from the information to prepare solving this problem.
        You would be given some questions, determining whether this would be some information that you can extract in the first step.
        Therefore, the task would be determining some information could be extracted in the first step.
        originally, the first step would be thinking on what useful information provided in the problem help solve the problem, and then build up those information to get the answer.
        In a contradict, now you are required to determine whether some information are provided in the problem or not and should be used in the first step.
        Try to firstly understand the question, what information it seeking, and trace back to the content of problem. Tracing back whether the problem provided these information to extract at the first place and should be used as the first step.
        Fully analysis on the problem is required, as you have to determine whether these information are fake, and not provided in the problem.
        
        Answer 1 if you think this information is the true, otherwise 0 should be given.
        The basic thoughts could be multiple, with the number denoted.
        Quote the answer within '[ ]'. Answer for multiple basic thoughts should be separated by comma, in the same '[ ]'. You are required to consider each basic thought separately.
        
        Example 1 and 2 showing how the problems should be tackled.
        example 1:
        ------------------
        Q: 
        Problem: The sum of the price of a pen and a ball is 11. The price of the pen is 10 more than the price of the ball. What is the price of the ball?
        Question: 
        Information 1. Is the system of the linear equation in mathematical format provided in the problem?
        Information 2. Is word expression of math equations provided in the problem?
        Information 3. Is find solution of the system of linear equation provided in the problem?
        
        Answer : [0,1,0]
        
        Reason:
        [0,1,0] means only information 2 is the true information that is provided in the problem.
        There are some explanations.
        
        For information 1, the question here is asking whether the system of the linear equation in mathematical format is provided in the problem. By tracing back the content of the problem. There is only words expression of equation about pen and ball, no maths equation like '4x+y=10' is provided. Therefore, this is false information, no such inforamtion are provided.
        
        For information 2, the question here is asking whether word expression of math equations is provided in the problem. Since "The sum of the price of a pen and a ball is 11. The price of the pen is 10 more than the price of the ball." is the mathematical equation expressed by words and provided in the problem. Moreover, the word expression should be used in the first step. Therefore, this is true information.
        
        For information 3, the question here is asking whether solution of the system of linear equation is provided in the problem. Obviously, no solution of th system of linear equation are provided in the text. And this should be the final step of this problem. It is clearly to determine that this should be false information provided by the problem.
        
        Therefore, it clear shows that you have to think with procedure:
        1. fully understand what the information question seeking.
        2. Are these information are clearly provided in the first place?
        ------------------
        
        example 2:
        ------------------
        Q:
        Problem: using addition/subtraction/multiplication/division, how can we get 24 from 3,4,5,6?
        Question: 
        information 1. Is the list of integer used to build 24 provided in the problem?
        information 2. Is the answer of the formula that build 24 provided in the problem?
        Answer : [1,0]
        
        Reason:
        [1,0] means only information 1 is the true information that provided in the problem.
        There are some explanations.
        
        For information 1, the question here is asking whether the list of integer used to build 24 is provided in the problem. Since it is obviously provided in the problem.
        
        For information 2, the question here is asking whether the answer of the formula that build 24 is provided in the problem. Again, tracing back the problem, it is not provided a answer of formula to build 24.
        -----------------
        
        Now, think on this.
        Q: 
        Problem: {problem}
        Question: 
        {check}
        A:(Your answer) 
        -----------------
        """

        ret = get_chat(prompt_, model=self.model, temperature=self.temperature)
        print(ret)
        ret = self._get_quoted_strs(ret)
        ret = NumListConverter.convert(ret)
        ret = [i for i in range(len(ret)) if ret[i] == 1]
        for index in sorted(ret, reverse=True):
            print(f"AI think {input_prompts[index]}, this input value could be fulfilled directly, no extra atom is required for this part")
            del input_prompts[index]

    def _datatype_guess(self, input_prompt):
        '''Guess the datatype of the value'''
        prompt_ = f"""
        There are some python datatype: str,int,float,list,dict,bool.
        str: string
        int: integer
        float: floating point number
        list: multiple element storage
        dict: dictionary, a mapping function in python
        In python environment, each variable would be assigned a datatype. 
        Currently, you are required to guess the datatype of a variable (str,int,float,list,dict,bool).
        During this guessing, you will be given the information of this variable.
        Quote the answer in [ ]. You should answer one of the datatype (str,int,float,list,dict,bool).
        -----------------
        Example 1:
        Information: calculation result of a formula
        Answer: float
        
        Reason: It is because floating point number are needed to represent if the calculation result involves floating point, like 4/3 = 1.3333333.
        -----------------
        Example 2:
        Information: solution of a system of linear equations
        Answer: dict
        
        Reason: It is because the variables ans their solution should be stored in mapping format, like [{{'x':3,'y':4}}] for their system of linear equation. 
        -----------------
        
        Now, think on this extraction game.
        Q: 
        Information: {input_prompt}
        Answer: (Your answer)
        -----------------
        """
        ret = self._get_quoted_strs(get_chat(prompt_, model=self.model, temperature=self.temperature))[0]
        ret = ret.lower()
        mapping = {'str': str, 'int': int, 'float': float, 'list': list, 'dict': dict, 'bool': bool}
        return mapping[ret]

    def _keep_explore_atom(self, node, chains_of_node, lists_of_value, lists_of_io_node):
        '''if current lowest atom still can't be solved directly, more atoms are needed to build from this'''
        atom, input_value_lists = self.extend_graph_in_question(node, chains_of_node)
        print("New atom should be used", atom, " ", atom.prompt)
        new_thought = Node(atom)
        node.insert_children(new_thought)
        new_thought.insert_parent(node)

        thought = new_thought
        print("Input value of this atom should be", end=" ")
        for input_value in input_value_lists:
            print(input_value.prompt, end=" ")
            # adding this value into preprocessing list
            lists_of_value.append(input_value)
            new_thought = Node(input_value)
            lists_of_io_node.append(new_thought)

            # inserting this input value as child of atom, atom as parent of input value
            thought.insert_children(children=new_thought)
            new_thought.insert_parent(thought)
        print("")

    def _voting_for_ans(self, result, question, k, limit):
        '''valid the final answer k-times'''
        valid = 0
        for i in range(k):
            valid += self._ans_valid_check(result, question)
        if valid/k >= limit:
            return True
        else:
            return False

    def _ans_valid_check(self, result, question):
        '''Validation on the answer generated, checking its correctness'''
        '''Checking whether the answer generated is correct or not'''
        prompt_ = f"""
        You are now checking the answer generated by you previously, based on a question.
        Try to think whether the answer you generated before is correct or not.
        If you think it is correct, please answer 1 to valid the correctness, otherwise answer 0.
        Quote your answer in [ ]
        
        Here are some example situation for you to follow:
        -----------------
        example 1:
        Question: The price of tha ball and pen are 10, and the price of the ball minus the pen's are 2. What is the price of pen?
        Answer: {{pen: 4, ball: 6}}
                
        VALIDATION: [1]
        
        Explanation: check 6+4=10, 6-4=2. Both variables suit to what the question required. Therefore, 1 is given, which is true.
        -----------------
        
        example 2:
        Question: The price of the ball and pen are 10, and the price of the ball minus the pen's are 2. What is the price of pen?
        Answer: {{pen: 5, ball:5}}
        
        VALIDATION: [0]
        
        Explanation: only the first requirement is satisfied, 5+5=10, while the price of the ball minus the pen's are not 2. Therefore, 0 is given, which is false.
        -----------------
        Here are the answer that you are required to valid.
        Question: {question}
        Answer: {result}
        
        VALIDATION: (your answer)
        -----------------
        Please note that only 1 or 0 is needed, explanations are just reference, you need not to give the explanations.
        """
        ret = self._get_quoted_strs(get_chat(prompt_, self.model, self.temperature))[0]
        while not (ret == '1' or ret == '0'):
            ret = self._get_quoted_strs(get_chat(prompt_, self.model, self.temperature))[0]
        if ret == '1':
            return 1
        return 0

    def _ans_extract(self, result, question):
        '''Remove any unnecessary answer to this question'''
        prompt_ = f"""
        You are now checking the answer generated by you previously, based on a question.
        Try to determine there exists unnecessary answer which the question doesn't require in the generated result or not. It is sure that the answer given is correct, but may contain redundant information.
        You can either remove unnecessary answer if you find it, or keep the answer remain unchanged.
        Quote your answer in [ ]

        Here are some example situation for you to follow:
        -----------------
        example 1: 
        Question: The price of tha ball and pen are 10, and the price of the ball minus the pen's are 2. What is the price of pen?
        Answer: {{pen: 4, ball: 6}}

        Refined: [{{pen: 4}}]

        Explanation: only prices of pen is needed. Therefore, the price of the
        ----------------

        example 2:
        Question: The price of tha ball and pen are 10, and the price of the ball minus the pen's are 2. What is the price of pen and ball?
        Answer: {{pen: 4, ball: 6}}

        Refined: [{{pen: 4, ball: 6}}]

        Explanation: prices of pen and ball are both needed. These two answer are not redundant. Therefore, the whole answer remain unchanged.
        ----------------
        Here are the answer that you are required to refine.
        Question: {question}
        Answer: {result}

        Refined: (your answer)
        ---------------
        Please note that explanations are just reference, you need not to give the explanations.
        """
        ret = self._get_quoted_strs(get_chat(prompt_, self.model, self.temperature))[0]
        return ret

    def _prompt_for_prompt_generation(self):
        prompt_ = f"""
        You are now required to generate some prompt so that you can generate a answer 
        """
        pass

    def _check_generative_tasks(self):
        prompt_ = f"""
        
        """
        pass

    def _python_code_for_atom(self, input_values, output_values, atom_prompts, false_codes: list[str, ...]) -> str:
        '''python scripts for atoms that could be processed by python/ without gpt directly'''
        if len(false_codes)==0:
            _false_codes = "No false code is provided in this problem"
        else:
            _false_codes = "Here are some false code example to build this function, you may debug one of them or create a new function to the atom \n"
            for i, false_code in enumerate(false_codes):
                _false_codes += f"false code {i+1}: {false_code}"
            _false_codes += "you are reminded that you should only give a function only, ether do a debug on the previous false example, or give a new function"

        input_values_prompt = output_values_prompt =  ""
        for i, input_value in enumerate(input_values):
            input_values_prompt += f"input {i+1}: {input_value.prompt}, input datatype {i+1}: {input_value.expected_type}\n"

        for i, output_value in enumerate(output_values):
            output_values_prompt += f"output {i+1}: {output_value.prompt}, output datatype {i+1}: {output_value.expected_type}\n"

        prompt_ = f"""
        You are now required to play a python code exercise.
        Under this challenge, you will be given a list of inputs, outputs and purpose of the function in python or even some false code.
        For the lists of input or output, we would also give the datatype of the input/output in python.
        However, the code of the function is missing. You are required to think about the code inside the function.
        false code of this function would be provided in some cases, if false code are provided, they are the false code example on this function
        Quote the function script in [ ]. Note that extra package in python could also be used.
        Note that the name of the function should be 'run', you must follow this format [def running(cls, ...): ...]
        The input argument of the function could be freely named, yet the arguments should follow the index of the input given.
        Here are some examples for different function.
        -----------------
        example 1:
        purpose: summation of two number
        input 1: number A, input datatype 1: float
        input 2: number B, input datatype 2: float
        output 1: the result, output datatype 1: float
        Answer:
        [def running(cls,A,B):\n    return sum(A,B)]
        ----------------
        example 2:
        purpose: solve the simultaneous equation
        input 1: system of linear equation, input datatype 1: list
        output 1: the solution of system of linear equation, output datatype 2: dict
        Answer:
        [def running(cls,system1):\n    _replace = {{chr(0x2212): '-',}}\n    for key, value in _replace.items():\n        system = [equation.replace(key, value) for equation in system]\n    system = [sympy.parse_expr(equation, transformations=sympy.parsing.sympy_parser.T[:11]) for equation in system]\n    system = [sympy.sympify(equation) for equation in system]\n    ans = sympy.solve(system)\n    return ans]
        ----------------
        Here are the question that you are required to solve.
        Question:
        purpose: {atom_prompts}
        {input_values_prompt}
        {output_values_prompt}
        {_false_codes}
        Answer: 
        [ ]
        """
        ret = self._get_quoted_strs(get_chat(prompt_, model=self.model, temperature=self.temperature))[0]
        return ret

    def example_format_form(self, data_types, input_prompt):
        '''Returning output format of new Value'''
        prompt_ = f"""
        You are now facing a challenge related to python,
        you will be given the datatype about a variable and a description on that.
        Try to think a correct example of the content of the variable.
        Quote the answer with a extra ( ).
        
        Here are some example situation for you to follow:
        -----------------
        example 1:
        Data_types: dict
        Description: the solution of a system of linear equations
        
        Answer: ({{x:5,y:10}})
        
        Explanation: the {{}} showcases the dict datatype in python, two variable (x,y) are mapped to (5,10), could be a solution of a system of linear equation.
        Therefore, the answer is a correct example content.
        -----------------
        example 2:
        Data_types: list
        Description: permutation of a list of number
        
        Answer: ([[1,2,3],[1,3,2],[2,1,3],[2,3,1],[3,1,2],[3,2,1]])
        
        Explanation: the [] showcases the list datatype in python, three number is used in the example to represent the permuataion of a list of number.
        -----------------
        EXTRA INFORMATION:::
        There are some python datatype: str,int,float,list,dict,bool.
        str: string
        int: integer
        float: floating point number
        list: multiple element storage
        dict: dictionary, a mapping function in python
        -----------------
        Here are the question that you are required to answer.
        Data_types: {data_types}
        Description: {input_prompt}
        
        Answer: (your answer)
        ----------------
        Please note that explanations are just reference, you need not to give the explanations.
        """
        ret = get_chat(prompt_, self.model, self.temperature)
        return re.findall(r'.*?\((.*?)\).*?', ret)[0]


    def _create_promptedobject(self, promptetype: Union[Atom, Value], prompt_: str, sub_cls_name: str, input_value: list, output_value: list):
        '''Creating new atom and value needed'''
        if promptetype == Atom:
            class TempPromptedObject(promptetype):
                prompt = prompt_
                inputs = tuple(*input_value)
                outputs = tuple(*output_value)
                @classmethod
                def run(cls, *inputs):
                    cls.function_create()
                    ast_obj = ast.parse(cls.scripts)
                    plain_text = ast.unparse(ast_obj)
                    exec(plain_text)
                    return cls.running(*inputs)
                @classmethod
                def function_create(cls, change=False):
                    if change:
                        cls.false_codes.append(cls.scripts)
                        cls.scripts = self._python_code_for_atom(input_value, output_value, prompt_, cls.false_codes)
                    else:
                        if cls.scripts is not None:
                            return cls.scripts
                        else:
                            cls.scripts = self._python_code_for_atom(input_value, output_value, prompt_, cls.false_codes)

        elif promptetype == Value:
            class TempPromptedObject(promptetype):
                prompt = prompt_
                expected_type = self._datatype_guess(prompt_)
                converter = Converter[expected_type]
                example_prompt = self.example_format_form(expected_type, prompt)
        else:
            return None

        TempPromptedObject.__qualname__ = sub_cls_name
        TempPromptedObject.cls_dict()[sub_cls_name] = TempPromptedObject
        return TempPromptedObject

    # endregion
    def create_atom_input_value(self,input_value_prompts, atom_prompt, value):
        '''no atom could be used. We have to create it by ourselves.'''
        input_value_lists = []
        '''list stores the input values used for this atom'''

        print(f"Creating new atom with {atom_prompt}")
        for input_value_prompt in input_value_prompts:
            print(f"Creating {atom_prompt} input prompt: {input_value_prompt}")
            input_value = self._create_promptedobject(promptetype=Value, prompt_=input_value_prompt, sub_cls_name=input_value_prompt)
            cypher = input_value.create_subcls_cyphers()
            session.run(cypher)
            input_value_lists.append(input_value)

        atom = self._create_promptedobject(promptetype=Atom, prompt_=atom_prompt, sub_cls_name=atom_prompt, input_value=input_value_lists, output_value=[value])
        cypher = atom.create_subcls_cyphers()
        session.run(cypher)
        cypher1 = atom.build_output_relationship_value()
        cypher2 = atom.build_input_relationship_value()
        session.run(cypher1)
        session.run(cypher2)
        return atom, input_value_lists

    def _fix_cycle(self,):
        '''If cycle found in graph using to solve the problem, then need to clear the recursion build in kg'''
        pass

    def _fix_atom(self, atom):
        '''If error in new-created atom, fix it here'''
        try:
            function_create = getattr(atom, 'function_create')
            if callable(function_create):
                function_create(atom, True)
        except:
            def function(cls, change=False):
                if change:
                    cls.false_codes.append(cls.scripts)
                    cls.scripts = self._python_code_for_atom(atom.inputs, atom.outputs, atom.prompt, cls.false_codes)
                else:
                    if cls.scripts is not None:
                        return cls.scripts
                    else:
                        cls.scripts = self._python_code_for_atom(atom.inputs, atom.outputs, atom.prompt, cls.false_codes)
            def run(cls, *inputs):
                cls.scripts = cls.function_create(True)
                ast_obj = ast.parse(cls.scripts)
                plain_text = ast.unparse(ast_obj)
                exec(plain_text)
                return cls.running(*inputs)
            atom.function_create = function
            atom.run = run

    def _check_for_correctness(self, ret, chains_of_node, lists_of_value, lists_of_io_node):
        '''Function to check whether error in running and solve the error'''
        while isinstance(ret, Node):
            print("need to correct, node: ", ret.promptedobj)
            promptedobj = ret.promptedobj
            if promptedobj.BASE_CLS_NAME == 'Atom':
                self._fix_atom(promptedobj)
            elif promptedobj.BASE_CLS_NAME == 'Value':
                self._keep_explore_atom(ret, chains_of_node, lists_of_value, lists_of_io_node)
            ret = chains_of_node.run_the_tree()
            print(ret)
        return ret

    def extend_graph_in_question(self, thought, chains_of_node):
        '''Given a output, find or create the atom and its inputs'''
        # search whether we have atom linked with this value (in output relationship)
        value = thought.promptedobj
        question = chains_of_node.question
        ret = session.query_linked_relationship(value.BASE_CLS_NAME, value.cls_name(), 'OUTPUT')
        list_of_atom = [Atom.cls_dict()[atom[0]] for atom in ret if atom[0] in Atom.cls_dict().keys()]
        '''Stores the atoms that have output relationship with this value'''
        print("linked atoms: ", list_of_atom)

        if len(list_of_atom) == 0:
            # if no atom are linked
            print("currently, no Atom with output relationship on that output Value")
            # need to search unlinked atom by ourselves, asking their prompts first
            if chains_of_node.head == thought:
                [atom_prompt, input_value_prompts] = self._step_think_atom(question, 1)
            else:
                [atom_prompt, input_value_prompts] = self._step_think_atom(question, 2, thought)

            # searching current atom having similar prompt or not
            atom = self.think_for_possible_func(atom_prompt, [value], False)

            if atom is None:
                # No atom could be used to solve this problem in the kg
                atom, input_value_lists = self.create_atom_input_value(input_value_prompts, atom_prompt, value)

            else:
                # atom with similar prompt existed in the kg
                print(f"successfully searching in kg")
                session.create_relationship('Value', value.cls_name(), 'Atom', atom.cls_name(), 'OUTPUT')
                input_value_lists = session.query_linked_relationship(atom.BASE_CLS_NAME, atom.cls_name(), 'INPUT')

                if input_value_lists is None:
                    # input value doesnt assigned for that atom(actually impossible), could be solved by using the input_prompts
                    raise Exception("Something goes wrong(input_value)")
                else:
                    input_value_lists = [Value.cls_dict()[input_value[0]] for input_value in input_value_lists]

        else:
            # linked relationship could be found
            if chains_of_node.head == thought:
                [atom_prompt, input_value_prompts] = self._step_think_atom(question, 1)
            else:
                [atom_prompt, input_value_prompts] = self._step_think_atom(question, 2, thought)

            # check under these linked relationships, useful atom exist or not
            atom = self.think_for_possible_func(atom_prompt, [value], True, list_of_atom)
            if atom is None:
                # No linked atom could be used to solve this problem in the kg
                atom, input_value_lists = self.create_atom_input_value(input_value_prompts, atom_prompt)

            else:
                input_value_lists = session.query_linked_relationship(atom.BASE_CLS_NAME, atom.cls_name(), 'INPUT')
                if input_value_lists is None:
                    raise Exception("Something goes wrong(input_value)")
                else:
                    print(input_value_lists)
                    input_value_lists = [Value.cls_dict()[input_value[0]] for input_value in input_value_lists]

        return atom, input_value_lists

    def think(self, question: str):
        '''The overall algorithm'''
        lists_of_io_node: list[Node, ...] = []
        '''the list of storing unprocessed node instance of input/output value used in this problem'''
        lists_of_value: list[Value, ...] = []
        '''the list of storing unprocessed the value class used in this problem'''

        print("start thinking Q:", question)
        output = self._init_think_output(question)
        print("AI thinks the final output is:", output)
        output_embed = get_embedding_vector(output).tolist()

        # try to search the output value in kg with similar prompt as output
        ret = session.query_vector_index(f'{Value.BASE_CLS_NAME}_INDEX', output_embed, 3, True, False)
        if ret[0][0]['score'] >= 0.95:
            output_value = Value.cls_dict()[ret[0][0]['name']]

        else:
            # there is no required output value, i.e. we have to create one
            output_value = self._create_promptedobject(promptetype=Value, prompt_=output, sub_cls_name=output)
            cypher = output.create_subcls_cyphers()
            session.run(cypher)

        print(output_value, output_value.prompt)

        lists_of_value.append(output_value)

        thought_of_value = Node(output_value)
        '''all variable related to thought, are the node instance of input/output/atom'''
        lists_of_io_node.append(thought_of_value)

        chains_of_node = Graph(question, thought_of_value)
        '''A Graph instance that connect all the node used in this problem'''
        # TODO:: fix the chains of atom as well as the _step_think_prompt
        self._information_match(question, lists_of_value)

        while len(lists_of_value) > 0:
            # firstly, value and thought (node instance of that value) are poped
            value = lists_of_value.pop(0)
            print('current output_value needed: ', value.prompt)
            thought = lists_of_io_node.pop(0)

            atom, input_value_lists = self.extend_graph_in_question(thought, chains_of_node)

            # finish the find of atom and its input values in kg
            print("Therefore, atom should be: ", atom.prompt)
            new_thought = Node(atom)

            # insert the atom as the child of the output value, output value as the parent of atom
            thought.insert_children(children=new_thought)
            new_thought.insert_parent(thought)

            thought = new_thought
            print("Input value of this atom should be", end=" ")
            for input_value in input_value_lists:
                print(input_value.prompt, end=" ")
                # adding this value into preprocessing list
                lists_of_value.append(input_value)
                new_thought = Node(input_value)
                lists_of_io_node.append(new_thought)

                # inserting this input value as child of atom, atom as parent of input value
                thought.insert_children(children=new_thought)
                new_thought.insert_parent(thought)

            print("")

            # searching any values could be deal with gpt directly, i.e. final node of the path of a tree(leaf)
            self._information_match(question, lists_of_value)

        # finish the process of finding the atom and values to solve the problem, try to run.
        ret = chains_of_node.run_the_tree()
        if ret == 'cycle error':
            self._fix_cycle()
            return self.think(question)
        ret = self._check_for_correctness(ret, chains_of_node, lists_of_value, lists_of_io_node)
        if self._voting_for_ans(ret, question, 10 ,0.8):
            return self._ans_extract(ret, question)
        return self.think(question)


    def think_for_possible_func(self, purpose:str, outputs, linked: True, lists_atom:[Atom,...] = [])->Atom:
        if linked:
            print('thinking for a suitable atom in linked_relationship...')
            possible_atoms = lists_atom
        else:
            print('thinking for a suitable atom...')
            possible_atoms = k_similar_atoms(purpose)
        print('possible atoms:', [atom.cls_name() for atom in possible_atoms])
        all_func_prompts = ""
        outputs_prompts = ','.join([f'{output.prompt}' for output in outputs])
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
        Consider more about the outputs of the functions whether could give you the answer directly. Note that a function may have many outputs, if the output required having inside the function outputs lists, then that function also could be chosen as one of the best.
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
        Q: Purpose: Find a solution for {{"x-y=1", "x+y=2"}} Output: the solution of the system of linear equations
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
        Q: Purpose: A pen is 10 more expensive than a ball, and the sum of the price of a pen and a ball is 11. What is the price of the ball? Output: the price of the ball.
        A: [no]. [No function could be used directly.]
        ------------------

        Now, you are given the following funcs and purpose:
        ------------------
        {all_func_prompts}
        Purpose: {purpose} Outputs: {outputs_prompts}
        ------------------
        Note that you just need to give out the index of the function.
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
            print(f"AI thinks the function is: {atom.cls_name()}. "
                  f"Because: {reason}")
            return atom



