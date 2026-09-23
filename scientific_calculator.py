#!/usr/bin/env python3
"""
Scientific Calculator (command line)

Type expressions like:  sin(30) + 2^3 * sqrt(16)
Uses a safe AST-based evaluator (no eval()), so arbitrary code can't run.
"""

import ast
import math
import operator

HELP_TEXT = """
Operators : + - * / // % ^ (or **)   and parentheses ( )
Constants : pi, e, tau, ans (previous result)
Functions :
  Trig      sin cos tan asin acos atan sinh cosh tanh
  Powers    sqrt(x) cbrt(x) exp(x) pow(x, y)
  Logs      log(x) [base 10]  log(x, base)  ln(x)  log2(x)
  Other     abs floor ceil round fact(n) nCr(n, r) nPr(n, r) gcd(a, b)
  Convert   deg(x) [rad -> deg]   rad(x) [deg -> rad]

Commands  :
  mode deg | mode rad   switch angle mode (default: deg)
  help                  show this message
  quit / exit           leave the calculator
"""

BINARY_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

MAX_EXPONENT = 10_000  # guard against things like 9**9**9


class Calculator:
    def __init__(self):
        self.angle_mode = "deg"
        self.ans = 0
        self.functions = self._build_functions()

    # ---------- angle helpers ----------
    def _in(self, x):
        """Convert an input angle to radians."""
        return math.radians(x) if self.angle_mode == "deg" else x

    def _out(self, x):
        """Convert a result angle from radians to the current mode."""
        return math.degrees(x) if self.angle_mode == "deg" else x

    # ---------- function table ----------
    def _build_functions(self):
        def tan(x):
            if self.angle_mode == "deg" and x % 180 == 90:
                raise ValueError("tan is undefined at this angle")
            return math.tan(self._in(x))

        def fact(n):
            if n != int(n) or n < 0:
                raise ValueError("factorial needs a non-negative integer")
            return math.factorial(int(n))

        def log(x, base=10):
            return math.log(x, base)

        def ncr(n, r):
            return math.comb(int(n), int(r))

        def npr(n, r):
            return math.perm(int(n), int(r))

        return {
            "sin": lambda x: math.sin(self._in(x)),
            "cos": lambda x: math.cos(self._in(x)),
            "tan": tan,
            "asin": lambda x: self._out(math.asin(x)),
            "acos": lambda x: self._out(math.acos(x)),
            "atan": lambda x: self._out(math.atan(x)),
            "sinh": math.sinh,
            "cosh": math.cosh,
            "tanh": math.tanh,
            "sqrt": math.sqrt,
            "cbrt": lambda x: math.copysign(abs(x) ** (1 / 3), x),
            "exp": math.exp,
            "pow": pow,
            "log": log,
            "ln": math.log,
            "log2": math.log2,
            "abs": abs,
            "floor": math.floor,
            "ceil": math.ceil,
            "round": round,
            "fact": fact,
            "ncr": ncr,
            "npr": npr,
            "gcd": lambda a, b: math.gcd(int(a), int(b)),
            "deg": math.degrees,
            "rad": math.radians,
        }

    # ---------- evaluator ----------
    def evaluate(self, expression):
        expression = expression.strip().replace("^", "**")
        tree = ast.parse(expression, mode="eval")
        return self._eval(tree.body)

    def _eval(self, node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value

        if isinstance(node, ast.Name):
            name = node.id.lower()
            constants = {"pi": math.pi, "e": math.e, "tau": math.tau, "ans": self.ans}
            if name in constants:
                return constants[name]
            raise ValueError(f"unknown name '{node.id}'")

        if isinstance(node, ast.BinOp) and type(node.op) in BINARY_OPS:
            left, right = self._eval(node.left), self._eval(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > MAX_EXPONENT:
                raise ValueError("exponent too large")
            return BINARY_OPS[type(node.op)](left, right)

        if isinstance(node, ast.UnaryOp) and type(node.op) in UNARY_OPS:
            return UNARY_OPS[type(node.op)](self._eval(node.operand))

        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            name = node.func.id.lower()
            if name not in self.functions or node.keywords:
                raise ValueError(f"unknown function '{node.func.id}'")
            args = [self._eval(arg) for arg in node.args]
            return self.functions[name](*args)

        raise ValueError("unsupported expression")

    # ---------- output formatting ----------
    @staticmethod
    def format(value):
        if isinstance(value, complex):
            return str(value)
        if isinstance(value, float):
            if value.is_integer() and abs(value) < 1e15:
                return str(int(value))
            return f"{value:.12g}"
        return str(value)


def main():
    calc = Calculator()
    print("=== Scientific Calculator ===")
    print("Type 'help' for instructions, 'quit' to exit.")
    print(f"Angle mode: {calc.angle_mode}\n")

    while True:
        try:
            line = input(f"[{calc.angle_mode}] > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if not line:
            continue

        command = line.lower()
        if command in ("quit", "exit", "q"):
            print("Bye!")
            break
        if command == "help":
            print(HELP_TEXT)
            continue
        if command.startswith("mode"):
            parts = command.split()
            if len(parts) == 2 and parts[1] in ("deg", "rad"):
                calc.angle_mode = parts[1]
                print(f"Angle mode set to {parts[1]}")
            else:
                print("Usage: mode deg | mode rad")
            continue

        try:
            result = calc.evaluate(line)
            calc.ans = result
            print(f"= {calc.format(result)}")
        except ZeroDivisionError:
            print("Error: division by zero")
        except (ValueError, OverflowError) as err:
            print(f"Error: {err}")
        except (SyntaxError, TypeError):
            print("Error: invalid expression")


if __name__ == "__main__":
    main()
