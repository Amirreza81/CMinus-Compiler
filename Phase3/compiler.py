# Amirreza Azari 99101087, Ghazal Tahan 99106374

import json
import anytree
from scanner import *
from codegen import CodeGenerator

Terminals = [';', '[', ']', '(', ')', ',', '{', '}', '=', '<', '==', '+', '-', '*', '$', '/',
             'return', 'NUM', 'ID', 'int', 'void', 'break', 'if', 'else', 'while']

file = open('./resources/First.json')
firsts = json.load(file)
file.close()

file = open('./resources/Follow.json')
follows = json.load(file)
file.close()

file = open('./resources/Grammar.json')
grammars = json.load(file)
file.close()


def new_token(scanner):
    global line_number
    token = scanner.get_next_token()
    while token.type == TokenType.COMMENT or token.type == TokenType.WHITESPACE:
        token = scanner.get_next_token()
    if token.type == TokenType.EOF:
        token.string = "$"
    return token


def create_ll1_table():
    ll1_table = {}
    for key in grammars:
        ll1_table[key] = {}
        for term in Terminals:
            ll1_table[key][term] = ""

    for key in grammars:
        rhs = " "
        for val in grammars[key]:
            flag = False
            q = val[0]
            if "#" in q:
                flag = True
                q = val[1]
            if q in Terminals:
                ll1_table[key][q] = rhs.join(val)
                continue
            if q == "EPSILON":
                for fol in follows[key]:
                    if not flag:
                        ll1_table[key][fol] = "epsilon"
                    else:
                        ll1_table[key][fol] = val[0] + " epsilon"
                continue
            for first in firsts[q]:
                if first == "EPSILON":
                    if len(val) == 1:
                        for fol in follows[key]:
                            ll1_table[key][fol] = rhs.join(val)
                    else:
                        for mio in val:
                            flag = False
                            for first in firsts[mio]:
                                if first != "EPSILON":
                                    ll1_table[key][first] = rhs.join(val)
                                else:
                                    flag = True
                            if not flag:
                                break
                        if flag:
                            for fol in follows[key]:
                                ll1_table[key][fol] = rhs.join(val)
                    continue

                ll1_table[key][first] = rhs.join(val)

    for key in grammars:
        for follow in follows[key]:
            if ll1_table[key][follow] == "":
                ll1_table[key][follow] = "synch"

    return ll1_table

def save_semantic_errors():
    with open('semantic_errors.txt', 'w') as f:
        for idx in semantic_errors:
            f.write(f'{idx}\n')
    with open('output.txt', 'w') as f:
        f.write('The code has not been generated.')


def save_program(code_gen):
    with open('output.txt', 'w') as f:
        for idx in sorted(code_gen.PB.keys()):
            f.write(f'{idx}\t{code_gen.PB[idx]}\n')

def main():
    ll1_table = create_ll1_table()
    print(ll1_table)
    f = open('input.txt', 'r')
    scanner = Scanner(f.read())
    codegenerator = CodeGenerator()

    path = anytree.Node('Program')
    flag_next_token = False
    eof = anytree.Node('$')
    syntax_errors = []
    flag_EOF = False
    stack = [eof, path]

    token = new_token(scanner)

    while stack:
        top = stack[-1]
        print(top.name)
        if flag_next_token:
            token = new_token(scanner)
            flag_next_token = False
        if token.type == TokenType.SYMBOL or token.type == TokenType.KEYWORD:
            current_token = token.lexeme
        else:
            current_token = token.type.value
        if token.type == TokenType.EOF:
            current_token = "$"

        if top.name.startswith('#'):
            mio = token.line_no, token.type.value, token.lexeme
            codegenerator.call_routine(top.name, mio)
            stack.pop()
            continue

        if top == "$" and current_token == "$":
            eof.parent = path
            break
        if top.name not in Terminals:
            if top.name == "epsilon":
                stack.pop()
                continue
            rhs = ll1_table[top.name][current_token]
            if rhs == "" and current_token != "$":
                flag_next_token = True
                syntax_errors.append("#" + str(token.line_no) + ": syntax error, illegal " + current_token + "\n")
            elif rhs == "" and current_token == "$":
                syntax_errors.append("#" + str(token.line_no) + " : syntax error, Unexpected EOF\n")
                flag_EOF = True
                break
            elif rhs == "synch":
                non_term_stack = stack.pop()
                non_term_stack.parent = None
                syntax_errors.append("#" + str(token.line_no) + ": syntax error, missing " + top.name + "\n")
            elif rhs == "epsilon":
                stack.pop()
                anytree.Node("epsilon", top)
            else:
                non_term_stack = stack.pop()
                rhs_nodes = rhs.split(" ")
                ordered_list = []
                for node in rhs_nodes:
                    ordered_list.append(anytree.Node(node, non_term_stack))
                stack += ordered_list[::-1]
        elif top.name == current_token and current_token != '$':
            term_node = stack.pop()
            flag_next_token = True
            term_node.name = "(" + token.type.value + ", " + token.lexeme + ") "
        elif top.name in Terminals:
            term_node = stack.pop()
            if top.name != "$":
                syntax_errors.append("#" + str(token.line_no) + ": syntax error, missing " + top.name + "\n")
                term_node.parent = None
            else:
                eof.parent = path

    if flag_EOF:
        for s in stack:
            s.parent = None

    if len(codegenerator.semantic_errors) > 0:
        save_semantic_errors()
    else:
        save_program(codegenerator)


if __name__ == '__main__':
    main()
