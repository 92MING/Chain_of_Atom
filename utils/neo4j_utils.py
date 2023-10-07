import os
import time
from neo4j import GraphDatabase, Driver, Session
from utils.global_value_utils import GetOrAddGlobalValue
from utils.classes import CrossModuleEnum
from neo4j_backup import Extractor, Importer
from typing import Optional, Literal
from types import FunctionType
from functools import partial

_driver:'Neo4jDriver' = GetOrAddGlobalValue('_NEO4J_DRIVER', None)
'''the singleton neo4j driver'''''
_single_session:'Neo4jSession' = GetOrAddGlobalValue('_NEO4J_SINGLE_SESSION', None)
'''a single session for neo4j driver. You can use this session for non-transactional queries.'''''

class Neo4jDriver(Driver):
    @classmethod
    def cast(cls, driver: Driver) -> 'Neo4jDriver':
        for attr in dir(cls):
            if attr=='session' or not hasattr(Driver, attr):
                attr_value = getattr(cls, attr)
                if isinstance(attr_value, FunctionType):
                    setattr(driver, attr, partial(attr_value, driver))
                else:
                    setattr(driver, attr, attr_value)
        return driver
    def backup(self, dir_path:str, db='neo4j', compress=False, indent_size=4):
        '''warning: this method will delete all files in dir_path.'''
        print(f'backup neo4j database {db} to {dir_path}...')
        try:
            extractor = Extractor(project_dir=dir_path, driver=self, database=db,
                                  input_yes=True, compress=compress, indent_size=indent_size,
                                  pull_uniqueness_constraints=True)
            extractor.extract_data()
        except LookupError:
            print(f'neo4j database {db} is empty. No backup is needed.')
    def restore(self, dir_path:str, db='neo4j', overwrite=False):
        '''warning: if overwrite is True, this method will drop the db with the same name in order to restore the backup.'''
        try:
            if not self.has_db(db):
                self.create_db(db)
            else:
                if not overwrite:
                    print(f'neo4j database {db} already exists. Restore skipped.')
                    return
                else:
                    print(f'neo4j database {db} already exists. It will be dropped and restored.')
                    self.drop_db(db)
                    self.create_db(db)
            importer = Importer(project_dir=dir_path, driver=self, database=db, input_yes=True)
            importer.import_data()
        except FileNotFoundError:
            print(f'Target backup directory {dir_path} is not found. Restore skipped.')

    def drop_db(self, db):
        '''drop the database with the given name'''
        with self.session(database='system') as session:
            session.run(f'DROP DATABASE {db} IF EXISTS')
    def create_db(self, db, wait_for_ready=True, timeout=10):
        '''create a new database with the given name'''
        with self.session(database='system') as session:
            session.run(f'CREATE DATABASE {db}')
            if wait_for_ready:
                timecount = 0
                while timecount < timeout:
                    if session.run(f'show database {db} where currentStatus="online"').single() is not None:
                        return
                    time.sleep(1)
                    timecount += 1
    def has_db(self, db):
        '''check if the database with the given name exists'''
        with self.session(database='system') as session:
            return session.run(f'SHOW DATABASES').single()[0] == db
    def session(self, *args, **kwargs)->'Neo4jSession':
        session = Driver.session(self, *args, **kwargs)
        return Neo4jSession.cast(session)
class Neo4jSession(Session):
    @classmethod
    def cast(cls, session: Session) -> 'Neo4jSession':
        for attr in dir(cls):
            if not hasattr(Session, attr):
                attr_value = getattr(cls, attr)
                if isinstance(attr_value, FunctionType):
                    setattr(session, attr, partial(attr_value, session))
                else:
                    setattr(session, attr, attr_value)
        return session
    def show_indexes(self):
        '''
        show all indexes in the database
        :return: list of dict. e.g. [{'id': 2, 'name': 'index_f7700477', 'state': 'ONLINE', 'populationPercent': 100.0, 'type': 'LOOKUP', 'entityType': 'RELATIONSHIP', 'labelsOrTypes': None, 'properties': None, 'indexProvider': 'token-lookup-1.0', 'owningConstraint': None, 'lastRead': None, 'readCount': 0}]
        '''
        cypher = '''SHOW INDEXES'''
        return self.run(cypher).data()
    def has_index(self, index_name:str):
        '''
        check if the index with the given name exists
        :param index_name: the name of the index
        :return: bool
        '''
        cypher = f'''SHOW INDEXES WHERE name="{index_name}"'''
        return len(self.run(cypher).data()) > 0
    def create_vector_index(self, name, label, propertyKey, vector_dimension, similarity_function:Literal['euclidean', 'cosine']='cosine',
                            overwrite=False):
        '''
        Create a vector index. Neo4j version >= 5.11 is required.
        :param name: the name of the index
        :param label: the label of the nodes to be indexed
        :param propertyKey: the key property of the nodes to be indexed
        :param vector_dimension: the dimension of the vector
        :param similarity_function: the similarity function of the vector [euclidean, cosine]
        :param overwrite: if True, the index with the same name will be dropped and recreated.
        '''
        if self.has_index(name):
            if not overwrite:
                return
            else:
                self.drop_index(name)
        cypher = f'CALL db.index.vector.createNodeIndex("{name}", "{label}", "{propertyKey}", {vector_dimension}, "{similarity_function}")'
        self.run(cypher)
    def query_vector_index(self, name, number, prompt_embed):
        '''
        Find a group of nodes in KG with similar prompt_embed. Neo4j version >= 5.11 is required.
        :param name: the name of the index
        :param number: number of the most similar embedding
        :param prompt_embed: the embedding vector of the prompt want to be searched
        '''
        if self.has_index(name):
            cypher = f'CALL db.index.vector.queryNodes("{name}", {number}, {prompt_embed}) YIELD node AS similarPrompt, score RETURN similarPrompt.name AS cls_name, score'
        records = self.run(cypher)
        return records.values()

    def query_linked_relationship(self,node_label: str,node_name: str, relationship: str):
        '''
        Find the nodes linked with the node with node_name and in that relationship
        :param node_label: the label of the node
        :param node_name: the name of the node
        :param relationship: the name of the relationship of these two nodes
        '''
        'Check existence of the node'
        cypher = f'match (n:{node_label}) where n.name="{node_name}" return n'
        records = self.run(cypher).single()
        if records is None:
            return None
        cypher = f'match (:{node_label} {{name: "{node_name}"}}) -[:{relationship}]-(node) return node.name AS name
        records = self.run(cypher).values()
        if records is None:
            return None
        return records['name']

    def create_relationship(self, into_node_label: str, into_node_name: str, out_node_label: str, out_node_name: str, relationship: str):
        '''
        create the relationship between two node with stated. i.e. outer_node --relationship--> inter_node
        :param into_node_label: the label of the node pointing to
        :param into_node_name: the name of the node pointing to
        :param out_node_label: the label of the node pointing out
        :param out_node_name: the name of the node pointing out
        :param relationship: the name of the relationship of these two nodes
        '''
        cypher1 = f'match (n:{into_node_label}) where n.name="{into_node_name}" return n'
        cypher2 = f'match (n:{out_node_label}) where n.name="{out_node_name}" return n'
        record1 = self.run(cypher1).single()
        record2 = self.run(cypher2).single()
        if record1 is None or record2 is None:
            return None
        cypher = f'''match (into_node:{into_node_label} {{name: "{into_node_name}"}}), (out_node:{out_node_label} {{name: "{out_node_name}"}}) create (out_node)-[:{relationship}]->(into_node)'''
        self.run(cypher)

    def drop_index(self, index_name):
        '''
        drop the index with the given name
        :param index_name: the name of the index
        :return:
        '''
        cypher = f'DROP INDEX {index_name}'
        self.run(cypher)

def neo4j_driver(try_connect=True)->Optional[Neo4jDriver]:
    '''return the singleton neo4j driver'''
    if _driver is None:
        if try_connect:
            try:
                connect_to_neo4j()
            except Exception as e:
                raise RuntimeError('Neo4j driver is not initialized. Also, auto connection is failed. Please call "connect_to_neo4j" first.') from e
    return _driver
def new_neo4j_session():
    '''
    Create a new session for neo4j driver. You must connect to neo4j first.
    '''
    driver = neo4j_driver()
    return driver.session()
def neo4j_session()->Optional[Neo4jSession]:
    '''
    return the singleton neo4j session. You must connect to neo4j first, otherwise it will be None.
    '''
    return _single_session

class Neo4jConnectMethod(CrossModuleEnum):
    BOLT = ('bolt', 7687) # name, default port
    HTTP = ('http', 7474)
    HTTPS = ('https', 7473)

DEFAULT_NEO4J_USERNAME = os.getenv('NEO4J_USER', 'neo4j')
'''You can set this value in environment variable NEO4J_USER. If not set, the default value is neo4j.'''
DEFAULT_NEO4J_PASSWORD = os.getenv('NEO4J_PW', None)
'''You can set this value in environment variable NEO4J_PW. If not set, the default value is None(Means no Authentication).'''

def connect_to_neo4j(username:str=DEFAULT_NEO4J_USERNAME, password:str=DEFAULT_NEO4J_PASSWORD, url:str='localhost', port:int=None, method=Neo4jConnectMethod.BOLT)->Neo4jDriver:
    '''
    if already connected, return the existing driver directly. If username or pw is None, it will try to connect to neo4j without authentication.
    :param username: the username of neo4j
    :param password: the password of neo4j
    '''
    global _driver, _single_session
    if _driver is not None:
        return _driver
    if port is None:
        port = method.value[1]
    uri = f'{method.value[0]}://{url}:{port}'
    if username is None or password is None:
        _driver = GraphDatabase.driver(uri)
    else:
        _driver = GraphDatabase.driver(uri, auth=(username, password))
    _driver.verify_connectivity()
    _driver = Neo4jDriver.cast(_driver)
    _single_session = _driver.session()
    return _driver