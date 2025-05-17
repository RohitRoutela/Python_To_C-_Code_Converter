from lexer import Token, tokenize
from ast_nodes import *

class Parser:
    def __init__(self, tokens):
        # Initialize parser with token list
        self.tokens = tokens
        self.pos = 0

    def current_token(self):
        # Get the current token or None if at end
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def eat(self, token_type=None):
        # Consume current token, optionally validating its type
        token = self.current_token()
        if token is None:
            raise SyntaxError(f"Unexpected end of input")
        if token_type is not None and token.type != token_type:
            line_info = f" at line {token.line}" if hasattr(token, 'line') else ""
            raise SyntaxError(f"Expected {token_type} but found {token.type}{line_info}")
        self.pos += 1
        return token

    def parse(self):
        # Start the parsing process
        return self.program()

    def program(self):
        # Parse the entire program
        statements = []
        while self.current_token():
            # Skip whitespace tokens at program level
            if self.current_token().type in ['NEWLINE', 'INDENT', 'DEDENT']:
                self.eat()
                continue
                
            statements.append(self.statement())
        return Program(statements)

    def block(self):
        # Parse an indented block of code
        statements = []
        
        # Handle indented blocks
        if self.current_token() and self.current_token().type == 'INDENT':
            self.eat('INDENT')
            
            # Process statements until DEDENT
            while self.current_token() and self.current_token().type != 'DEDENT':
                if self.current_token().type == 'NEWLINE':
                    self.eat()
                    continue
                    
                statements.append(self.statement())
                
            # End of indented block
            if self.current_token() and self.current_token().type == 'DEDENT':
                self.eat('DEDENT')
        else:
            # Single statement block without indentation
            statements.append(self.statement())
            
        return statements

    def statement(self):
        # Parse a single statement
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
        # Parse variable assignment
        identifier = self.current_token().value
        self.eat("IDENTIFIER")
        self.eat("OPERATOR")  # Expect '='
        expression = self.expression()
        return AssignmentNode(identifier, expression)

    def if_statement(self):
        # Parse if statement with optional else block
        self.eat("KEYWORD")  # Consume 'if'
        condition = self.expression()
        self.eat("SYMBOL")  # Expect ':'
        
        # Skip newlines before block
        while self.current_token() and self.current_token().type == 'NEWLINE':
            self.eat()
            
        true_branch = self.block()
        false_branch = None
        
        # Check for else clause
        if self.current_token() and self.current_token().type == "KEYWORD" and self.current_token().value == "else":
            self.eat("KEYWORD")
            self.eat("SYMBOL")  # Expect ':'
            
            # Skip newlines before block
            while self.current_token() and self.current_token().type == 'NEWLINE':
                self.eat()
                
            false_branch = self.block()
            
        return IfNode(condition, true_branch, false_branch)

    def while_statement(self):
        # Parse while loop
        self.eat("KEYWORD")  # Consume 'while'
        condition = self.expression()
        self.eat("SYMBOL")  # Expect ':'
        
        # Skip newlines before block
        while self.current_token() and self.current_token().type == 'NEWLINE':
            self.eat()
            
        body = self.block()
        return WhileNode(condition, body)

    def for_statement(self):
        # Parse for loop with iterable
        self.eat("KEYWORD")  # Consume 'for'
        variable = self.current_token().value
        self.eat("IDENTIFIER")
        self.eat("KEYWORD")  # Expect 'in'

        # Special handling for range expressions
        if self.current_token().type == "IDENTIFIER" and self.current_token().value == "range":
            iterable = self.range_expression()
        else:
            iterable = self.expression()

        self.eat("SYMBOL")  # Expect ':'
        
        # Skip newlines before block
        while self.current_token() and self.current_token().type == 'NEWLINE':
            self.eat()
            
        body = self.block()
        return ForNode(variable, iterable, body)

    def range_expression(self):
        # Parse range function call for loops
        self.eat("IDENTIFIER")  # Consume 'range'
        self.eat("SYMBOL")  # Expect '('
        argument = self.expression()
        self.eat("SYMBOL")  # Expect ')'
        return FunctionCallNode("range", [argument])

    def function_definition(self):
        # Parse function definition
        self.eat("KEYWORD")  # Consume 'def'
        name = self.current_token().value
        self.eat("IDENTIFIER")
        self.eat("SYMBOL")  # Expect '('
        
        # Parse parameter list
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
        self.eat("SYMBOL")  # Expect ')'
        self.eat("SYMBOL")  # Expect ':'
        
        # Skip newlines before block
        while self.current_token() and self.current_token().type == 'NEWLINE':
            self.eat()
            
        body = self.block()
        return FunctionDefNode(name, parameters, body)

    def return_statement(self):
        # Parse return statement
        self.eat("KEYWORD")  # Consume 'return'
        
        # Optional return value
        if self.current_token() and self.current_token().type != "NEWLINE":
            value = self.expression()
        else:
            value = None
        return ReturnNode(value)

    def print_statement(self):
        # Parse print statement
        self.eat("KEYWORD")  # Consume 'print'
        self.eat("SYMBOL")  # Expect '('
        expression = self.expression()
        self.eat("SYMBOL")  # Expect ')'
        return PrintNode(expression)

    def expression(self):
        # Parse expressions with lowest precedence operators (comparison, addition/subtraction)
        left = self.term()
        while self.current_token() and self.current_token().type == "OPERATOR" and self.current_token().value in ('+', '-', '<', '>', '==', '!=', '<=', '>='):
            operator = self.current_token().value
            self.eat("OPERATOR")
            right = self.term()
            left = BinaryOpNode(left, operator, right)
        return left

    def term(self):
        # Parse terms with medium precedence operators (multiplication/division)
        left = self.factor()
        while self.current_token() and self.current_token().type == "OPERATOR" and self.current_token().value in ('*', '/'):
            operator = self.current_token().value
            self.eat("OPERATOR")
            right = self.factor()
            left = BinaryOpNode(left, operator, right)
        return left

    def factor(self):
        # Parse factors (highest precedence elements)
        token = self.current_token()
        
        # Numeric literals
        if token.type == "NUMBER":
            value = token.value 
            self.eat("NUMBER")
            return NumberNode(value)
            
        # String literals
        elif token.type == "STRING":
            value = token.value
            self.eat("STRING")
            return StringNode(value)
            
        # Variables and function calls
        elif token.type == "IDENTIFIER":
            name = token.value
            self.eat("IDENTIFIER")
            
            # Handle function calls
            if self.current_token() and self.current_token().type == "SYMBOL" and self.current_token().value == "(":
                self.eat("SYMBOL")  # Expect '('
                args = []
                
                # Parse arguments if any
                if self.current_token().type != "SYMBOL" or self.current_token().value != ")":
                    args.append(self.expression())
                    
                    while self.current_token().type == "SYMBOL" and self.current_token().value == ",":
                        self.eat("SYMBOL")  # Expect ','
                        args.append(self.expression())
                        
                self.eat("SYMBOL")  # Expect ')'
                return FunctionCallNode(name, args)
            
            # Simple variable reference
            return IdentifierNode(name)
            
        # Parenthesized expressions
        elif token.type == "SYMBOL" and token.value == "(":
            self.eat("SYMBOL")
            expr = self.expression()
            self.eat("SYMBOL")  # Expect ')'
            return expr
            
        # List literals
        elif token.type == "SYMBOL" and token.value == "[":
            self.eat("SYMBOL")  # Expect '['
            elements = []
            
            # Parse elements if any
            if self.current_token().type != "SYMBOL" or self.current_token().value != "]":
                elements.append(self.expression())
                
                while self.current_token().type == "SYMBOL" and self.current_token().value == ",":
                    self.eat("SYMBOL")  # Expect ','
                    
                    # Handle trailing comma
                    if self.current_token().type == "SYMBOL" and self.current_token().value == "]":
                        break
                        
                    elements.append(self.expression())
                    
            self.eat("SYMBOL")  # Expect ']'
            return ListNode(elements)
            
        else:
            raise SyntaxError(f"Unexpected token: {token}")
