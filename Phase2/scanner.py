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


class TokenType(Enum):
    ID = 'ID'
    EOF = 'EOF'
    NUM = 'NUM'
    SYMBOL = 'SYMBOL'
    COMMENT = 'COMMENT'
    KEYWORD = 'KEYWORD'
    WHITESPACE = 'WHITESPACE'


class Token:
    def __init__(self, type: TokenType, lexeme: str, line_no):
        self.type = type
        self.lexeme = lexeme
        self.line_no = line_no

    def __str__(self):
        return f'({self.type.value}, {self.lexeme})'

    def __ge__(self, other):
        return self.line_no >= other.line_no

    def __gt__(self, other):
        return self.line_no > other.line_no


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
            return Token(TokenType.KEYWORD, word, self.line_no)
        elif word.isidentifier():
            return Token(TokenType.ID, word, self.line_no)
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
        return Token(TokenType.WHITESPACE, self.string[prev_position:pt], self.line_no)

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
                    return Token(TokenType.SYMBOL, self.string[self.position - 2:self.position], self.line_no)
                elif self.validating(self.string[self.position + 1]):
                    self.position += 1
                    return Token(TokenType.SYMBOL, self.string[self.position - 1], self.line_no)
                else:
                    self.position += 2
                    return ("Error", "Invalid input", self.line_no, f'{self.string[self.position - 2: self.position]}')

            # if it is not * or =, just return it as a symbol
            self.position += 1
            return Token(TokenType.SYMBOL, self.string[self.position - 1], self.line_no)

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
            return Token(TokenType.NUM, tokenized_number, self.line_no)
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
                return Token(TokenType.COMMENT, self.string[prev_position:pt - 1], line)  # Return whole comment
            else:
                pt += 1
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
            return Token(TokenType.EOF, '$', self.line_no)
        if self.state == States.START:
            # /
            if self.string[self.position] == '/':
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

