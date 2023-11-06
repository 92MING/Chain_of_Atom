from data_struct.converter import Converter
from data_struct.promptedObj import *
import numpy as np
from utils.AI_utils import get_embedding_vector, get_chat, ChatModel
from typing import Callable, Union
from utils.neo4j_utils import neo4j_session
import re

class ValueMeta(PromptedObjMeta):
    BASE_CLS_NAME = 'Value'
    ADD_TO_KG = True

    # region override
    @classmethod
    def subcls_exist_in_kg(cls, subcls_name: str):
        exist = (neo4j_session().run(f'match (n:Value) where n.name="{subcls_name}" return n').single() is not None)
        if not exist:
            # check if it is included in a merged value node
            exist = (neo4j_session().run(f'match (n:MergedValue) where "{subcls_name}" in n.from return n').single() is not None)
        return exist
    @classmethod
    def subcls_need_update(cls, subcls: Union[type, 'PromptedObj']) -> bool:
        current_node_prompt = neo4j_session().run(f'match (n:{cls.BASE_CLS_NAME}) where n.name="{subcls.cls_name()}" return n.prompt').single()
        # if not found, current_node_prompt is None
        # if not found, means it is included in a merged value node. It will not be updated(currently not supported)
        if current_node_prompt is not None:
            current_node_prompt = current_node_prompt[0] # real n.prompt
        return current_node_prompt is not None and current_node_prompt != subcls.prompt
    @classmethod
    def create_subcls_cyphers(cls, subcls: Union['Value', type]):
        return f"""
        CREATE (n:{cls.BASE_CLS_NAME} 
        {{
            name: "{subcls.cls_name()}", 
            prompt: "{subcls.prompt}",
            expected_type: "{subcls._expected_type_name()}", 
            converter: "{subcls._converter_name()}", 
            default: "{subcls.default}",
            example_prompt: "{subcls.example_prompt}", 
            prompt_embed: {subcls.prompt_embedding().tolist()}
        }})
        """
    @classmethod
    def update_subcls_cyphers(cls, subcls: Union['Value', type]):
        return f"""
        MATCH (n:{cls.BASE_CLS_NAME} {{name: "{subcls.cls_name()}"}}) 
        SET 
            n.prompt = "{subcls.prompt}",
            n.expected_type = "{subcls._expected_type_name()}",
            n.converter = "{subcls._converter_name()}",
            n.default = "{subcls.default}",
            n.example_prompt = "{subcls.example_prompt}",
            n.prompt_embed = {subcls.prompt_embedding().tolist()}
        """
    # endregion

class Value(PromptedObj, metaclass=ValueMeta):
    '''
    Value is the base class of all input/ output params of an atom.
    Note that all Value subclasses should be static classes, with unique subclass name.
    '''

    expected_type: type = None
    '''Override this cls property to specify the expected type of the value.'''
    converter: Union[Converter, type] = None
    '''Override this cls property to specify the converter of the value.'''
    default: object = None
    '''Override this cls property to specify the default value of the value.'''
    example_prompt:str = None
    '''Override this cls property to specify the example prompt of the value. Example prompt is for teaching LM to know the format'''

    _value = None # store the real value of the param
    _prompt_embed : np.array = None # store the embedding of the prompt

    # region override
    @classmethod
    def kg_id(cls):
        '''override the original kg_id method to return the merged value node in some cases'''
        if cls._kg_id is None and cls.cls_name() not in ['Value',',PromptedObj']:
            node = neo4j_session().run(f'match (n:{cls.BASE_CLS_NAME}) where n.name="{cls.cls_name()}" return elementId(n)').single()
            if node is not None:
                cls._kg_id = node[0]
            else: # if it is included in a merged value node
                cls._kg_id = neo4j_session().run(f'match (n:MergedValue) where "{cls.cls_name()}" in n.from return elementId(n)').single()[0]
        return cls._kg_id
    # endregion

    # region private methods
    @classmethod
    def _converter(cls):
        '''the real converter'''
        if cls.converter is not None:
            if issubclass(cls.converter, Converter):
                return cls.converter
            elif isinstance(cls.converter, type):
                try:
                    return Converter[cls.converter]
                except KeyError:
                    return cls.converter
            else:
                return cls.expected_type
        else:
            try:
                return Converter[cls.expected_type]
            except KeyError:
                return cls.expected_type
    @classmethod
    def _convert(cls, value):
        '''try convert value to expected type or using given converter. If fail, return default value'''
        try:
            converter = cls._converter()
            if issubclass(converter, Converter):
                return converter.convert(value)
            else:
                return converter(value)
        except:
            return cls.default
    @classmethod
    def _converter_name(cls):
        '''try to return the converter's name. If no proper converter found, return "DIRECT_CONVERT"'''
        converter = cls._converter()
        if issubclass(converter, Converter):
            return converter.__qualname__
        else:
            return "DIRECT_CONVERT"
    @classmethod
    def _expected_type_name(cls):
        return cls.expected_type.__qualname__
    # endregion

    @classmethod
    def input(cls, value):
        if isinstance(value, cls.expected_type):  # no need to convert
            cls._value = value
        else:  # try to convert
            cls._value = cls._convert(value)
        return cls._value
    @classmethod
    def value(cls):
        return cls._value if cls._value is not None else cls.default
    @classmethod
    def prompt_embed(cls, embeder:callable=None):
        if cls._prompt_embed is None:
            if embeder is not None:
                cls._prompt_embed = embeder(cls.prompt)
            else:
                cls._prompt_embed = get_embedding_vector(cls.prompt)
        return cls._prompt_embed
    @classmethod
    def full_prompt(cls):
        '''Return both prompt and example prompt(if exists)'''
        if cls.example_prompt is None:
            return cls.prompt
        else:
            return f'{cls.prompt} (e.g.:{cls.example_prompt})'

    @classmethod
    def ask_for_input(cls,question, prompts, example_prompt):
        if prompts[-1] == '.':
            prompts[-1] = '?'
        elif prompts[-1] != '?':
            prompts = prompts + '?'
        prompts = 'give ' + prompts

        '''This only called if it is the bottom'''
        prompt = f'''
        You are now solving a problem, you are required to answer the question using from the information given in the problem.
        You will see that there is a question inside the problem, However, that is the final result the whole problem seeking.
        There will be another question stated in 'Question' which you will need to deal with.
        The question here is actually some pre-question involved in the whole problem, i.e you will need to tackle these questions in order to solve the whole problem.
        You have to find out a certain materials from the question stated.
        Here are two type of questions that you will face, single-step and multiple-steps questions.
        single-step questions are the questions which will only seek the content that the problem have given directly.
        ------------------
        Examples for single-step question:
        Problem: The price of the apple and orange is 10 and the price of the apple minus orange's is 1. What are the prices of the apple and orange?
        Question: give out the what type of fruit involved.
        
        
        That could be generalized that single-step questions only seek information that are directly shown in the problem side.
        Features of single-step questions:
        they seek contents that could be directly extracted, are directly shown in the problem only.
        ------------------
        multiple-steps question are the questions which the content of questions seeking has not given in the question. Therefore, multiple step are required to answer this question by firstly extracting some useful information from the problem and deriving the useful information to get the answer.
        
        Examples for multiple-steps questions:
        1)
        Problem: The price of the apple and orange is 10 and the price of the apple minus orange's is 1. What are the prices of the apple and orange?
        Question: give the solution of some math equation.
        2)
        Problem: There are many famous people in the world which sum of their day, month, year of birth equal to some special number. Can you name some famous people which sum of their day, month, year of birth respectively equal to 3000?
        Question: give some famous person which sum of the day, month, year of birth equal to 3000.
        
        That could be generalized that multiple-steps questions will seek the information that is not given in the problem.
        They will seek information that need to be derived, calculated or deduced from the background information the problem suggested. In some cases, their maybe even no information could be used in problem to support the derivation. Extra and specific knowledge is needed.
        
        As said, this then will need multiple-steps to tackle the questions. Therefore, they are called multiple-steps questions. 
        
        ------------------
        As said, under this problem, you have to face two kinds of problems.
        
        To deal with this situation, two thinking steps are needed to give correct answer of the questions.
        1. Try to think whether the question is a single-step question or multiple-step question. (check whether the content that question seeking provided in the problem or not)
        2. if the question is single-step question, then you have to solve it (For answering the single-step question, try to think how to extract the content of question seeking in the problem.). If the question are multiple-step question, please do not need to solve that, just answer 'no'. Because there maybe some faults in your derivations or calculations. 
        
        ------------------
        Moreover, during answering the single-step question, there is a guideline called output_format. output_format would be used as a answering template, it has no relationship with the problem and question. 
        Don't think the answer shown output format as information provided by the problem. It only shows a answering format that you have to follow in answering this question.
        Please quote the answer of the question with [ ].

        Here are some example problem and some procedure to solve the problem.
        ------------------
        example 1:
        ------------------
        Problem: a medicine A and another medicine B cost 100 dollars, price of a medicine B minus price of a A equal to 50 dollars. What are the prices of A and B?
        Question: give word expressing some equation on the A and B?
        Output format: 6 apples and a orange cost 18 dollars, 4 apples and a orange cost 14 dollars. for question: 6 apples and a orange cost 18 dollars, 4 apples and a orange cost 14 dollars. What are prices of apples and orange.
        Answer: [a medicine A and another medicine B cost 100 dollars, price of a medicine B minus price of a A equal to 50 dollars].
        
        Procedure:
        1. It is thought that the question 'find word expressing some equation on the A and B.' should be single step, as the related content are given in the text.
        2. It is single-step problem, keep answer this question by extracting the content, 'a medicine A and another medicine B cost 100 dollars, price of a medicine B minus price of a A equal to 50 dollars'.
        
        -----------------
        example 2:
        -----------------
        Problem: The sum of the price of a pen and a ball is 11. The price of the pen is 10 more than the price of the ball. What are the prices of pen and ball?
        Question: give the solution of system of linear equation?
        Output format: {{x:100, y:200, z:300}}
        Answer: [no].
        
        Procedure:
        1. It is thought that the question 'find the solution of system of linear equation.' should be multiple-steps. As the content of math equation has not given. It is suggested, multiple-steps like extractions and calculations are needed.
        2. Because it is a multiple-step question. you should answer 'no'.
        -----------------
        Refering to the output format shown in these two examples, these are formatting used to follow when the question is found as single-step question. Content in output format is not related to the answer of the question. Dont extract the answer in output format as the information provided by the question.
        IN other words, output format only used for single-step question. 
        -----------------
        example 3:
        -----------------
        Problem: Generate a HKDSE english mock paper 1, with part A,B1 and B2.
        Question: give the mock HKDSE english paper1? 
        Output format: """Article part A: xxxxxxxxxxx
                          Questions part A: xxxxxxxxx
                          Article part B1: xxxxxxxxxx
                          Questions part B2: xxxxxxxx
                          Article part B2: xxxxxxxxxx
                          Questions part B2: xxxxxxxx
                        """
        Answer: [no].
        
        
        Procedure:
        1.It is classified as multiple-step questions. Obviously, the question is asking what the problem asking, and there isn't any useful information to directly extract so that you can answer this question. Much steps are needed to build the paper/
        2. Therefore, as it is a multiple-step questions. 'No' should be answer.
        -----------------
        Now, think on this searching game.
        Problem: {question}
        Question: {prompts}
        Output format: {example_prompt}
        Answer: (your answer)
        Quote your answer with [ ]
        -----------------
        '''
        ret = get_chat(prompt, model=ChatModel.GPT3_5, temperature=0.5)
        ret = re.findall(r'.*?\[(.*?)\].*?', ret)
        if len(ret)>1:
            ans, reason = ret[:2]
        else:
            ans, reason = ret[0], 'No reason.'
        if 'no' in ans.lower():
            print('AI think no enough information to fulfil the input', reason)
            return None
        else:
            print('AI think the input could be fulfilled reason: ', reason)
            return ans

