import argparse
import re
import sys
from dataclasses import dataclass


class CompilerError(Exception):
    pass


@dataclass
class Token:
    type: str
    value: str
    position: int


# =========================================================
# PHASE 1: LEXER
# =========================================================


class Lexer:
    KEYWORDS = {"function": "FUNCTION", "return": "RETURN"}
    SYMBOLS = {
        "(": "LPAREN",
        ")": "RPAREN",
        "{": "LBRACE",
        "}": "RBRACE",
        ";": "SEMICOLON",
    }

    def __init__(self, code):
        self.code = code
        self.pos = 0

    def tokenize(self):
        tokens = []

        while self.pos < len(self.code):
            char = self.code[self.pos]

            if char.isspace():
                self.pos += 1
                continue

            if self.code.startswith("//", self.pos):
                self._skip_line_comment()
                continue

            if self.code.startswith("/*", self.pos):
                self._skip_block_comment()
                continue

            if char in self.SYMBOLS:
                tokens.append(Token(self.SYMBOLS[char], char, self.pos))
                self.pos += 1
                continue

            if char == "<":
                tokens.append(self._read_jsx())
                continue

            if char.isalpha() or char == "_":
                tokens.append(self._read_identifier_or_keyword())
                continue

            raise CompilerError(f"Unexpected character {char!r} at position {self.pos}")

        tokens.append(Token("EOF", "", self.pos))
        return tokens

    def _skip_line_comment(self):
        next_newline = self.code.find("\n", self.pos)
        self.pos = len(self.code) if next_newline == -1 else next_newline + 1

    def _skip_block_comment(self):
        end = self.code.find("*/", self.pos + 2)
        if end == -1:
            raise CompilerError("Unclosed block comment")
        self.pos = end + 2

    def _read_identifier_or_keyword(self):
        start = self.pos
        while self.pos < len(self.code) and (
            self.code[self.pos].isalnum() or self.code[self.pos] == "_"
        ):
            self.pos += 1

        value = self.code[start:self.pos]
        token_type = self.KEYWORDS.get(value, "IDENT")
        return Token(token_type, value, start)

    def _read_jsx(self):
        start = self.pos
        depth = 0
        root_tag = None

        while self.pos < len(self.code):
            if self.code[self.pos] != "<":
                self.pos += 1
                continue

            tag_end = self.code.find(">", self.pos)
            if tag_end == -1:
                raise CompilerError("Unclosed JSX tag")

            tag_text = self.code[self.pos : tag_end + 1]
            tag_name = self._tag_name(tag_text)

            if tag_name:
                if tag_text.startswith("</"):
                    depth -= 1
                    if depth < 0:
                        raise CompilerError(f"Unexpected closing JSX tag </{tag_name}>")
                    if depth == 0 and tag_name == root_tag:
                        self.pos = tag_end + 1
                        return Token("JSX", self.code[start:self.pos], start)
                elif not tag_text.endswith("/>"):
                    if depth == 0:
                        root_tag = tag_name
                    depth += 1

            self.pos = tag_end + 1

        raise CompilerError("Unclosed JSX expression")

    @staticmethod
    def _tag_name(tag_text):
        match = re.match(r"</?\s*([A-Za-z][A-Za-z0-9]*)", tag_text)
        return match.group(1) if match else None


# =========================================================
# PHASE 2: PARSER (AST)
# =========================================================


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current(self):
        return self.tokens[self.pos]

    def eat(self, token_type):
        token = self.current()
        if token.type != token_type:
            raise CompilerError(
                f"Expected {token_type}, found {token.type} ({token.value!r}) "
                f"at position {token.position}"
            )
        self.pos += 1
        return token

    def parse(self):
        ast = self.parse_function()
        self.eat("EOF")
        return ast

    def parse_function(self):
        self.eat("FUNCTION")
        name = self.eat("IDENT").value
        self.eat("LPAREN")
        self.eat("RPAREN")
        self.eat("LBRACE")
        self.eat("RETURN")

        if self.current().type == "LPAREN":
            self.eat("LPAREN")
            jsx = self.eat("JSX").value
            self.eat("RPAREN")
        else:
            jsx = self.eat("JSX").value

        if self.current().type == "SEMICOLON":
            self.eat("SEMICOLON")

        self.eat("RBRACE")

        return {
            "type": "Function",
            "name": name,
            "body": {"type": "JSX", "value": jsx},
        }


# =========================================================
# PHASE 3: SEMANTIC ANALYSIS
# =========================================================


class Semantic:
    HTML_TAGS = {
        "a",
        "article",
        "button",
        "div",
        "footer",
        "form",
        "h1",
        "h2",
        "h3",
        "header",
        "img",
        "input",
        "label",
        "li",
        "main",
        "nav",
        "ol",
        "p",
        "section",
        "span",
        "strong",
        "ul",
    }

    def check(self, ast):
        if ast["type"] != "Function":
            raise CompilerError("Only function components are supported")

        if not re.match(r"^[A-Z][A-Za-z0-9_]*$", ast["name"]):
            raise CompilerError("Component function name must start with a capital letter")

        jsx = ast["body"]["value"].strip()
        if not jsx:
            raise CompilerError("Empty return is not allowed")

        if "{" in jsx or "}" in jsx:
            raise CompilerError("JSX expressions like {name} are not supported in this subset")

        self._check_balanced_tags(jsx)
        return True

    def _check_balanced_tags(self, jsx):
        stack = []
        for tag in re.findall(r"<[^>]+>", jsx):
            tag_name = self._tag_name(tag)
            if not tag_name:
                continue
            if tag.startswith("</"):
                if not stack or stack[-1] != tag_name:
                    raise CompilerError(f"Mismatched closing tag </{tag_name}>")
                stack.pop()
            elif not tag.endswith("/>"):
                stack.append(tag_name)

        if stack:
            raise CompilerError(f"Unclosed JSX tag <{stack[-1]}>")

    @staticmethod
    def _tag_name(tag_text):
        match = re.match(r"</?\s*([A-Za-z][A-Za-z0-9]*)", tag_text)
        return match.group(1) if match else None
    HTML_TAGS = {
        "a",
        "article",
        "button",
        "div",
        "footer",
        "form",
        "h1",
        "h2",
        "h3",
        "header",
        "img",
        "input",
        "label",
        "li",
        "main",
        "nav",
        "ol",
        "p",
        "section",
        "span",
        "strong",
        "ul",
    }

    def check(self, ast):
        if ast["type"] != "Function":
            raise CompilerError("Only function components are supported")

        if not re.match(r"^[A-Z][A-Za-z0-9_]*$", ast["name"]):
            raise CompilerError("Component function name must start with a capital letter")

        jsx = ast["body"]["value"].strip()
        if not jsx:
            raise CompilerError("Empty return is not allowed")

        if "{" in jsx or "}" in jsx:
            raise CompilerError("JSX expressions like {name} are not supported in this subset")

        self._check_balanced_tags(jsx)
        return True

    def _check_balanced_tags(self, jsx):
        stack = []
        for tag in re.findall(r"<[^>]+>", jsx):
            tag_name = self._tag_name(tag)
            if not tag_name:
                continue
            if tag.startswith("</"):
                if not stack or stack[-1] != tag_name:
                    raise CompilerError(f"Mismatched closing tag </{tag_name}>")
                stack.pop()
            elif not tag.endswith("/>"):
                stack.append(tag_name)

        if stack:
            raise CompilerError(f"Unclosed JSX tag <{stack[-1]}>")

    @staticmethod
    def _tag_name(tag_text):
        match = re.match(r"</?\s*([A-Za-z][A-Za-z0-9]*)", tag_text)
        return match.group(1) if match else None


# =========================================================
# PHASE 4: IR GENERATION
# =========================================================


class IR:
    def generate(self, ast):
        return {
            "component": ast["name"],
            "template": ast["body"]["value"].strip(),
        }


# =========================================================
# PHASE 5: OPTIMIZER / JSX TO ANGULAR TEMPLATE
# =========================================================


class Optimizer:
    ATTRIBUTE_MAP = {
        "className": "class",
        "htmlFor": "for",
    }

    def optimize(self, ir):
        template = ir["template"]
        template = self._normalize_whitespace(template)
        template = self._convert_attributes(template)
        ir["template"] = template
        ir["selector"] = "app-" + self._to_kebab_case(ir["component"])
        return ir

    @staticmethod
    def _normalize_whitespace(template):
        template = re.sub(r"\s+", " ", template)
        template = re.sub(r">\s+<", "><", template)
        return template.strip()

    def _convert_attributes(self, template):
        for react_name, angular_name in self.ATTRIBUTE_MAP.items():
            template = re.sub(rf"\b{react_name}\s*=", f"{angular_name}=", template)
        return template

    @staticmethod
    def _to_kebab_case(name):
        return re.sub(r"(?<!^)([A-Z])", r"-\1", name).replace("_", "-").lower()

# =========================================================
# PHASE 6: ANGULAR CODE GENERATOR
# =========================================================


class AngularGenerator:
    def generate(self, ir):
        escaped_template = ir["template"].replace("`", "\\`")
        return f"""import {{ Component }} from '@angular/core';

@Component({{
  selector: '{ir["selector"]}',
  template: `{escaped_template}`
}})
export class {ir["component"]}Component {{}}
"""


# =========================================================
# COMPILER PIPELINE
# =========================================================


def compile_react_to_angular(code, verbose=True):
    if verbose:
        print("\n====================")
        print("SOURCE CODE")
        print("====================")
        print(code)

    lexer = Lexer(code)
    tokens = lexer.tokenize()

    if verbose:
        print("\n1. LEXICAL ANALYSIS")
        print([(token.type, token.value) for token in tokens if token.type != "EOF"])

    parser = Parser(tokens)
    ast = parser.parse()

    if verbose:
        print("\n2. SYNTAX ANALYSIS (AST)")
        print(ast)

    semantic = Semantic()
    semantic.check(ast)

    if verbose:
        print("\n3. SEMANTIC ANALYSIS PASSED")

    ir_gen = IR()
    ir = ir_gen.generate(ast)

    if verbose:
        print("\n4. INTERMEDIATE REPRESENTATION")
        print(ir)

    optimizer = Optimizer()
    optimized = optimizer.optimize(ir)

    if verbose:
        print("\n5. OPTIMIZED IR")
        print(optimized)

    generator = AngularGenerator()
    output = generator.generate(optimized)

    if verbose:
        print("\n6. ANGULAR OUTPUT")
        print(output)

    return output


def read_interactive_code():
    print("Paste React component code. Finish with a line containing only END:")
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == "END":
            break
        lines.append(line)
    return "\n".join(lines)


def build_arg_parser():
    parser = argparse.ArgumentParser(
        description="Compile a small subset of React function components to Angular components."
    )
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument("--code", help="React component source code")
    input_group.add_argument("--file", help="Path to a file containing React component source code")
    parser.add_argument("--output", "-o", help="Write generated Angular code to this file")
    parser.add_argument("--quiet", action="store_true", help="Only print the final Angular output")
    return parser


def main(argv=None):
    args = build_arg_parser().parse_args(argv)

    if args.code:
        code = args.code
    elif args.file:
        with open(args.file, "r", encoding="utf-8") as source_file:
            code = source_file.read()
    else:
        code = read_interactive_code()

    if not code.strip():
        print("No input code provided.", file=sys.stderr)
        return 1

    try:
        output = compile_react_to_angular(code, verbose=not args.quiet)
    except CompilerError as error:
        print(f"Compiler error: {error}", file=sys.stderr)
        return 1

    if args.output:
        with open(args.output, "w", encoding="utf-8") as output_file:
            output_file.write(output)
        print(f"Angular component written to {args.output}")
    elif args.quiet:
        print(output)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())