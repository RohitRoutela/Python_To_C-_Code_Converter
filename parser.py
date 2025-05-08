from lexer import Token, tokenize
from ast_nodes import *

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current_token(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def eat(self, token_type):
        while self.current_token() and self.current_token().type == "COMMENT":
            self.pos += 1
        if self.current_token() and self.current_token().type == token_type:
            self.pos += 1
        else:
            raise SyntaxError(f"Expected {token_type} but found {self.current_token()}")

    def parse(self):
        return self.program()

    def program(self):
        statements = []
        while self.current_token():
            if self.current_token().type == "NEWLINE":
                self.eat("NEWLINE")
                continue
            statements.append(self.statement())
        return Program(statements)

    def block(self):
        statements = []
        while self.current_token() and not (self.current_token().type == "KEYWORD" and self.current_token().value in ["else"]):
            if self.current_token().type == "NEWLINE":
                self.eat("NEWLINE")
                continue
            statements.append(self.statement())
        return statements

    def statement(self):
        token = self.current_token()

        if token.type == "IDENTIFIER":
            return self.assignment()

        elif token.type == "KEYWORD":
            keyword = token.value
            if keyword == "if":
                return self.if_statement()
            elif keyword == "while":
                return self.while_statement()
            elif keyword == "for":
                return self.for_statement()
            elif keyword == "print":
                return self.print_statement()
            elif keyword == "def":
                return self.function_definition()
            elif keyword == "return":
                return self.return_statement()

        raise SyntaxError(f"Unexpected token: {token}")

    def assignment(self):
        identifier = self.current_token().value
        self.eat("IDENTIFIER")
        self.eat("OPERATOR")  # '=' expected
        expression = self.expression()
        return AssignmentNode(identifier, expression)

    def if_statement(self):
        self.eat("KEYWORD")  # if
        condition = self.expression()
        self.eat("SYMBOL")  # :
        if self.current_token().type == "NEWLINE":
            self.eat("NEWLINE")
        true_branch = self.block()
        false_branch = None
        if self.current_token() and self.current_token().type == "KEYWORD" and self.current_token().value == "else":
            self.eat("KEYWORD")
            self.eat("SYMBOL")  # :
            if self.current_token().type == "NEWLINE":
                self.eat("NEWLINE")
            false_branch = self.block()
        return IfNode(condition, true_branch, false_branch)

    def while_statement(self):
        self.eat("KEYWORD")  # while
        condition = self.expression()
        self.eat("SYMBOL")  # :
        if self.current_token().type == "NEWLINE":
            self.eat("NEWLINE")
        body = self.block()
        return WhileNode(condition, body)

    def for_statement(self):
        self.eat("KEYWORD")  # for
        variable = self.current_token().value
        self.eat("IDENTIFIER")
        self.eat("KEYWORD")  # in

        if self.current_token().type == "IDENTIFIER" and self.current_token().value == "range":
            iterable = self.range_expression()
        else:
            iterable = self.expression()

        self.eat("SYMBOL")  # :
        if self.current_token().type == "NEWLINE":
            self.eat("NEWLINE")
        body = self.block()
        return ForNode(variable, iterable, body)

    def range_expression(self):
        self.eat("IDENTIFIER")  # range
        self.eat("SYMBOL")  # (
        argument = self.expression()
        self.eat("SYMBOL")  # )
        return FunctionCallNode("range", [argument])

    def function_definition(self):
        self.eat("KEYWORD")  # def
        name = self.current_token().value
        self.eat("IDENTIFIER")
        self.eat("SYMBOL")  # (
        parameters = []
        if self.current_token().type != "SYMBOL" or self.current_token().value != ")":
            while True:
                if self.current_token().type != "IDENTIFIER":
                    raise SyntaxError(f"Expected parameter name, got {self.current_token()}")
                parameters.append(self.current_token().value)
                self.eat("IDENTIFIER")
                if self.current_token().type == "SYMBOL" and self.current_token().value == ",":
                    self.eat("SYMBOL")
                elif self.current_token().type == "SYMBOL" and self.current_token().value == ")":
                    break
                else:
                    raise SyntaxError(f"Expected ',' or ')', got {self.current_token()}")
        self.eat("SYMBOL")  # )
        self.eat("SYMBOL")  # :
        if self.current_token().type == "NEWLINE":
            self.eat("NEWLINE")
        body = self.block()
        return FunctionDefNode(name, parameters, body)

    def return_statement(self):
        self.eat("KEYWORD")  # return
        if self.current_token() and self.current_token().type != "NEWLINE":
            value = self.expression()
        else:
            value = None
        return ReturnNode(value)

    def print_statement(self):
        self.eat("KEYWORD")  # print
        self.eat("SYMBOL")  # (
        expression = self.expression()
        self.eat("SYMBOL")  # )
        return PrintNode(expression)

    def expression(self):
        left = self.term()
        while self.current_token() and self.current_token().type == "OPERATOR" and self.current_token().value in ('+', '-', '<', '>', '==', '!=', '<=', '>='):
            operator = self.current_token().value
            self.eat("OPERATOR")
            right = self.term()
            left = BinaryOpNode(left, operator, right)
        return left

    def term(self):
        left = self.factor()
        while self.current_token() and self.current_token().type == "OPERATOR" and self.current_token().value in ('*', '/'):
            operator = self.current_token().value
            self.eat("OPERATOR")
            right = self.factor()
            left = BinaryOpNode(left, operator, right)
        return left

    def factor(self):
        token = self.current_token()
        if token.type == "NUMBER":
            value = float(token.value) if '.' in token.value else int(token.value)
            self.eat("NUMBER")
            return NumberNode(value)
        elif token.type == "STRING":
            value = token.value.strip('"')
            self.eat("STRING")
            return StringNode(value)
        elif token.type == "IDENTIFIER":
            name = token.value
            self.eat("IDENTIFIER")
            return IdentifierNode(name)
        elif token.type == "SYMBOL" and token.value == "(":
            self.eat("SYMBOL")
            expr = self.expression()
            self.eat("SYMBOL")
            return expr
        else:
            raise SyntaxError(f"Unexpected token: {token}")
