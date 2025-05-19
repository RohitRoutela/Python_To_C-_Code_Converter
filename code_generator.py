class CodeGenerator:
    def __init__(self):
        # Initialize the code generator with empty state
        self.code = []  # Regular code for inside main()
        self.functions = []  # Function definitions to be placed outside main()
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
                    
                    # Handle cases where expression is already a string conversion
                    if isinstance(expr, tuple) and expr[0] == 'already_string':
                        expr = expr[1]  # Extract the actual string expression
                    
                    # We want to use the simplest possible print statement
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
                        # Check if false branch starts with another if statement
                        # This indicates an elif in Python
                        if len(ir[3]) > 0 and isinstance(ir[3][0], tuple) and ir[3][0][0] == 'if':
                            # This is an "elif" in Python, which becomes "else if" in C++
                            nested_if = ir[3][0]
                            nested_condition = self.generate_expr(nested_if[1])
                            nested_true = self.generate_block(nested_if[2])
                            nested_false = self.generate_block(nested_if[3]) if len(nested_if) > 3 and nested_if[3] else []
                            
                            self.code.append(self._indent(f"else if ({nested_condition}) {{"))
                            self.indentation_level += 1
                            self.code.extend(nested_true)
                            self.indentation_level -= 1
                            self.code.append(self._indent("}"))
                            
                            if nested_false:
                                self.code.append(self._indent("else {"))
                                self.indentation_level += 1
                                self.code.extend(nested_false)
                                self.indentation_level -= 1
                                self.code.append(self._indent("}"))
                        else:
                            # Regular else block
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
                        # Determine if left and right are strings or need conversion
                        left_is_string = self._is_string_literal_or_var(ir[2])
                        right_is_string = self._is_string_literal_or_var(ir[3])
                        
                        # Generate appropriate concatenation expressions
                        if left_is_string and right_is_string:
                            # Both are strings, direct concatenation
                            return f"{left} + {right}"
                        elif left_is_string:
                            # Right needs conversion (if not already a string)
                            if isinstance(ir[3], tuple) and ir[3][0] == 'function_call' and ir[3][1] == 'str':
                                # This is str() call - use the argument directly with to_string if needed
                                if len(ir[3][2]) == 1:
                                    arg = ir[3][2][0]
                                    if isinstance(arg, tuple) and arg[0] == 'const' and isinstance(arg[1], str):
                                        # String constant inside str() - no need for to_string
                                        return f"{left} + {self.generate_expr(arg)}"
                                    else:
                                        # Non-string inside str() - apply to_string once
                                        inner_expr = self.generate_expr(arg)
                                        return f"{left} + to_string({inner_expr})"
                            elif not self._is_already_string(right):
                                right = f"to_string({right})"
                            return f"{left} + {right}"
                        elif right_is_string:
                            # Left needs conversion (if not already a string)
                            if isinstance(ir[2], tuple) and ir[2][0] == 'function_call' and ir[2][1] == 'str':
                                # This is str() call - use the argument directly with to_string if needed
                                if len(ir[2][2]) == 1:
                                    arg = ir[2][2][0]
                                    if isinstance(arg, tuple) and arg[0] == 'const' and isinstance(arg[1], str):
                                        # String constant inside str() - no need for to_string
                                        return f"{self.generate_expr(arg)} + {right}"
                                    else:
                                        # Non-string inside str() - apply to_string once
                                        inner_expr = self.generate_expr(arg)
                                        return f"to_string({inner_expr}) + {right}"
                            elif not self._is_already_string(left):
                                left = f"to_string({left})"
                            return f"{left} + {right}"
                        else:
                            # Both need conversion
                            if not self._is_already_string(left):
                                left = f"to_string({left})"
                            if not self._is_already_string(right):
                                right = f"to_string({right})"
                            return f"{left} + {right}"
                    
                    # Simple expressions don't need extra parentheses
                    if operator == '**':
                        return f"pow({left}, {right})"
                    elif self._is_simple_expr(left) and self._is_simple_expr(right):
                        return f"{left} {operator} {right}"
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
                    # Try to determine the element type
                    if elements:
                        if all(self.is_numeric(elem) for elem in ir[1]):
                            if any(isinstance(elem[1], float) for elem in ir[1] if isinstance(elem, tuple) and elem[0] == 'const'):
                                return f"vector<double>{{{', '.join(elements)}}}"
                            else:
                                return f"vector<int>{{{', '.join(elements)}}}"
                        elif all(self.is_string(elem) for elem in ir[1]):
                            # Ensure all string elements have quotes
                            return f"vector<string>{{{', '.join(elements)}}}"
                        else:
                            # Mixed type or complex types
                            return f"vector<auto>{{{', '.join(elements)}}}"
                    else:
                        # Empty list
                        return "vector<auto>{}"

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
                    
                    # Special handling for list access
                    if func_name == "__list_access__" and len(arguments) == 2:
                        # This is our special marker for list indexing
                        container = arguments[0]
                        index = arguments[1]
                        return f"{container}[{index}]"
                        
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
                        # Check the argument type to determine the best way to convert
                        if len(ir[2]) == 1:
                            arg = ir[2][0]
                            if isinstance(arg, tuple):
                                if arg[0] == 'const':
                                    # For constants, we can simplify
                                    if isinstance(arg[1], (int, float)):
                                        return f"to_string({arguments_str})"
                                    elif isinstance(arg[1], str):
                                        # String constants don't need conversion
                                        return arguments_str
                                    elif isinstance(arg[1], bool):
                                        # Convert boolean to string
                                        return f"({arguments_str} ? \"true\" : \"false\")"
                                elif arg[0] == 'var':
                                    var_name = arg[1]
                                    if var_name in self.declared_vars:
                                        if self.declared_vars[var_name] in ['int', 'double', 'float']:
                                            return f"to_string({arguments_str})"
                                        elif self.declared_vars[var_name] == 'bool':
                                            return f"({arguments_str} ? \"true\" : \"false\")"
                                        elif self.declared_vars[var_name] == 'string':
                                            # No need to convert strings
                                            return arguments_str
                                
                        # Default case: apply to_string
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
                    # Store function definitions separately (outside main)
                    saved_indent = self.indentation_level
                    self.indentation_level = 0  # No indentation for functions outside main
                    
                    function_code = []
                    function_code.append(self._indent(f"auto {name}({param_str}) {{"))
                    self.indentation_level = 1  # Indent function body
                    function_code.extend(body)
                    self.indentation_level = 0  # Reset for closing brace
                    function_code.append(self._indent("}"))
                    
                    self.functions.append("\n".join(function_code))
                    self.indentation_level = saved_indent  # Restore indentation level

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
            
            # Check for already converted string marker
            if instruction_type == 'already_string':
                return ir[1]  # Return the string expression without additional conversion
            
            if instruction_type == 'binop':
                left = self.generate_expr(ir[2])
                right = self.generate_expr(ir[3])
                operator = ir[1]
                
                # Special handling for string concatenation
                if operator == '+':
                    # Determine if left and right are strings or need conversion
                    left_is_string = self._is_string_literal_or_var(ir[2])
                    right_is_string = self._is_string_literal_or_var(ir[3])
                    
                    # Generate appropriate concatenation expressions
                    if left_is_string and right_is_string:
                        # Both are strings, direct concatenation
                        return f"{left} + {right}"
                    elif left_is_string:
                        # Right needs conversion (if not already a string)
                        if isinstance(ir[3], tuple) and ir[3][0] == 'function_call' and ir[3][1] == 'str':
                            # This is str() call - use the argument directly with to_string if needed
                            if len(ir[3][2]) == 1:
                                arg = ir[3][2][0]
                                if isinstance(arg, tuple) and arg[0] == 'const' and isinstance(arg[1], str):
                                    # String constant inside str() - no need for to_string
                                    return f"{left} + {self.generate_expr(arg)}"
                                else:
                                    # Non-string inside str() - apply to_string once
                                    inner_expr = self.generate_expr(arg)
                                    return f"{left} + to_string({inner_expr})"
                        elif not self._is_already_string(right):
                            right = f"to_string({right})"
                        return f"{left} + {right}"
                    elif right_is_string:
                        # Left needs conversion (if not already a string)
                        if isinstance(ir[2], tuple) and ir[2][0] == 'function_call' and ir[2][1] == 'str':
                            # This is str() call - use the argument directly with to_string if needed
                            if len(ir[2][2]) == 1:
                                arg = ir[2][2][0]
                                if isinstance(arg, tuple) and arg[0] == 'const' and isinstance(arg[1], str):
                                    # String constant inside str() - no need for to_string
                                    return f"{self.generate_expr(arg)} + {right}"
                                else:
                                    # Non-string inside str() - apply to_string once
                                    inner_expr = self.generate_expr(arg)
                                    return f"to_string({inner_expr}) + {right}"
                        elif not self._is_already_string(left):
                            left = f"to_string({left})"
                        return f"{left} + {right}"
                    else:
                        # Both need conversion
                        if not self._is_already_string(left):
                            left = f"to_string({left})"
                        if not self._is_already_string(right):
                            right = f"to_string({right})"
                        return f"{left} + {right}"
                
                # Simple expressions don't need extra parentheses
                if operator == '**':
                    return f"pow({left}, {right})"
                elif self._is_simple_expr(left) and self._is_simple_expr(right):
                    return f"{left} {operator} {right}"
                else:
                    return f"({left} {operator} {right})"
            
            elif instruction_type == 'compare':
                left = self.generate_expr(ir[2])
                right = self.generate_expr(ir[3])
                operator = ir[1]
                
                # Simple expressions don't need extra parentheses
                if self._is_simple_expr(left) and self._is_simple_expr(right):
                    return f"{left} {operator} {right}"
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

    def _is_simple_expr(self, expr):
        """Check if an expression is simple enough to not need parentheses"""
        # If it's a variable name, constant, or simple function call
        if isinstance(expr, str):
            # Check if it's a simple identifier, number, or string literal
            return (expr.isalnum() or 
                   (expr.startswith('"') and expr.endswith('"')) or
                   (expr.startswith("'") and expr.endswith("'")) or
                   expr.isdigit() or
                   expr == "true" or
                   expr == "false" or
                   (expr.startswith("to_string(") and expr.endswith(")")) or
                   not any(op in expr for op in "+-*/%<>=!&|^~"))
        return False

    def _is_string_expr(self, ir):
        # Check if an expression is a string type
        if isinstance(ir, tuple):
            if ir[0] == 'const' and isinstance(ir[1], str):
                return True
            elif ir[0] == 'var':
                var_name = ir[1]
                return var_name in self.declared_vars and self.declared_vars[var_name] == 'string'
            elif ir[0] == 'function_call' and ir[1] in ['str', 'to_string']:
                return True
            elif ir[0] == 'already_string':
                return True
        return False
        
    def _is_string_literal_or_var(self, ir):
        # Check if an expression is a string literal or a variable
        if isinstance(ir, tuple):
            if ir[0] == 'const' and isinstance(ir[1], str):
                return True
            elif ir[0] == 'var':
                var_name = ir[1]
                return var_name in self.declared_vars and self.declared_vars[var_name] == 'string'
        return False
 
    def _is_already_string(self, ir):
        # Check if an expression is already a string
        if isinstance(ir, tuple):
            if ir[0] == 'already_string':
                return True
            elif ir[0] == 'const' and isinstance(ir[1], str):
                return True
            elif ir[0] == 'var' and ir[1] in self.declared_vars and self.declared_vars[ir[1]] == 'string':
                return True
            elif ir[0] == 'function_call' and ir[1] == 'str':
                return True
        elif isinstance(ir, str) and (ir.startswith('"') or ir.startswith("'")):
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
        header_code = "#include <bits/stdc++.h>\n#include <vector>\n#include <string>\nusing namespace std;\n\n"
        
        # Add function declarations before main
        functions_code = ""
        if self.functions:
            functions_code = "\n".join(self.functions) + "\n\n"
            
        # Generate main function with the rest of the code
        main_code = "int main() {\n"
        if self.code:
            main_code += "\n".join(filter(None, self.code))
        main_code += "\n    return 0;\n}"
        
        # Combine all parts
        cpp_code = header_code + functions_code + main_code
        return cpp_code

    def is_numeric(self, expr):
        """Check if an expression is numeric (int or float)."""
        if isinstance(expr, tuple):
            if expr[0] == 'const':
                return isinstance(expr[1], (int, float))
            elif expr[0] == 'var':
                var_name = expr[1]
                if var_name in self.declared_vars:
                    return self.declared_vars[var_name] in ['int', 'double']
            elif expr[0] == 'binop':
                # Numeric operations typically yield numeric results
                return self.is_numeric(expr[2]) and self.is_numeric(expr[3])
        return False
        
    def is_string(self, expr):
        """Check if an expression is a string."""
        if isinstance(expr, tuple):
            if expr[0] == 'const':
                return isinstance(expr[1], str)
            elif expr[0] == 'var':
                var_name = expr[1]
                if var_name in self.declared_vars:
                    return self.declared_vars[var_name] == 'string'
            elif expr[0] == 'already_string':
                return True
        return False
