import numpy as np
from data_struct.promptedObj import *
from data_struct.value import Value
from typing import Tuple, Union
from utils.AI_utils import get_embedding_vector
from utils.global_value_utils import GetOrAddGlobalValue
from utils.neo4j_utils import neo4j_session

class AtomMeta(PromptedObjMeta):
    '''AtomMeta is a baseclass for Atom. It is for doing some initialization work when a Atom subclass is defined.'''
    BASE_CLS_NAME = 'Atom'
    ADD_TO_KG = True
    INIT_PRIORITY = 1 # atom should be initialized after all values are initialized

    @classmethod
    def create_subcls_cyphers(cls, subcls):
        return f"""
        CREATE (n:{cls.BASE_CLS_NAME} 
        {{
            name: "{subcls.cls_name()}", 
            prompt: "{subcls.prompt}",
            prompt_embed: {subcls.prompt_embedding().tolist()}
        }})
        """

    @classmethod
    def update_subcls_cyphers(cls, subcls) ->Union[list, str]:
        return f"""
        MATCH (n:{cls.BASE_CLS_NAME} {{name: "{subcls.cls_name()}"}}) 
        SET 
            n.prompt = "{subcls.prompt}",
            n.prompt_embed = {subcls.prompt_embedding().tolist()}
        """

    @classmethod
    def build_output_relationship_value(cls, subcls):
        output = subcls.outputs
        cypher =  f"MATCH (into_node: Value), (out_node: Atom {{name: '{subcls.cls_name()}'}}) WHERE "
        for i in range(len(output)):
            cypher += f"into_node.name = '{output[i].cls_name()}'"
            if i != len(output)-1:
                cypher += " OR "
        cypher += " CREATE (out_node)-[:OUTPUT]->(into_node)"
        return cypher

    @classmethod
    def build_input_relationship_value(cls, subcls):
        input = subcls.inputs
        cypher = f"MATCH (into_node: Atom {{name: '{subcls.cls_name()}'}}), (out_node: Value) WHERE "
        for i in range(len(input)):
            cypher += f"out_node.name = '{input[i].cls_name()}'"
            if i != len(input)-1:
                cypher += " OR "
        cypher += " CREATE (out_node)-[:INPUT]->(into_node)"
        return cypher

class Atom(PromptedObj, metaclass=AtomMeta):
    '''
    Atom is 1 single action with clear param/ result description. It is a basic unit of a step.
    Override this class to define your own atom.
    Note that all atoms should be static classes, with unique class name.
    '''

    inputs:Tuple[Value,...] = None
    '''Override this cls property to specify the input params of the atom.'''
    outputs:Tuple[Value,...] = None
    '''Override this cls property to specify the output params of the atom.'''
    scripts = None
    '''Override this cls property to specify the scripts of run function of the atom if atom's run function could not be prefined'''
    false_codes = []
    '''Stores false code used before in scripts'''

    def __init__(self):
        raise Exception("Atom is a static class, don't initialize it. You should herit to define your own atom with input/ output params and run method.")
    @classmethod
    def inputVals(cls):
        '''Get the inputted values of this atom. Note that "call" method should be called in advance.'''
        return tuple(val.value() for val in cls.inputs)
    @classmethod
    def input_prompt_embeds(cls):
        '''Get the prompt embed of each param this atom. '''
        return tuple(val.prompt_embed() for val in cls.inputs)
    @classmethod
    def outputVals(cls):
        '''Get the outputted values of this atom. Note that "call" method should be called in advance.'''
        return tuple(val.value() for val in cls.outputs)

    @classmethod
    def output_prompt_embeds(cls):
        '''Get the prompt embed of each param this atom. '''
        return tuple(val.prompt_embed() for val in cls.outputs)

    # region override
    @classmethod
    def kg_id(cls):
        '''override the original kg_id method to return the merged value node in some cases'''
        if cls._kg_id is None and cls.cls_name() not in ['Atom',',PromptedObj']:
            node = neo4j_session().run(f'match (n:{cls.BASE_CLS_NAME}) where n.name="{cls.cls_name()}" return elementId(n)').single()
            cls._kg_id = node[0]
        return cls._kg_id
    # endregion
    @classmethod
    def call(cls, *values):
        '''
        Call this atoms' function.
        Inputted values will be stored in each input param. You could access by self.inputVals.
        Outputted values will be stored in each output param. You could access by self.outputVals.
        '''
        print(cls.cls_name(), ' execute')
        # input values
        for i, value in enumerate(values):
            cls.inputs[i].input(value)

        # run the atom
        result = cls.run(*cls.inputVals())

        # save the result into output params
        if len(cls.outputs) > 1:
            for i, value in enumerate(result):
                cls.outputs[i].input(value)
        else:
            cls.outputs[0].input(result)
        return result

    @classmethod
    def run(self, *inputs):
        '''Run the atom. Override this method to implement the atom's function.'''
        raise NotImplementedError
# endregion

# region static methods
def all_atom_prompts()->Tuple[str, ...]:
    '''Get all atom prompts.'''
    return tuple(atom.prompt for atom in Atom.all_subclses())
def all_atom_inputs()->Tuple[Tuple[Value, ...], ...]:
    '''Get all atom input params.'''
    return tuple(atom.inputs for atom in Atom.all_subclses())
def all_atom_outputs()->Tuple[Tuple[Value, ...], ...]:
    '''Get all atom output params.'''
    return tuple(atom.outputs for atom in Atom.all_subclses())

def k_similar_atoms(prompt:str, k=5):
    '''Get k similar atoms with the input prompt.'''
    prompt_embed = get_embedding_vector(prompt)
    cypher = f'CALL db.index.vector.queryNodes("Atom_INDEX",{k},{prompt_embed.tolist()}) YIELD node return elementId(node)'
    atom_ids = neo4j_session().run(cypher).data()
    return [Atom.find_subcls_byID(atom_id['elementId(node)']) for atom_id in atom_ids]
