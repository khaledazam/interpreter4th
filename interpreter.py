import sys

# --- Debug Flag ---
DEBUG_MODE = False

# --- Error Classes ---
class Error(Exception):
    def __init__(self, name, message, pos):
        self.name = name
        self.message = message
        self.pos = pos

    def __str__(self):
        return f"{self.name}: {self.message} at position {self.pos}"

class IllegalCharError(Error):
    def __init__(self, message, pos):
        super().__init__("Illegal Character Error", message, pos)

class InvalidSyntaxError(Error):
    def __init__(self, message, pos):
        super().__init__("Invalid Syntax Error", message, pos)

class RuntimeError(Error):
    def __init__(self, message, pos):
        super().__init__("Runtime Error", message, pos)

# --- Constants & Token Types ---
TT_INT      = 'INT'
TT_FLOAT    = 'FLOAT'
TT_ID       = 'ID'
TT_KEYWORD  = 'KEYWORD'
TT_PLUS     = 'PLUS'
TT_MINUS    = 'MINUS'
TT_MUL      = 'MUL'
TT_DIV      = 'DIV'
TT_EQ       = 'EQ'
TT_EE       = 'EE'
TT_GT       = 'GT'
TT_LT       = 'LT'
TT_LPAREN   = 'LPAREN'
TT_RPAREN   = 'RPAREN'
TT_EOF      = 'EOF'
TT_NEWLINE  = 'NEWLINE'

KEYWORDS = ['let', 'if', 'then', 'else', 'while', 'do', 'print']

# --- Token Class ---
class Token:
    def __init__(self, type_, value=None, pos=None):
        self.type = type_
        self.value = value
        self.pos = pos

    def __repr__(self):
        if self.value is not None: return f'{self.type}:{self.value}'
        return f'{self.type}'

# --- Lexer ---
class Lexer:
    def __init__(self, text):
        self.text = text
        self.pos = -1
        self.current_char = None
        self.advance()

    def advance(self):
        self.pos += 1
        self.current_char = self.text[self.pos] if self.pos < len(self.text) else None

    def make_tokens(self):
        tokens = []
        while self.current_char is not None:
            pos_start = self.pos
            if self.current_char in ' \t':
                self.advance()
            elif self.current_char in '\n;':
                tokens.append(Token(TT_NEWLINE, pos=pos_start))
                self.advance()
            elif self.current_char.isdigit():
                tokens.append(self.make_number())
            elif self.current_char.isalpha():
                tokens.append(self.make_identifier())
            elif self.current_char == '+':
                tokens.append(Token(TT_PLUS, pos=pos_start))
                self.advance()
            elif self.current_char == '-':
                tokens.append(Token(TT_MINUS, pos=pos_start))
                self.advance()
            elif self.current_char == '*':
                tokens.append(Token(TT_MUL, pos=pos_start))
                self.advance()
            elif self.current_char == '/':
                tokens.append(Token(TT_DIV, pos=pos_start))
                self.advance()
            elif self.current_char == '(':
                tokens.append(Token(TT_LPAREN, pos=pos_start))
                self.advance()
            elif self.current_char == ')':
                tokens.append(Token(TT_RPAREN, pos=pos_start))
                self.advance()
            elif self.current_char == '=':
                tokens.append(self.make_equals())
            elif self.current_char == '>':
                tokens.append(Token(TT_GT, pos=pos_start))
                self.advance()
            elif self.current_char == '<':
                tokens.append(Token(TT_LT, pos=pos_start))
                self.advance()
            else:
                raise IllegalCharError(f"'{self.current_char}'", self.pos)

        tokens.append(Token(TT_EOF, pos=self.pos))
        return tokens

    def make_number(self):
        num_str = ''
        pos_start = self.pos
        dot_count = 0
        while self.current_char is not None and (self.current_char.isdigit() or self.current_char == '.'):
            if self.current_char == '.':
                if dot_count == 1: break
                dot_count += 1
            num_str += self.current_char
            self.advance()
        if dot_count == 0:
            return Token(TT_INT, int(num_str), pos=pos_start)
        return Token(TT_FLOAT, float(num_str), pos=pos_start)

    def make_identifier(self):
        id_str = ''
        pos_start = self.pos
        while self.current_char is not None and (self.current_char.isalnum() or self.current_char == '_'):
            id_str += self.current_char
            self.advance()
        tok_type = TT_KEYWORD if id_str in KEYWORDS else TT_ID
        return Token(tok_type, id_str, pos=pos_start)

    def make_equals(self):
        pos_start = self.pos
        self.advance()
        if self.current_char == '=':
            self.advance()
            return Token(TT_EE, pos=pos_start)
        return Token(TT_EQ, pos=pos_start)

# --- AST Nodes ---
class NumberNode:
    def __init__(self, tok):
        self.tok = tok
        self.pos = tok.pos
    def __repr__(self): return str(self.tok.value)

class VarAccessNode:
    def __init__(self, var_name_tok):
        self.var_name_tok = var_name_tok
        self.pos = var_name_tok.pos
    def __repr__(self): return str(self.var_name_tok.value)

class VarAssignNode:
    def __init__(self, var_name_tok, value_node):
        self.var_name_tok = var_name_tok
        self.value_node = value_node
        self.pos = var_name_tok.pos
    def __repr__(self): return f"(Assign {self.var_name_tok.value} = {self.value_node})"

class BinOpNode:
    def __init__(self, left_node, op_tok, right_node):
        self.left_node = left_node
        self.op_tok = op_tok
        self.right_node = right_node
        self.pos = op_tok.pos
    def __repr__(self): return f"({self.left_node} {self.op_tok.type} {self.right_node})"

class IfNode:
    def __init__(self, condition, then_stmt, else_stmt=None):
        self.condition = condition
        self.then_stmt = then_stmt
        self.else_stmt = else_stmt
        self.pos = condition.pos
    def __repr__(self): return f"(If {self.condition} Then {self.then_stmt} Else {self.else_stmt})"

class WhileNode:
    def __init__(self, condition, body_node):
        self.condition = condition
        self.body_node = body_node
        self.pos = condition.pos
    def __repr__(self): return f"(While {self.condition} Do {self.body_node})"

class PrintNode:
    def __init__(self, node):
        self.node = node
        self.pos = node.pos
    def __repr__(self): return f"(Print {self.node})"

class ListNode:
    def __init__(self, nodes):
        self.nodes = nodes
        self.pos = nodes[0].pos if nodes else 0
    def __repr__(self): return f"[ {', '.join(map(repr, self.nodes))} ]"

# --- Parser ---
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.tok_idx = -1
        self.advance()

    def advance(self):
        self.tok_idx += 1
        self.current_tok = self.tokens[self.tok_idx] if self.tok_idx < len(self.tokens) else None
        return self.current_tok

    def parse(self):
        res = self.statements()
        if self.current_tok.type != TT_EOF:
            raise InvalidSyntaxError(f"Unexpected token '{self.current_tok.type}'", self.current_tok.pos)
        return res

    def statements(self):
        statements = []
        while self.current_tok.type == TT_NEWLINE: self.advance()
        stmt = self.statement()
        if stmt: statements.append(stmt)
        while True:
            newline_count = 0
            while self.current_tok.type == TT_NEWLINE:
                self.advance()
                newline_count += 1
            if newline_count == 0: break
            stmt = self.statement()
            if not stmt: break
            statements.append(stmt)
        return ListNode(statements)

    def statement(self):
        if self.current_tok.type == TT_EOF: return None
        if self.current_tok.type == TT_KEYWORD:
            if self.current_tok.value == 'let':
                self.advance()
                if self.current_tok.type != TT_ID: raise InvalidSyntaxError("Expected identifier after 'let'", self.current_tok.pos)
                var_name = self.current_tok
                self.advance()
                if self.current_tok.type != TT_EQ: raise InvalidSyntaxError("Expected '='", self.current_tok.pos)
                self.advance()
                return VarAssignNode(var_name, self.expr())
            elif self.current_tok.value == 'print':
                self.advance()
                return PrintNode(self.expr())
            elif self.current_tok.value == 'if':
                return self.if_stmt()
            elif self.current_tok.value == 'while':
                self.advance()
                condition = self.expr()
                if self.current_tok.type != TT_KEYWORD or self.current_tok.value != 'do':
                    raise InvalidSyntaxError("Expected 'do'", self.current_tok.pos)
                self.advance()
                return WhileNode(condition, self.statement())

        if self.current_tok.type == TT_ID:
            if self.tok_idx + 1 < len(self.tokens) and self.tokens[self.tok_idx+1].type == TT_EQ:
                var_name = self.current_tok
                self.advance(); self.advance()
                return VarAssignNode(var_name, self.expr())
        return self.expr()

    def if_stmt(self):
        self.advance()
        condition = self.expr()
        if self.current_tok.value != 'then': raise InvalidSyntaxError("Expected 'then'", self.current_tok.pos)
        self.advance()
        then_stmt = self.statement()
        else_stmt = None
        if self.current_tok.value == 'else':
            self.advance()
            else_stmt = self.statement()
        return IfNode(condition, then_stmt, else_stmt)

    def expr(self):
        node = self.arith_expr()
        if self.current_tok.type in (TT_GT, TT_LT, TT_EE):
            op_tok = self.current_tok
            self.advance()
            node = BinOpNode(node, op_tok, self.arith_expr())
        return node

    def arith_expr(self): return self.bin_op(self.term, (TT_PLUS, TT_MINUS))
    def term(self): return self.bin_op(self.factor, (TT_MUL, TT_DIV))

    def factor(self):
        tok = self.current_tok
        if tok.type in (TT_INT, TT_FLOAT):
            self.advance(); return NumberNode(tok)
        elif tok.type == TT_ID:
            self.advance(); return VarAccessNode(tok)
        elif tok.type == TT_LPAREN:
            self.advance()
            expr = self.expr()
            if self.current_tok.type != TT_RPAREN: raise InvalidSyntaxError("Expected ')'", self.current_tok.pos)
            self.advance(); return expr
        elif tok.type in (TT_PLUS, TT_MINUS):
            self.advance(); return BinOpNode(NumberNode(Token(TT_INT, 0)), tok, self.factor())
        raise InvalidSyntaxError(f"Unexpected token '{tok.type}'", tok.pos)

    def bin_op(self, func, ops):
        left = func()
        while self.current_tok.type in ops:
            op_tok = self.current_tok
            self.advance()
            left = BinOpNode(left, op_tok, func())
        return left

# --- Interpreter ---
class Interpreter:
    def visit(self, node, env):
        method_name = f'visit_{type(node).__name__}'
        method = getattr(self, method_name, self.no_visit_method)
        return method(node, env)

    def no_visit_method(self, node, env):
        raise Exception(f'No visit_{type(node).__name__} method defined')

    def visit_NumberNode(self, node, env): return node.tok.value
    def visit_VarAccessNode(self, node, env):
        var_name = node.var_name_tok.value
        val = env.get(var_name)
        if val is None: raise RuntimeError(f"Variable '{var_name}' is not defined", node.pos)
        return val

    def visit_VarAssignNode(self, node, env):
        value = self.visit(node.value_node, env)
        env.set(node.var_name_tok.value, value)
        return None

    def visit_BinOpNode(self, node, env):
        left, right = self.visit(node.left_node, env), self.visit(node.right_node, env)
        if node.op_tok.type == TT_PLUS: return left + right
        if node.op_tok.type == TT_MINUS: return left - right
        if node.op_tok.type == TT_MUL: return left * right
        if node.op_tok.type == TT_DIV:
            if right == 0: raise RuntimeError("Division by zero", node.pos)
            return left / right
        if node.op_tok.type == TT_GT: return 1 if left > right else 0
        if node.op_tok.type == TT_LT: return 1 if left < right else 0
        if node.op_tok.type == TT_EE: return 1 if left == right else 0

    def visit_IfNode(self, node, env):
        condition_val = self.visit(node.condition, env)
        if condition_val:
            return self.visit(node.then_stmt, env)
        elif node.else_stmt:
            return self.visit(node.else_stmt, env)
        return None

    def visit_WhileNode(self, node, env):
        while self.visit(node.condition, env): self.visit(node.body_node, env)
        return None

    def visit_PrintNode(self, node, env):
        val = self.visit(node.node, env)
        print(val); return None

    def visit_ListNode(self, node, env):
        results = []
        for element in node.nodes: results.append(self.visit(element, env))
        return results

# --- Environment ---
class Environment:
    def __init__(self, parent=None):
        self.values = {}
        self.parent = parent
    def get(self, name):
        val = self.values.get(name)
        if val is not None: return val
        if self.parent: return self.parent.get(name)
        return None
    def set(self, name, value): self.values[name] = value
    def print_env(self):
        print("--- Environment Variables ---")
        for k, v in self.values.items(): print(f"{k}: {v}")
        print("-----------------------------")

# --- Runner ---
def run(text, env):
    try:
        lexer = Lexer(text)
        tokens = lexer.make_tokens()
        if DEBUG_MODE: print(f"DEBUG TOKENS: {tokens}")
        parser = Parser(tokens)
        ast = parser.parse()
        if DEBUG_MODE: print(f"DEBUG AST: {ast}")
        interpreter = Interpreter()
        return interpreter.visit(ast, env)
    except Error as e:
        print(e); return None
    except Exception as e:
        print(f"Internal Error: {e}"); return None

# --- Main REPL ---
if __name__ == "__main__":
    global_env = Environment()
    print("=== Mini Programming Language Interpreter ===")
    print("Commands: :debug (toggle), :env (show vars), exit")
    while True:
        try:
            lines = []
            while True:
                prompt = "mini-lang > " if not lines else "... "
                line = input(prompt)
                if line.strip() == "": break
                lines.append(line)
            text = "\n".join(lines)
            if not text.strip(): continue
            if text.strip() == "exit": break
            if text.strip() == ":debug":
                DEBUG_MODE = not DEBUG_MODE
                print(f"Debug Mode: {'ON' if DEBUG_MODE else 'OFF'}")
                continue
            if text.strip() == ":env":
                global_env.print_env(); continue
            
            result = run(text, global_env)
            if result is not None and isinstance(result, list) and len(result) > 0:
                last_val = result[-1]
                if last_val is not None and isinstance(last_val, (int, float)): print(last_val)
        except (EOFError, KeyboardInterrupt):
            print("\nExiting..."); break
