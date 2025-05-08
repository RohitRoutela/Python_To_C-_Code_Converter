class CodeGenerator:
    def __init__(self):
        self.code = []
        self.declared_vars = {}
        self.indentation_level = 1  # Start with an indentation level of 1 for the main function.

    def generate(self, ir):
        if isinstance(ir, list):
            for stmt in ir:
                self.generate(stmt)  # Now this modifies self.code directly

        elif isinstance(ir, tuple):
            instruction_type = ir[0]

            if instruction_type == 'assign':
                var_name = ir[1]
                expr = self.generate_expr(ir[2])
                var_type = self.infer_var_type(ir[2])

                if var_name not in self.declared_vars:
                    self.code.append(self._indent(f"{var_type} {var_name} = {expr};"))
                    self.declared_vars[var_name] = var_type
                else:
                    self.code.append(self._indent(f"{var_name} = {expr};"))

            elif instruction_type == 'print':
                expr = self.generate_expr(ir[1])
                self.code.append(self._indent(f"std::cout << {expr} << std::endl;"))

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

            elif instruction_type == 'while':
                condition = self.generate_expr(ir[1])
                body = self.generate_block(ir[2])

                self.code.append(self._indent(f"while ({condition}) {{"))
                self.indentation_level += 1
                self.code.extend(body)
                self.indentation_level -= 1
                self.code.append(self._indent("}"))

            elif instruction_type == 'for':
                var_name = ir[1]
                iterable = self.generate_expr(ir[2])
                body = self.generate_block(ir[3])

                self.code.append(self._indent(f"for (auto {var_name} : {iterable}) {{"))
                self.indentation_level += 1
                self.code.extend(body)
                self.indentation_level -= 1
                self.code.append(self._indent("}"))

            elif instruction_type == 'binop':
                left = self.generate_expr(ir[2])
                right = self.generate_expr(ir[3])
                return f"({left} {ir[1]} {right})"

            elif instruction_type == 'var':
                return ir[1]

            elif instruction_type == 'const':
                if isinstance(ir[1], str):
                    return f'"{ir[1]}"'
                return str(ir[1])

            elif instruction_type == 'function_call':
                func_name = ir[1]
                arguments = ", ".join(self.generate_expr(arg) for arg in ir[2])
                return f"{func_name}({arguments})"

            elif instruction_type == 'return':
                value = self.generate_expr(ir[1]) if ir[1] else ""
                self.code.append(self._indent(f"return {value};"))

        else:
            raise Exception(f"Unknown IR format: {ir}")

    def generate_expr(self, ir):
        if ir is None:
            raise ValueError("Invalid expression: None value encountered.")

        if isinstance(ir, tuple):
            return self.generate(ir)

        return str(ir)

    def generate_block(self, ir_block):
        saved_code = self.code
        self.code = []
        self.generate(ir_block)
        block_code = self.code
        self.code = saved_code
        return block_code

    def infer_var_type(self, expr):
        if isinstance(expr, tuple):
            if expr[0] == 'const':
                if isinstance(expr[1], int):
                    return 'int'
                elif isinstance(expr[1], float):
                    return 'float'
                elif isinstance(expr[1], str):
                    return 'string'
                else:
                    return 'unknown'
            if expr[0] == 'binop':
                left_type = self.infer_var_type(expr[2])
                right_type = self.infer_var_type(expr[3])
                if left_type == 'unknown' or right_type == 'unknown':
                    raise Exception(f"Unable to infer type for binary operation: {left_type} vs {right_type}")
                if left_type == right_type:
                    return left_type
                else:
                    raise Exception(f"Type mismatch in binary operation: {left_type} vs {right_type}")
        elif isinstance(expr, str):
            return 'string'
        elif isinstance(expr, int):
            return 'int'
        elif isinstance(expr, float):
            return 'float'

        return 'unknown'

    def _indent(self, code):
        return '    ' * self.indentation_level + code

    def get_cpp_code(self):
        cpp_code = "#include<bits/stdc++.h>\nusing namespace std;\n\nint main() {\n"
        if self.code:
            cpp_code += "\n".join(filter(None, self.code))
        cpp_code += "\n    return 0;\n}"
        return cpp_code
