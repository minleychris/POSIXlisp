#!/usr/bin/python

import sys
import getopt
import re

from parsimonious.grammar import Grammar



class List:
    def __init__(self, head = None, rest = None):
        self.head = head
        self.rest = rest

    def __iter__(self):
        class ListIterator:
            def __init__(self, lst):
                self.lst = lst
            def next(self):
                if self.lst == None:
                    raise StopIteration
                head = self.lst.head
                self.lst = self.lst.rest
                return head

        return ListIterator(self)

    def innerStr(self):
        if self.rest == None:
            return self.head.__str__()
        return self.head.__str__() + " " + self.rest.innerStr()

    def __str__(self):
        return "(" + self.innerStr() + ")"

class Environment:
    def __init__(self, parent = None):
        self.parent = parent
        self.env = {}

    def assign(self, name, value):
        self.env[name] = value

    def resolve(self, name):
        if self.env.has_key(name):
            return self.env[name]

        if self.parent != None:
            return self.parent.resolve(name)

        return None

    def __str__(self):
        if self.parent == None:
            return self.env.__str__() + " => None"
        return self.env.__str__() + " => " + self.parent.__str__()



def COND(args, env):
    if args.head == None:
        return None;

    if eval(args.head):
        return eval(args.rest.head, env)

    return COND(args.rest.rest)

def QUOTE(args, env):
    return args.head

def DEF(args, env):
    name = args.head
    value = eval(args.rest.head, env)
    env.assign(name, value);
    return name

def FN(args, env):
    argz = args.head
    body = args.rest.head

    class Func:
        def __init__(self, argz, body):
            self.argz = argz
            self.body = body

        def __call__(self, *args):
            new_env = Environment(env)
            i=0
            for arg in argz:
                new_env.assign(arg, args[i])
                i = i+1

            return eval(body, new_env)

    return Func(argz, body)



def CONS(*args):
    return List(args[0], args[1])

def FIRST(*args):
    return args[0].head

def REST(*args):
    return args[0].rest

def PLUS(*args):
    return sum(args)

def EQUALS(*args):
    return reduce(lambda x,y: x==y, args)



def is_special(func):
    return func == COND or func == QUOTE or func == DEF or func == FN



def eval_s_exp(s_exp, env):
    rest = s_exp.rest
    func = eval(s_exp.head, env)

    if is_special(func):
        return func(rest, env)
    else:
        if rest == None:
            return func()
        evaled = map(lambda r: eval(r, env), rest)
        return func(*evaled)

def eval(exp, env):
    if isinstance(exp, int):
        return exp
    if isinstance(exp, str):
        return env.resolve(exp)
    if isinstance(exp, List):
        return eval_s_exp(exp, env)





grammar = Grammar(
    """
    exp = number / symbol / s_exp
    number = ~"[0-9]+"
    symbol = ~"[+=a-zA-Z][+=a-zA-Z0-9]*"
    s_exp  = "(" (exp space)* exp ")"
    space = " "
    """)

def reduce_exp_tree(exp):
    """
    Trim the tree to get rid of unwanted nodes.  Ideally we wouldn't create them in the first place, though...
    """

    if exp.expr_name == "" and len(exp.children) == 0:
        return None

    children = []

    for node in exp.children:
        child = reduce_exp_tree(node)
        if child:
            if child['type'] != "" and child['type'] != "space" and child['type'] != "exp":
                children.append(child)
            else:
                children.extend(child['children'])

    return {'type': exp.expr_name,
            'children': children,
            'text': exp.text}

def tree_to_list(tree):
    """
    Put the tree into the internal list structure.  Ideally we'd load it into this in the first place, though...
    """

    lst = None

    for node in reversed(tree["children"]):
        if node["type"] == "s_exp":
            lst = List(tree_to_list(node), lst)
        elif node["type"] == "number":
            lst = List(int(node["text"]), lst)
        elif node["type"] == "symbol":
            lst = List(node["text"], lst)

    if tree["type"] == "exp":
        return lst.head
    else:
        return lst;


def main(argv=None):
    env = Environment()
    env.env = {"cond": COND,
               "quote": QUOTE,
               "def": DEF,
               "fn": FN,
               "+": PLUS,
               "=": EQUALS,
               "cons": CONS,
               "first": FIRST,
               "rest": REST}

    while True:
        line = raw_input("=> ")
        reduced_tree = reduce_exp_tree(grammar.parse(line))
        program_list = tree_to_list(reduced_tree)
        print(eval(program_list, env))

if __name__ == "__main__":
    sys.exit(main())
