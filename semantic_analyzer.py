from ast_nodes import (
    Program, AssignmentNode, IfNode, WhileNode, ForNode, PrintNode,
    BinaryOpNode, IdentifierNode, NumberNode, StringNode, FunctionCallNode,
    FunctionDefNode, ReturnNode, ListNode
)

class SemanticError(Exception):
    # Custom exception for semantic analysis errors
    pass

class ScopedSymbolTable:
    def __init__(self):
        # Initialize with a global scope
        self.scopes = [{}]

    def enter_scope(self):
        # Create a new scope for blocks
        self.scopes.append({})

    def exit_scope(self):
        # Remove the current scope when exiting a block
        self.scopes.pop()

    def declare(self, name, type_):
        # Add a variable to the current scope
        self.scopes[-1][name] = type_

    def lookup(self, name):
        # Find a variable in the current or parent scopes
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        raise SemanticError(f"Undeclared variable '{name}'")

class SemanticAnalyzer:
    def __init__(self):
        # Initialize the symbol table for tracking variables
        self.symbol_table = ScopedSymbolTable()

    def analyze(self, node):
        # Process lists of nodes
        if isinstance(node, list):
            for n in node:
                self.analyze(n)

        # Program node contains statements
        elif isinstance(node, Program):
            self.analyze(node.statements)

        # Variable assignment - record the variable type
        elif isinstance(node, AssignmentNode):
            expr_type = self.analyze(node.expression)
            self.symbol_table.declare(node.identifier, expr_type)

        # If statement - verify condition and analyze branches
        elif isinstance(node, IfNode):
            cond_type = self.analyze(node.condition)
            if cond_type != 'int':
                raise SemanticError(f"Condition in if must be an integer (0 or 1), got {cond_type}.")
            self.symbol_table.enter_scope()
            self.analyze(node.true_branch)
            self.symbol_table.exit_scope()
            if node.false_branch:
                self.symbol_table.enter_scope()
                self.analyze(node.false_branch)
                self.symbol_table.exit_scope()

        # While loop - verify condition and analyze body
        elif isinstance(node, WhileNode):
            cond_type = self.analyze(node.condition)
            if cond_type != 'int':
                raise SemanticError(f"Condition in while must be an integer (0 or 1), got {cond_type}.")
            self.symbol_table.enter_scope()
            self.analyze(node.body)
            self.symbol_table.exit_scope()

        # For loop - verify iterable and analyze body
        elif isinstance(node, ForNode):
            iterable_type = self.analyze(node.iterable)
            if iterable_type not in ['int', 'iterable']:
                raise SemanticError(f"For loops expect a valid iterable, got {iterable_type}.")
            self.symbol_table.enter_scope()
            self.symbol_table.declare(node.variable, 'int')
            self.analyze(node.body)
            self.symbol_table.exit_scope()

        # Print statement - just analyze the expression
        elif isinstance(node, PrintNode):
            self.analyze(node.expression)

        # Binary operation - verify operands have matching types
        elif isinstance(node, BinaryOpNode):
            left_type = self.analyze(node.left)
            right_type = self.analyze(node.right)
            if left_type != right_type:
                raise SemanticError(f"Type mismatch: {left_type} vs {right_type}")
            return left_type

        # Variable reference - lookup in symbol table
        elif isinstance(node, IdentifierNode):
            return self.symbol_table.lookup(node.name)

        # Numeric literal
        elif isinstance(node, NumberNode):
            return 'int'

        # String literal
        elif isinstance(node, StringNode):
            return 'string'

        # List literal - determine element type
        elif isinstance(node, ListNode):
            if node.elements:
                # Assume all list elements have same type as first
                first_elem_type = self.analyze(node.elements[0])
                return f'list<{first_elem_type}>'
            return 'list<unknown>'

        # Function call - handle built-ins like range()
        elif isinstance(node, FunctionCallNode):
            if node.function_name == "range":
                if len(node.arguments) not in [1, 2]:
                    raise SemanticError(f"Invalid number of arguments for range(), expected 1 or 2 arguments.")
                for arg in node.arguments:
                    arg_type = self.analyze(arg)
                    if arg_type != 'int':
                        raise SemanticError(f"Argument to range() must be an integer, got {arg_type}")
                return 'iterable'
            else:
                raise SemanticError(f"Unknown function call: {node.function_name}")

        # Function definition - create scope for parameters
        elif isinstance(node, FunctionDefNode):
            self.symbol_table.declare(node.name, 'function')
            self.symbol_table.enter_scope()
            for param in node.parameters:
                self.symbol_table.declare(param, 'int')  # Assume all params are int
            self.analyze(node.body)
            self.symbol_table.exit_scope()

        # Return statement - analyze the return value
        elif isinstance(node, ReturnNode):
            if node.value:
                self.analyze(node.value)

        else:
            raise SemanticError(f"No semantic analysis defined for {type(node).__name__}")
