from data_struct.value import Value
from data_struct.atom import Atom
from typing import Union
from collections import deque


class Node:
    def __init__(self, promptedobj: Union[Value,Atom], children: list = []):
        self.promptedobj = promptedobj
        self.child: list[Node, ...] = list(children)

    def insert_child(self, children):
        if isinstance(children, list):
            self.child.extend(children)
        else:
            if children is not None:
                self.child.append(children)
        # print(self.child)

    def child_print(self):
        return [child.promptedobj for child in self.child]


class Tree:
    def __init__(self, question, head: Node):
        self.head = head
        self.question = question

    def run_the_tree(self):
        return self.post_order_travel(self.head)

    def post_order_travel(self, current: Node):
        if len(current.child) == 0:
            value_to_be_stored = current.promptedobj.ask_for_input(self.question, current.promptedobj.prompt, current.promptedobj.example_prompt)
            current.promptedobj.input(value_to_be_stored)
            print(value_to_be_stored)
        else:
            if current.promptedobj.BASE_CLS_NAME == 'Atom':
                for child in current.child:
                    self.post_order_travel(child)
                return current.promptedobj.call()
            if current.promptedobj.BASE_CLS_NAME == 'Value':
                #assume child of value only have one
                current.promptedobj.input(self.post_order_travel(current.child[0]))
                if current == self.head:
                    return current.promptedobj.value()



