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
        self.head = head if head is not None else None
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
                    if self._cycle_detection(child, visited, recstack):
                        return True
                elif not recstack[child]:
                    return True
        recstack[node] = False
        return False

    def post_order_travel(self, stack: list, visited):
        while len(stack)>0:
            node = stack[len(stack)-1]
            if not visited.get(node, False):
                visited[node] = True
                for child in node.children:
                    if not visited.get(child, False):
                        visited[child] = False
                        stack.append(child)

            else:
                stack.pop()
                if node.promptedobj.BASE_CLS_NAME == 'Value':
                    if len(node.children) == 0:
                        value_to_be_stored = node.promptedobj.ask_for_input(self.question, node.promptedobj.prompt, node.promptedobj.example_prompt)
                        if value_to_be_stored is None:
                            return node
                        print(f"final_input{node.promptedobj}: ", node.promptedobj.input(value_to_be_stored))
                    if self.head == node:
                        if node.promptedobj.value() == {}:
                            return node
                        return node.promptedobj.value()
                else:
                    try:
                        node.promptedobj.call(input = node.children, output = node.parents)
                    except:
                        return node

    def print_post_order(self):
        pass






