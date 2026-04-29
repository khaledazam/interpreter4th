import sys

# --- Constants & Token Types ---
# We define the types of tokens our lexer will recognize.
TT_INT      = 'INT'
TT_FLOAT    = 'FLOAT'
TT_ID       = 'ID'
TT_KEYWORD  = 'KEYWORD'
TT_PLUS     = 'PLUS'
TT_MINUS    = 'MINUS'
TT_MUL      = 'MUL'
TT_DIV      = 'DIV'
TT_EQ       = 'EQ'       # = (Assignment)
TT_EE       = 'EE'       # == (Equality)
TT_GT       = 'GT'       # >
TT_LT       = 'LT'       # <
TT_LPAREN   = 'LPAREN'
TT_RPAREN   = 'RPAREN'
TT_EOF      = 'EOF'
TT_NEWLINE  = 'NEWLINE'

# Reserved words in our language
KEYWORDS = [
    'let',
    'if',
    'then',
    'else',
    'while',
    'do',
    'print'
]

# --- Token Class ---
# Represents a single unit of the source code (e.g., a number or a keyword).
class Token:
    def __init__(self, type_, value=None):
        self.type = type_
        self.value = value

    def __repr__(self):
        if self.value is not None: return f'{self.type}:{self.value}'
        return f'{self.type}'

# --- Lexer ---
# Scans the input text and converts it into a list of Tokens.
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
            if self.current_char in ' \t':
                self.advance()
            elif self.current_char in '\n;':
                tokens.append(Token(TT_NEWLINE))
                self.advance()
            elif self.current_char.isdigit():
                tokens.append(self.make_number())
            elif self.current_char.isalpha():
                tokens.append(self.make_identifier())
            elif self.current_char == '+':
                tokens.append(Token(TT_PLUS))
                self.advance()
            elif self.current_char == '-':
                tokens.append(Token(TT_MINUS))
                self.advance()
            elif self.current_char == '*':
                tokens.append(Token(TT_MUL))
                self.advance()
            elif self.current_char == '/':
                tokens.append(Token(TT_DIV))
                self.advance()
            elif self.current_char == '(':
                tokens.append(Token(TT_LPAREN))
                self.advance()
            elif self.current_char == ')':
                tokens.append(Token(TT_RPAREN))
                self.advance()
            elif self.current_char == '=':
                tokens.append(self.make_equals())
            elif self.current_char == '>':
                tokens.append(Token(TT_GT))
                self.advance()
            elif self.current_char == '<':
                tokens.append(Token(TT_LT))
                self.advance()
            else:
                char = self.current_char
                self.advance()
                raise Exception(f"Illegal character: '{char}'")

        tokens.append(Token(TT_EOF))
        return tokens

    def make_number(self):
        num_str = ''
        dot_count = 0
        while self.current_char is not None and (self.current_char.isdigit() or self.current_char == '.'):
            if self.current_char == '.':
                if dot_count == 1: break
                dot_count += 1
            num_str += self.current_char
            self.advance()

        if dot_count == 0:
            return Token(TT_INT, int(num_str))
        else:
            return Token(TT_FLOAT, float(num_str))

    def make_identifier(self):
        id_str = ''
        while self.current_char is not None and (self.current_char.isalnum() or self.current_char == '_'):
            id_str += self.current_char
            self.advance()
        
        tok_type = TT_KEYWORD if id_str in KEYWORDS else TT_ID
        return Token(tok_type, id_str)

    def make_equals(self):
        self.advance()
        if self.current_char == '=':
            self.advance()
            return Token(TT_EE)
        return Token(TT_EQ)

# --- AST Nodes ---
# Classes representing the nodes in our Abstract Syntax Tree.
class NumberNode:
    def __init__(self, tok):
        self.tok = tok
    def __repr__(self): return f'{self.tok}'

class VarAccessNode:
    def __init__(self, var_name_tok):
        self.var_name_tok = var_name_tok
    def __repr__(self): return f'{self.var_name_tok}'

class VarAssignNode:
    def __init__(self, var_name_tok, value_node):
        self.var_name_tok = var_name_tok
        self.value_node = value_node
    def __repr__(self): return f'(let {self.var_name_tok} = {self.value_node})'

class BinOpNode:
    def __init__(self, left_node, op_tok, right_node):
        self.left_node = left_node
        self.op_tok = op_tok
        self.right_node = right_node
    def __repr__(self): return f'({self.left_node} {self.op_tok} {self.right_node})'

class IfNode:
    def __init__(self, condition, then_stmt, else_stmt=None):
        self.condition = condition
        self.then_stmt = then_stmt
        self.else_stmt = else_stmt

class WhileNode:
    def __init__(self, condition, body_node):
        self.condition = condition
        self.body_node = body_node

class PrintNode:
    def __init__(self, node):
        self.node = node

class ListNode:
    def __init__(self, nodes):
        self.nodes = nodes

# --- Parser ---
# Converts the list of tokens into an AST based on the language grammar.
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.tok_idx = -1
        self.current_tok = None
        self.advance()

    def advance(self):
        self.tok_idx += 1
        self.current_tok = self.tokens[self.tok_idx] if self.tok_idx < len(self.tokens) else None
        return self.current_tok

    def parse(self):
        res = self.statements()
        if self.current_tok.type != TT_EOF:
            raise Exception("Expected EOF, but found " + str(self.current_tok))
        return res

    def statements(self):
        statements = []
        while self.current_tok.type == TT_NEWLINE:
            self.advance()

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
            # let <id> = <expr>
            if self.current_tok.value == 'let':
                self.advance()
                if self.current_tok.type != TT_ID: raise Exception("Expected identifier after 'let'")
                var_name = self.current_tok
                self.advance()
                if self.current_tok.type != TT_EQ: raise Exception("Expected '=' after identifier")
                self.advance()
                expr = self.expr()
                return VarAssignNode(var_name, expr)
            
            # print <expr>
            elif self.current_tok.value == 'print':
                self.advance()
                return PrintNode(self.expr())
            
            # if <expr> then <stmt> else <stmt>
            elif self.current_tok.value == 'if':
                return self.if_stmt()
            
            # while <expr> do <stmt>
            elif self.current_tok.value == 'while':
                self.advance()
                condition = self.expr()
                if self.current_tok.type != TT_KEYWORD or self.current_tok.value != 'do':
                    raise Exception("Expected 'do' after while condition")
                self.advance()
                body = self.statement()
                return WhileNode(condition, body)

        # Fallback to expression (e.g. x = 10 without let, or just an arithmetic expr)
        if self.current_tok.type == TT_ID:
            # Peek next to see if it is assignment
            if self.tok_idx + 1 < len(self.tokens) and self.tokens[self.tok_idx+1].type == TT_EQ:
                var_name = self.current_tok
                self.advance() # id
                self.advance() # =
                return VarAssignNode(var_name, self.expr())

        return self.expr()

    def if_stmt(self):
        self.advance() # skip 'if'
        condition = self.expr()
        if self.current_tok.type != TT_KEYWORD or self.current_tok.value != 'then':
            raise Exception("Expected 'then' after if condition")
        self.advance()
        then_stmt = self.statement()
        
        else_stmt = None
        if self.current_tok.type == TT_KEYWORD and self.current_tok.value == 'else':
            self.advance()
            else_stmt = self.statement()
            
        return IfNode(condition, then_stmt, else_stmt)

    def expr(self):
        # Comparison logic (e.g., > < ==)
        node = self.arith_expr()
        if self.current_tok.type in (TT_GT, TT_LT, TT_EE):
            op_tok = self.current_tok
            self.advance()
            right = self.arith_expr()
            node = BinOpNode(node, op_tok, right)
        return node

    def arith_expr(self):
        return self.bin_op(self.term, (TT_PLUS, TT_MINUS))

    def term(self):
        return self.bin_op(self.factor, (TT_MUL, TT_DIV))

    def factor(self):
        tok = self.current_tok
        if tok.type in (TT_INT, TT_FLOAT):
            self.advance()
            return NumberNode(tok)
        elif tok.type == TT_ID:
            self.advance()
            return VarAccessNode(tok)
        elif tok.type == TT_LPAREN:
            self.advance()
            expr = self.expr()
            if self.current_tok.type == TT_RPAREN:
                self.advance()
                return expr
            else:
                raise Exception("Expected ')'")
        elif tok.type in (TT_PLUS, TT_MINUS):
            # Unary operator support (simplified as 0 - factor)
            op_tok = self.current_tok
            self.advance()
            return BinOpNode(NumberNode(Token(TT_INT, 0)), op_tok, self.factor())
        
        raise Exception(f"Unexpected token: {tok}")

    def bin_op(self, func, ops):
        left = func()
        while self.current_tok.type in ops:
            op_tok = self.current_tok
            self.advance()
            right = func()
            left = BinOpNode(left, op_tok, right)
        return left

# --- Interpreter ---
# Traverses the AST and executes the program.
class Interpreter:
    def visit(self, node, env):
        method_name = f'visit_{type(node).__name__}'
        method = getattr(self, method_name, self.no_visit_method)
        return method(node, env)

    def no_visit_method(self, node, env):
        raise Exception(f'No visit_{type(node).__name__} method defined')

    def visit_NumberNode(self, node, env):
        return node.tok.value

    def visit_VarAccessNode(self, node, env):
        var_name = node.var_name_tok.value
        val = env.get(var_name)
        if val is None:
            raise Exception(f"Undefined variable: '{var_name}'")
        return val

    def visit_VarAssignNode(self, node, env):
        var_name = node.var_name_tok.value
        value = self.visit(node.value_node, env)
        env.set(var_name, value)
        return None

    def visit_BinOpNode(self, node, env):
        left = self.visit(node.left_node, env)
        right = self.visit(node.right_node, env)
        
        if node.op_tok.type == TT_PLUS: return left + right
        elif node.op_tok.type == TT_MINUS: return left - right
        elif node.op_tok.type == TT_MUL: return left * right
        elif node.op_tok.type == TT_DIV:
            if right == 0: raise Exception("Runtime Error: Division by zero")
            return left / right
        elif node.op_tok.type == TT_GT: return 1 if left > right else 0
        elif node.op_tok.type == TT_LT: return 1 if left < right else 0
        elif node.op_tok.type == TT_EE: return 1 if left == right else 0

    def visit_IfNode(self, node, env):
        condition = self.visit(node.condition, env)
        if condition:
            return self.visit(node.then_stmt, env)
        elif node.else_stmt:
            return self.visit(node.else_stmt, env)
        return None

    def visit_WhileNode(self, node, env):
        while self.visit(node.condition, env):
            self.visit(node.body_node, env)
        return None

    def visit_PrintNode(self, node, env):
        value = self.visit(node.node, env)
        print(value)
        return None

    def visit_ListNode(self, node, env):
        results = []
        for element in node.nodes:
            results.append(self.visit(element, env))
        return results

# --- Environment / Symbol Table ---
# Stores variable values and supports scoping (parent environments).
class Environment:
    def __init__(self, parent=None):
        self.values = {}
        self.parent = parent

    def get(self, name):
        val = self.values.get(name)
        if val is None and self.parent:
            return self.parent.get(name)
        return val

    def set(self, name, value):
        self.values[name] = value

# --- Runner ---
def run(text, env):
    try:
        # 1. Lexical Analysis
        lexer = Lexer(text)
        tokens = lexer.make_tokens()
        
        # 2. Parsing
        parser = Parser(tokens)
        ast = parser.parse()
        
        # 3. Interpretation
        interpreter = Interpreter()
        return interpreter.visit(ast, env)
    except Exception as e:
        print(f"Error: {e}")
        return None

# --- Main Entry Point ---
if __name__ == "__main__":
    global_env = Environment()
    
    # 5. Example Input Program
    example_program = """
let x = 10
let y = 20
let z = x + y

if z > 25 then print z else print x
"""
    
    print("=== Executing Example Program ===")
    print("Program Text:")
    print(example_program)
    print("Output:")
    run(example_program, global_env)
    
    # Bonus: REPL Mode
    print("\n=== REPL Mode (Type 'exit' or Ctrl+C to quit) ===")
    while True:
        try:
            text = input("mini-lang > ")
            if text.strip().lower() == 'exit': break
            if not text.strip(): continue
            
            result = run(text, global_env)
            
            # Show last expression result in REPL if it's not None
            if result is not None:
                if isinstance(result, list) and len(result) > 0:
                    last_val = result[-1]
                    # Print result if it's an expression (not None) and primitive
                    if last_val is not None and isinstance(last_val, (int, float)):
                        print(last_val)
        except EOFError:
            break
        except KeyboardInterrupt:
            print("\nExiting...")
            break
