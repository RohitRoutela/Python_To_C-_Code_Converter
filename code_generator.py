class CodeGenerator:
    def __init__(self):
        # Initialize the code generator with empty state
        self.code = []
        self.declared_vars = {}
        self.indentation_level = 1  # Main function indentation level
        self.error_context = ""

    def generate(self, ir):
        try:
            # Process list of instructions
            if isinstance(ir, list):
                for stmt in ir:
                    self.generate(stmt)

            # Process tuple instruction
            elif isinstance(ir, tuple):
                instruction_type = ir[0]

                # Variable assignment
                if instruction_type == 'assign':
                    var_name = ir[1]
                    expr = self.generate_expr(ir[2])
                    
                    # Special handling for boolean values
                    if isinstance(ir[2], tuple) and ir[2][0] == 'const' and isinstance(ir[2][1], bool):
                        var_type = 'bool'
                    else:
                        var_type = self.infer_var_type(ir[2])
                    
                    # Check if expression is from an input operation
                    if isinstance(ir[2], tuple) and ir[2][0] == 'input':
                        prompt = self.generate_expr(ir[2][1])
                        if prompt and prompt != '""':
                            self.code.append(self._indent(f"cout << {prompt};"))
                        
                        # If variable is already declared, read directly into it
                        if var_name in self.declared_vars:
                            if self.declared_vars[var_name] == 'int':
                                self.code.append(self._indent(f"cin >> {var_name};"))
                            elif self.declared_vars[var_name] == 'double':
                                self.code.append(self._indent(f"cin >> {var_name};"))
                            else:  # string or other types
                                self.code.append(self._indent(f"cin >> {var_name};"))
                        else:
                            # If variable not declared, create with appropriate type
                            self.code.append(self._indent(f"string {var_name};"))
                            self.code.append(self._indent(f"cin >> {var_name};"))
                            self.declared_vars[var_name] = 'string'
                        return
                    
                    # For int(input()) pattern
                    if isinstance(ir[2], tuple) and ir[2][0] == 'function_call' and ir[2][1] == 'int' and \
                       len(ir[2][2]) == 1 and isinstance(ir[2][2][0], tuple) and ir[2][2][0][0] == 'input':
                        prompt = self.generate_expr(ir[2][2][0][1]) if len(ir[2][2][0]) > 1 else '""'
                        if prompt and prompt != '""':
                            self.code.append(self._indent(f"cout << {prompt};"))
                        
                        # Declare variable if not already declared
                        if var_name not in self.declared_vars:
                            self.code.append(self._indent(f"int {var_name};"))
                            self.declared_vars[var_name] = 'int'
                        # Read directly into the variable
                        self.code.append(self._indent(f"cin >> {var_name};"))
                        return

                    # Normal variable assignment
                    if var_name not in self.declared_vars:
                        self.code.append(self._indent(f"{var_type} {var_name} = {expr};"))
                        self.declared_vars[var_name] = var_type
                    else:
                        self.code.append(self._indent(f"{var_name} = {expr};"))

                # Print statement
                elif instruction_type == 'print':
                    expr = self.generate_expr(ir[1])
                    
                    # Don't apply to_string if it's already a string expression
                    if ir[1][0] == 'binop' and ir[1][1] == '+' and self._is_string_expr(ir[1][2]):
                        # For concatenation where the first part is a string, don't add to_string
                        self.code.append(self._indent(f"cout << {expr} << endl;"))
                    elif self._is_string_expr(ir[1]):
                        # For string literals or variables that are strings
                        self.code.append(self._indent(f"cout << {expr} << endl;"))
                    else:
                        self.code.append(self._indent(f"cout << {expr} << endl;"))

                # If-else statement
                elif instruction_type == 'if':
                    condition = self.generate_expr(ir[1])
                    true_branch = self.generate_block(ir[2])
                    false_branch = self.generate_block(ir[3]) if ir[3] else []

                    self.code.append(self._indent(f"if ({condition}) {{"))
                    self.indentation_level += 1
                    self.code.extend(true_branch)
                    self.indentation_level -= 1
                    self.code.append(self._indent("}"))

                    if false_branch:
                        self.code.append(self._indent("else {"))
                        self.indentation_level += 1
                        self.code.extend(false_branch)
                        self.indentation_level -= 1
                        self.code.append(self._indent("}"))

                # While loop
                elif instruction_type == 'while':
                    condition = self.generate_expr(ir[1])
                    body = self.generate_block(ir[2])

                    self.code.append(self._indent(f"while ({condition}) {{"))
                    self.indentation_level += 1
                    self.code.extend(body)
                    self.indentation_level -= 1
                    self.code.append(self._indent("}"))

                # For loop (with special handling for range)
                elif instruction_type == 'for':
                    var_name = ir[1]
                    iterable = self.generate_expr(ir[2])
                    body = self.generate_block(ir[3])

                    if self.is_range_call(ir[2]):
                        range_info = self.extract_range_info(ir[2])
                        if len(range_info) == 1:
                            # range(stop)
                            self.code.append(self._indent(f"for (int {var_name} = 0; {var_name} < {range_info[0]}; ++{var_name}) {{"))
                        elif len(range_info) == 2:
                            # range(start, stop)
                            self.code.append(self._indent(f"for (int {var_name} = {range_info[0]}; {var_name} < {range_info[1]}; ++{var_name}) {{"))
                        elif len(range_info) == 3:
                            # range(start, stop, step)
                            step = range_info[2]
                            if step.startswith('-'):
                                self.code.append(self._indent(f"for (int {var_name} = {range_info[0]}; {var_name} > {range_info[1]}; {var_name} -= {step[1:]}) {{"))
                            else:
                                self.code.append(self._indent(f"for (int {var_name} = {range_info[0]}; {var_name} < {range_info[1]}; {var_name} += {step}) {{"))
                    else:
                        # For non-range iterables
                        self.code.append(self._indent(f"for (auto& {var_name} : {iterable}) {{"))
                        
                    self.indentation_level += 1
                    self.code.extend(body)
                    self.indentation_level -= 1
                    self.code.append(self._indent("}"))

                # Binary operation
                elif instruction_type == 'binop':
                    left = self.generate_expr(ir[2])
                    right = self.generate_expr(ir[3])
                    operator = ir[1]
                    
                    # Special handling for string concatenation
                    if operator == '+':
                        # For string concatenation, only convert non-string values to string
                        left_is_string = (
                            isinstance(ir[2], tuple) and 
                            ((ir[2][0] == 'const' and isinstance(ir[2][1], str)) or (ir[2][0] == 'var' and ir[2][1] in self.declared_vars and self.declared_vars[ir[2][1]] == 'string'))
                        )
                        
                        right_is_string = (
                            isinstance(ir[3], tuple) and 
                            ((ir[3][0] == 'const' and isinstance(ir[3][1], str)) or (ir[3][0] == 'var' and ir[3][1] in self.declared_vars and self.declared_vars[ir[3][1]] == 'string'))
                        )
                        
                        # If either side is a string, we need a string concatenation
                        if left_is_string or right_is_string:
                            # Only convert non-string expressions to string
                            if not left_is_string and not (
                                isinstance(ir[2], tuple) and ir[2][0] == 'var' and 
                                self.declared_vars.get(ir[2][1]) == 'string'
                            ):
                                left = f"to_string({left})"
                                
                            if not right_is_string and not (
                                isinstance(ir[3], tuple) and ir[3][0] == 'var' and
                                self.declared_vars.get(ir[3][1]) == 'string'
                            ):
                                right = f"to_string({right})"
                            
                            return f"({left} + {right})"
                    
                    if operator == '**':
                        return f"pow({left}, {right})"
                    else:
                        return f"({left} {operator} {right})"

                # Input operation
                elif instruction_type == 'input':
                    prompt = self.generate_expr(ir[1])
                    # Return a placeholder that will be handled in the assignment
                    return ('input', prompt)

                # Variable reference
                elif instruction_type == 'var':
                    return ir[1]

                # Constant value
                elif instruction_type == 'const':
                    if isinstance(ir[1], str):
                        # Escape string literals
                        escaped = ir[1].replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                        return f'"{escaped}"'
                    elif isinstance(ir[1], bool):
                        # Convert bool to C++ true/false and make sure it's typed correctly
                        if ir[1] not in self.declared_vars or self.declared_vars[ir[1]] != 'bool':
                            # Only add a declaration if not already declared
                            return "true" if ir[1] else "false"
                    return str(ir[1])

                # List/vector
                elif instruction_type == 'list':
                    elements = [self.generate_expr(elem) for elem in ir[1]]
                    return f"vector<auto>{{{', '.join(elements)}}}"

                # Function call
                elif instruction_type == 'function_call':
                    func_name = ir[1]
                    # Make sure arguments are converted to strings before joining
                    arguments = []
                    for arg in ir[2]:
                        arg_expr = self.generate_expr(arg)
                        # Make sure we have a string
                        if isinstance(arg_expr, tuple):
                            arg_expr = str(arg_expr)
                        arguments.append(str(arg_expr))
                    arguments_str = ", ".join(arguments)
                    
                    # Handle special function translations
                    if func_name == 'len':
                        return f"{arguments_str}.size()"
                    elif func_name == 'print':
                        self.code.append(self._indent(f"cout << {arguments_str} << endl;"))
                        return ""
                    elif func_name == 'type':
                        # Special handling for Python's type() function
                        return f"typeid({arguments_str}).name()"
                    elif func_name == 'int':
                        # Handle int conversion with negative number support
                        return f"stoi({arguments_str})"
                    elif func_name == 'float':
                        # Handle float conversion
                        return f"stod({arguments_str})"
                    elif func_name == 'str':
                        # Handle string conversion for C++
                        return f"to_string({arguments_str})"
                    elif func_name == 'bool':
                        # For 'bool()', create proper C++ boolean casting
                        if len(ir[2]) == 1 and isinstance(ir[2][0], tuple) and ir[2][0][0] == 'var':
                            # If it's a variable reference, just cast it directly without to_string
                            var_name = ir[2][0][1]
                            return f"bool({var_name})"
                        else:
                            # For all other cases use standard bool conversion
                            return f"bool({arguments_str})"
                    else:
                        return f"{func_name}({arguments_str})"

                # Function definition
                elif instruction_type == 'function_def':
                    name = ir[1]
                    params = ir[2]
                    body = self.generate_block(ir[3])
                    
                    param_str = ", ".join([f"auto {p}" for p in params])
                    self.code.append(self._indent(f"auto {name}({param_str}) {{"))
                    self.indentation_level += 1
                    self.code.extend(body)
                    self.indentation_level -= 1
                    self.code.append(self._indent("}"))

                # Return statement
                elif instruction_type == 'return':
                    value = self.generate_expr(ir[1]) if ir[1] else ""
                    self.code.append(self._indent(f"return {value};"))

            else:
                raise Exception(f"Unknown IR format: {ir}")
                
        except Exception as e:
            raise Exception(f"Code generation error: {str(e)} in {self.error_context}")

    def is_range_call(self, ir):
        # Check if IR node is a call to range()
        if isinstance(ir, tuple) and ir[0] == 'function_call' and ir[1] == 'range':
            return True
        return False
        
    def extract_range_info(self, ir):
        # Extract start, stop, step from range function call
        if ir[0] == 'function_call' and ir[1] == 'range':
            args = ir[2]
            return [self.generate_expr(arg) for arg in args]
        return []

    def generate_expr(self, ir):
        # Generate code for an expression
        if ir is None:
            return ""

        self.error_context = f"expression {ir}"
        if isinstance(ir, tuple):
            instruction_type = ir[0]
            
            if instruction_type == 'binop':
                left = self.generate_expr(ir[2])
                right = self.generate_expr(ir[3])
                operator = ir[1]
                
                # Special handling for string concatenation
                if operator == '+':
                    # For string concatenation, only convert non-string values to string
                    left_is_string = (
                        isinstance(ir[2], tuple) and 
                        ((ir[2][0] == 'const' and isinstance(ir[2][1], str)) or (ir[2][0] == 'var' and ir[2][1] in self.declared_vars and self.declared_vars[ir[2][1]] == 'string'))
                    )
                    
                    right_is_string = (
                        isinstance(ir[3], tuple) and 
                        ((ir[3][0] == 'const' and isinstance(ir[3][1], str)) or (ir[3][0] == 'var' and ir[3][1] in self.declared_vars and self.declared_vars[ir[3][1]] == 'string'))
                    )
                    
                    # If either side is a string, we need a string concatenation
                    if left_is_string or right_is_string:
                        # Only convert non-string expressions to string
                        if not left_is_string and not (
                            isinstance(ir[2], tuple) and ir[2][0] == 'var' and 
                            self.declared_vars.get(ir[2][1]) == 'string'
                        ):
                            left = f"to_string({left})"
                            
                        if not right_is_string and not (
                            isinstance(ir[3], tuple) and ir[3][0] == 'var' and
                            self.declared_vars.get(ir[3][1]) == 'string'
                        ):
                            right = f"to_string({right})"
                        
                        return f"({left} + {right})"
                
                if operator == '**':
                    return f"pow({left}, {right})"
                else:
                    return f"({left} {operator} {right})"
            else:
                try:
                    result = self.generate(ir)
                    return result if result is not None else ""
                except Exception as e:
                    # If we get an error, convert to string as a fallback
                    return str(ir)
        # Handle non-string values
        if ir is not None and not isinstance(ir, str):
            return str(ir)
        return ir if ir is not None else ""

    def _is_string_expr(self, ir):
        # Check if an expression is a string type
        if isinstance(ir, tuple):
            if ir[0] == 'const' and isinstance(ir[1], str):
                return True
            elif ir[0] == 'var':
                # This is a simplification - ideally would check variable type
                return True
            elif ir[0] == 'function_call' and ir[1] in ['str', 'to_string']:
                return True
        return False

    def _is_known_string_var(self, var_name):
        # Check if a variable is known to be a string
        return var_name in self.declared_vars and self.declared_vars[var_name] == 'string'

    def generate_block(self, ir_block):
        # Generate a block of code while preserving the outer context
        saved_code = self.code
        saved_context = self.error_context
        self.code = []
        self.error_context = f"block {ir_block}"
        
        if ir_block:
            self.generate(ir_block)
            
        block_code = self.code
        self.code = saved_code
        self.error_context = saved_context
        return block_code

    def infer_var_type(self, expr):
        # Determine the C++ type for a given expression
        try:
            if isinstance(expr, tuple):
                if expr[0] == 'const':
                    if isinstance(expr[1], int):
                        return 'int'
                    elif isinstance(expr[1], float):
                        return 'double'
                    elif isinstance(expr[1], str):
                        return 'string'
                    elif isinstance(expr[1], bool):
                        return 'bool'  # Use bool type for boolean values
                    elif expr[1] is None:
                        return 'void*'
                    else:
                        return 'auto'
                elif expr[0] == 'function_call':
                    # Better inference for common function calls
                    if expr[1] == 'bool':
                        return 'bool'
                    elif expr[1] == 'int':
                        return 'int'
                    elif expr[1] == 'float':
                        return 'double'
                    elif expr[1] == 'str':
                        return 'string'
                    # Cannot infer other function return types without context
                    return 'auto'
                elif expr[0] == 'binop':
                    left_type = self.infer_var_type(expr[2])
                    right_type = self.infer_var_type(expr[3])
                    
                    # Comparison operators yield boolean
                    if expr[1] in ['>', '<', '>=', '<=', '==', '!=']:
                        return 'bool'
                    
                    # Type promotion rules
                    if left_type == 'double' or right_type == 'double':
                        return 'double'
                    elif left_type == 'int' and right_type == 'int':
                        return 'int'
                    elif left_type == 'string' or right_type == 'string':
                        return 'string'
                    elif left_type == 'bool' and right_type == 'bool':
                        return 'bool'
                    else:
                        return 'auto'
                elif expr[0] == 'var':
                    var_name = expr[1]
                    if var_name in self.declared_vars:
                        return self.declared_vars[var_name]
                    return 'auto'
            elif isinstance(expr, str):
                return 'string'
            elif isinstance(expr, int):
                return 'int'
            elif isinstance(expr, float):
                return 'double'
            elif isinstance(expr, bool):
                return 'bool'
                
            return 'auto'
        except Exception:
            # Fallback to auto
            return 'auto'

    def _indent(self, code):
        # Add proper indentation to code line
        return '    ' * self.indentation_level + code

    def get_cpp_code(self):
        # Generate the complete C++ program with includes and main function
        header_code = "#include <bits/stdc++.h>\nusing namespace std;\n\n"
        
        cpp_code = header_code + "int main() {\n"
        if self.code:
            cpp_code += "\n".join(filter(None, self.code))
        cpp_code += "\n    return 0;\n}"
        return cpp_code
