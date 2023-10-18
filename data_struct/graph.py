from data_struct.value import Value
from data_struct.atom import Atom
from typing import Union


class Node:
    def __init__(self, promptedobj: Union[Value,Atom], children: list = [],parents: list = []):
        self.promptedobj = promptedobj
        self.children: list[Node, ...] = list(children)
        self.parents: list[Node, ...] = list(parents)

    def insert_children(self, children):
        if isinstance(children, list):
            self.children.extend(children)
        else:
            if children is not None:
                self.children.append(children)

    def insert_parent(self, parents):
        if isinstance(parents, list):
            self.parents.extend(parents)
        else:
            if parents is not None:
                self.parents.append(parents)

    def children_print(self):
        return [child.promptedobj for child in self.children]

    def parents_print(self):
        return [parent.promptedobj for parent in self.parents]

class Graph:
    def __init__(self, question, head: Node):
        self.head = head
        self.question = question


    def run_the_tree(self):
        if self.cycle_detection():
            return 'cycle error'
        stack = [self.head]
        visited = dict()
        visited[self.head] = False
        return self.post_order_travel(stack, visited)

    def cycle_detection(self):
        visited = dict()
        'visiting list'
        recstack = dict()
        'check cycle'
        visited[self.head] = False
        recstack[self.head] = False
        return self._cycle_detection(self.head, visited, recstack)

    def _cycle_detection(self, node, visited, recstack):
        if not visited[node]:
            visited[node] = True
            recstack[node] = True
            for child in node.children:
                if not visited.get(child, False):
                    visited[child] = False
                    if self._cycle_detection(node, child, visited, recstack):
                        return True
                elif not recstack[child]:
                    return True
        recstack[node] = False
        return False

    def post_order_travel(self, stack: list, visited):
        node = stack[len(stack)-1]
        if not visited.get(node, False):
            visited[node] = True
            for child in node.children:
                if not visited.get(child, False):
                    visited[child] = False
                    stack.append(child)

        else:
            stack.pop()
            if node.promptedobj == 'Value':
                if len(node.child) == 0:
                    value_to_be_stored = node.promptedobj.ask_for_input(self.question, node.promptedobj.prompt, node.promptedobj.example_prompt)
                    if value_to_be_stored is None:
                        return node.promptedobj
                    node.promptedobj.input(value_to_be_stored)
                elif self.head == node:
                    return self.head.value()
            else:
                try:
                    node.promptedobj.call()
                except:
                    return node.promptedobj





