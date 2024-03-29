# Amirreza Azari 99101087
# Ghazal Tahan 99106374
from enum import Enum

whitespaces = [' ', '\n', '\t', '\r', '\v', '\f']
keywords = ["if", "else", 'void', 'int', 'while', "break", "return"]
symbols = [';', ':', ',', '[', ']', '(', ')', '{', '}', '+', '-', '*', '=', '<', '==', '/']


class States(Enum):
    ID = 0
    NUM = 1
    START = 2
    SYMBOL = 3
    COMMENT = 4
    WHITESPACE = 5


class Scanner:
    def __init__(self, string):
        self.string = string
        self.position = 0
        self.line_no = 1

    def id_state(self):
        pt = self.position
        while pt < len(self.string):
            if (self.string[pt] in symbols):
                break
            elif (self.string[pt] in whitespaces):
                break
            elif not self.string[pt].isalnum():
                prev_position = self.position
                self.position = pt + 1
                return ("Error", "Invalid input", self.line_no, f'{self.string[prev_position:pt + 1]}')
            pt += 1

        word = self.string[self.position:pt]
        self.position = pt
        self.state = States.START

        if word in keywords:
            return ("Token", "KEYWORD", word, self.line_no)
        elif word.isidentifier():
            return ("Token", "ID", word, self.line_no)
        else:
            return ("Error", "Invalid word", self.line_no, f'{word}')

    def whitespace_state(self):
        pt = self.position
        # just checking \n in whitespace for updating line number
        while pt < len(self.string) and self.string[pt] in whitespaces:
            if self.string[pt] == '\n':
                self.line_no += 1
            pt += 1
        prev_position = self.position
        self.position = pt
        self.state = States.START
        return ("Token", "WHITESPACE", self.string[prev_position:pt], self.line_no)

    def symbol_state(self):
        if self.string[self.position] in symbols:
            if self.string[self.position] == '*':  # in DFA, after * if we have /, we have error of unmatched
                if self.string[self.position + 1] == '/':
                    self.state = States.START
                    self.position += 2
                    return ("Error", "Unmatched comment", self.line_no,
                            f'{self.string[self.position - 2:self.position]}')
                elif not self.validating(
                        self.string[self.position + 1]):  # after * if we do not have valid char, invalid input
                    self.position += 2
                    return ("Error", "Invalid input", self.line_no, f'{self.string[self.position - 2: self.position]}')

            if self.string[self.position] == '=':  # after = we can have another = or a valid char. Otherwise error.
                if self.string[self.position + 1] == '=':
                    self.state = States.START
                    self.position += 2
                    return ("Token", "SYMBOL", self.string[self.position - 2:self.position], self.line_no)
                elif self.validating(self.string[self.position + 1]):
                    self.position += 1
                    return ("Token", "SYMBOL", self.string[self.position - 1], self.line_no)
                else:
                    self.position += 2
                    return ("Error", "Invalid input", self.line_no, f'{self.string[self.position - 2: self.position]}')

            # if it is not * or =, just return it as a symbol
            self.position += 1
            return ("Token", "SYMBOL", self.string[self.position - 1], self.line_no)

    def num_state(self):
        pt = self.position  # current position
        while pt < len(self.string):
            if (self.string[pt] in symbols) or (self.string[pt] in whitespaces):
                break  # end of numbers
            elif not self.string[pt].isdigit():  # illegal input
                prev_position = self.position
                self.position = pt + 1
                return ("Error", "Invalid number", self.line_no, f'{self.string[prev_position:pt + 1]}')
            pt += 1

        tokenized_number = self.string[self.position:pt]  # all digits
        self.position = pt
        if tokenized_number.isdecimal():
            return ("Token", "NUM", tokenized_number, self.line_no)
        else:
            return ("Error", "Invalid number", self.line_no, f'{tokenized_number}')

    def comment_state(self):
        pt = self.position
        line = self.line_no
        while pt < len(self.string):
            # New line
            if self.string[pt] == '\n':
                self.line_no += 1
            # If we don not have *, go to next. Else, check next.
            if self.string[pt] != '*':
                pt += 1
            elif pt < len(self.string) - 1 and self.string[pt + 1] == '/':  # */ and end of a comment
                self.state = States.START
                prev_position = self.position
                self.position = pt + 2  # Jump this lookahead
                return (
                    "Token", "COMMENT", self.string[prev_position:pt - 1], line)  # Return whole comment
            else:
                pt += 1
        # If a comment remains open when the end of the input file is encountered,
        # record this error with
        # just the message 'Unclosed comment'. In this type of errors, a long string (i.e., the unclosed
        # comment) might be thrown away by the scanner.
        # However, it is sufficient to print at most the
        # first seven characters of the unclosed comment with three dots
        if pt >= len(self.string):
            if pt - self.position > 6:
                comment = self.string[self.position - 2: self.position + 5] + '...'
            else:
                comment = self.string[self.position:pt - 2]
            self.state = States.START
            self.position = pt
            return ("Error", "Unclosed comment", line, f'{comment}')

    def get_next_token(self):
        self.state = States.START
        if self.position >= len(self.string):
            return ("EOF", "EOF", 'EOF', self.line_no)
        if self.state == States.START:
            # /
            if self.string[self.position] == '/':
                # / *
                if self.string[self.position + 1] == '*':
                    self.position += 2
                    self.state = States.COMMENT
                # / any valid char
                elif self.validating(self.string[self.position + 1]):
                    self.state = States.SYMBOL
                # / other chars (invalid)
                else:
                    self.position += 2
                    return ("Error", "Invalid input", self.line_no, self.string[self.position])
            # alphabet
            elif self.string[self.position].isalpha():
                self.state = States.ID
            # digit
            elif self.string[self.position].isdigit():
                self.state = States.NUM
            # symbols
            elif self.string[self.position] in symbols:
                self.state = States.SYMBOL
            # white space
            elif self.string[self.position] in whitespaces:
                self.state = States.WHITESPACE
            # other chars (invalid)
            else:
                self.position += 1
                return ("Error", "Invalid input", self.line_no, self.string[self.position - 1])
        if self.state == States.COMMENT:
            return (self.comment_state())
        elif self.state == States.SYMBOL:
            return (self.symbol_state())
        elif self.state == States.ID:
            return (self.id_state())
        elif self.state == States.WHITESPACE:
            return (self.whitespace_state())
        else:
            return (self.num_state())

    def validating(self, char: str):
        return char in whitespaces or char in symbols or char.isalnum()


class output:
    def __init__(self, errors, tokens, table):
        self.errors = errors
        self.tokens = tokens
        self.table = table

    def lexical_file(self):
        with open("lexical_errors.txt", "w") as f:
            cl = None
            for error in self.errors:
                if error[2] != cl:
                    if cl is not None:
                        f.write("\n")
                    cl = error[2]
                    f.write(str(cl) + "." + "\t")
                f.write("(" + error[-1] + ", " + error[1] + ") ")
            if len(self.errors) == 0:
                f.write("There is no lexical error.")
            else:
                f.write("\n")

    def symbol_file(self):
        line_number = 1
        with open("symbol_table.txt", "w") as f:
            for keyword in keywords:
                f.write(str(line_number) + "." + "\t" + keyword + "\n")
                line_number += 1

            for index, id in enumerate(set(self.table)):
                if index != len(self.table) - 1:
                    f.write(str(line_number) + "." + "\t" + id + "\n")
                else:
                    f.write(str(line_number) + "." + "\t" + id)
                line_number += 1

    def token_file(self):
        with open("tokens.txt", "w") as f:
            cl = None
            for token in self.tokens:
                if token[1] == "WHITESPACE" or token[1] == "COMMENT":
                    continue
                if token[3] != cl:
                    if cl is not None:
                        f.write("\n")
                    cl = token[3]
                    f.write(str(cl) + "." + "\t")
                f.write("(" + token[1] + ", " + token[2] + ") ")


def main():
    f = open('input.txt', 'r')
    scanner = Scanner(f.read())
    f.close()
    tokens = []
    errors = []
    table = []
    while True:
        token = scanner.get_next_token()
        if token[0] == "EOF":
            break
        if token[0] == "Error":
            errors.append(token)
            continue
        if token[0] == "Token":
            tokens.append(token)
        if token[0] == "Token" and token[1] == "ID":
            table.append(token[2])
    files = output(errors, tokens, table)
    files.lexical_file()
    files.symbol_file()
    files.token_file()


if __name__ == '__main__':
    main()
