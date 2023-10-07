from data_struct.value import Value
from data_struct.atom import Atom
from typing import Union
from collections import deque


class Node:
    def __init__(self, promptedobj: Union[Value,Atom], children: list[Node,...] = []):
        self.promptedobj = promptedobj
        self.child: list[Node,...] = children

    def insert_child(self, children):
        if isinstance(children, list):
            self.child.extend(children)
        else:
            if children is not None:
                self.child.append(children)


class Tree:
    def __init__(self, head: Node):
        self.head = head

    def run_the_tree(self):
        self.post_order_travel(self.head)

    def post_order_travel(self, current: Node):
        if len(current.child) == 0:
            current.promptedobj.run()

        else:
            for child in current.child:
                self.post_order_travel(child)

            current.promptedobj.run()




