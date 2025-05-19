from ast_nodes import *
import ast

class IRGenerator:
    def __init__(self):
        # Initialize IR generator state
        self.instructions = []
        self.label_count = 0

    def new_label(self):
        # Generate unique label identifiers for control flow
        self.label_count += 1
        return f"label_{self.label_count}"

    def generate(self, node):
        try:
            # Process list of statements
            if isinstance(node, list):
                for stmt in node:
                    self.generate(stmt)
                    
            # Process Python AST Module
            elif isinstance(node, ast.Module):
                for stmt in node.body:
                    self.generate(stmt)
            
            # Process Python AST expressions
            elif isinstance(node, ast.Expr):
                result = self.generate(node.value)
                if result:  # Only add if the expression returns a value
                    self.instructions.append(result)
                    
            # Process Python AST assignments
            elif isinstance(node, ast.Assign):
                target = node.targets[0].id if isinstance(node.targets[0], ast.Name) else None
                if target:
                    value = self.generate(node.value)
                    self.instructions.append(('assign', target, value))
                    
            # Process Python AST function calls
            elif isinstance(node, ast.Call):
                func_name = self.generate(node.func)
                if isinstance(func_name, tuple) and func_name[0] == 'var':
                    func_name = func_name[1]
                args = [self.generate(arg) for arg in node.args]
                
                if func_name == 'print':
                    # Special handling for print statements
                    if args:
                        self.instructions.append(('print', args[0]))
                    else:
                        self.instructions.append(('print', ('const', "")))
                    return None
                
                return ('function_call', func_name, args)
                
            # Process Python AST if statements
            elif isinstance(node, ast.If):
                condition = self.generate(node.test)
                true_body = []
                for stmt in node.body:
                    result = self.generate(stmt)
                    if result:
                        true_body.append(result)
                        
                false_body = []
                if node.orelse:
                    for stmt in node.orelse:
                        result = self.generate(stmt)
                        if result:
                            false_body.append(result)
                            
                self.instructions.append(('if', condition, true_body, false_body if false_body else None))
                
            # Process Python AST variable references
            elif isinstance(node, ast.Name):
                # Check if this is a variable in an f-string
                if hasattr(node, '_is_string_format') and node._is_string_format:
                    # Mark this variable to prevent to_string conversion
                    return ('var', node.id, True)  # The third parameter indicates it's from an f-string
                return ('var', node.id)
                
            # Process Python AST constants
            elif isinstance(node, ast.Constant):
                return ('const', node.value)
                
            # Process Python AST binary operations
            elif isinstance(node, ast.BinOp):
                left = self.generate(node.left)
                right = self.generate(node.right)
                
                op_map = {
                    ast.Add: '+',
                    ast.Sub: '-',
                    ast.Mult: '*',
                    ast.Div: '/',
                    ast.FloorDiv: '//',
                    ast.Mod: '%',
                    ast.Pow: '**',
                }
                
                op = op_map.get(type(node.op), str(type(node.op).__name__))
                return ('binop', op, left, right)
                
            # Process Python AST comparison operations
            elif isinstance(node, ast.Compare):
                # Handle comparison operations
                left = self.generate(node.left)
                
                # Process the first comparison operator and right operand
                if len(node.ops) > 0 and len(node.comparators) > 0:
                    right = self.generate(node.comparators[0])
                    
                    op_map = {
                        ast.Eq: '==',
                        ast.NotEq: '!=',
                        ast.Lt: '<',
                        ast.LtE: '<=',
                        ast.Gt: '>',
                        ast.GtE: '>=',
                    }
                    
                    op = op_map.get(type(node.ops[0]), str(type(node.ops[0]).__name__))
                    return ('compare', op, left, right)
                
                raise Exception(f"Invalid comparison operation")
                
            # Process Python AST f-strings
            elif isinstance(node, ast.JoinedStr):
                parts = []
                for value in node.values:
                    if isinstance(value, ast.FormattedValue):
                        parts.append(self.generate(value))
                    else:
                        parts.append(self.generate(value))
                
                # Build a string concatenation expression
                if parts:
                    result = parts[0]
                    for part in parts[1:]:
                        result = ('binop', '+', result, part)
                    return result
                return ('const', "")

            # Program node (root)
            elif isinstance(node, Program):
                for stmt in node.statements:
                    self.generate(stmt)

            # Generate assignment IR
            elif isinstance(node, AssignmentNode):
                expr = self.generate(node.expression)
                self.instructions.append(('assign', node.identifier, expr))

            # Generate print statement IR
            elif isinstance(node, PrintNode):
                expr = self.generate(node.expression)
                self.instructions.append(('print', expr))

            # Generate if-statement IR with branches
            elif isinstance(node, IfNode):
                condition_ir = self.generate(node.condition)

                true_branch_ir = self._generate_block(node.true_branch)
                false_branch_ir = self._generate_block(node.false_branch) if node.false_branch else None

                self.instructions.append(('if', condition_ir, true_branch_ir, false_branch_ir))

            # Generate while-loop IR
            elif isinstance(node, WhileNode):
                condition_ir = self.generate(node.condition)
                body_ir = self._generate_block(node.body)
                self.instructions.append(('while', condition_ir, body_ir))

            # Generate for-loop IR
            elif isinstance(node, ForNode):
                iterable_ir = self.generate(node.iterable)
                body_ir = self._generate_block(node.body)
                self.instructions.append(('for', node.variable, iterable_ir, body_ir))

            # Generate function call IR
            elif isinstance(node, FunctionCallNode):
                args = [self.generate(arg) for arg in node.arguments]
                return ('function_call', node.function_name, args)

            # Generate function definition IR
            elif isinstance(node, FunctionDefNode):
                body_ir = self._generate_block(node.body)
                self.instructions.append(('function_def', node.name, node.parameters, body_ir))

            # Generate return statement IR
            elif isinstance(node, ReturnNode):
                value_ir = self.generate(node.value) if node.value is not None else None
                self.instructions.append(('return', value_ir))

            # Generate binary operation IR
            elif isinstance(node, BinaryOpNode):
                left = self.generate(node.left)
                right = self.generate(node.right)
                return ('binop', node.operator, left, right)

            # Generate input operation IR
            elif isinstance(node, InputNode):
                prompt_ir = self.generate(node.prompt) if node.prompt else ('const', "")
                return ('input', prompt_ir)

            # Generate list literal IR
            elif isinstance(node, ListNode):
                elements = [self.generate(elem) for elem in node.elements]
                return ('list', elements)

            # Generate variable reference IR
            elif isinstance(node, IdentifierNode):
                return ('var', node.name)

            # Generate constant value IR
            elif isinstance(node, NumberNode) or isinstance(node, StringNode):
                return ('const', node.value)

            # Process f-string value expressions
            elif isinstance(node, ast.FormattedValue):
                value = self.generate(node.value)
                return value

            # Process f-strings (formatted strings)
            elif isinstance(node, ast.JoinedStr):
                parts = []
                for value in node.values:
                    if isinstance(value, ast.FormattedValue):
                        parts.append(self.generate(value))
                    else:
                        parts.append(self.generate(value))
                
                # Build a sequence of string concatenations
                result = parts[0]
                for part in parts[1:]:
                    result = ('binop', '+', result, part)
                
                return result

            else:
                raise Exception(f"Unknown node type: {type(node).__name__}")
                
        except Exception as e:
            # Add node context to exceptions for better debugging
            node_info = f" in node {type(node).__name__}"
            if hasattr(node, 'line'):
                node_info += f" at line {node.line}"
            raise Exception(f"{str(e)}{node_info}")

    def _generate_block(self, statements):
        # Process a block of statements with independent state
        sub_generator = IRGenerator()
        sub_generator.label_count = self.label_count  # Share label counter
        
        if statements is None:
            return []
            
        sub_generator.generate(statements)
        self.label_count = sub_generator.label_count  # Sync label counter
        return sub_generator.get_instructions()

    def get_instructions(self):
        # Return the complete list of generated IR instructions
        return self.instructions

    def visit_BinOp(self, node):
        # Process binary operations
        left = self.generate(node.left)
        right = self.generate(node.right)
        
        # Map Python operators to C++ operators
        op_map = {
            ast.Add: '+',
            ast.Sub: '-',
            ast.Mult: '*',
            ast.Div: '/',
            ast.FloorDiv: '/',  # Note: This needs special handling
            ast.Mod: '%',
            ast.Pow: '**',
        }
        
        if isinstance(node.op, ast.FloorDiv):
            # Special case for floor division
            return ('function_call', 'floor', [('binop', '/', left, right)])
        
        if type(node.op) in op_map:
            return ('binop', op_map[type(node.op)], left, right)
        
        raise Exception(f"Unsupported binary operator: {type(node.op).__name__}")

    def visit_FormattedValue(self, node):
        # Process f-string value expressions
        value = self.generate(node.value)
        return value

    def visit_JoinedStr(self, node):
        # Process f-strings (formatted strings)
        parts = []
        for value in node.values:
            if isinstance(value, ast.FormattedValue):
                parts.append(self.generate(value))
            else:
                parts.append(self.generate(value))
        
        # Build a sequence of string concatenations
        result = parts[0]
        for part in parts[1:]:
            result = ('binop', '+', result, part)
            
        return result
