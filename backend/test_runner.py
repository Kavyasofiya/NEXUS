
import ast


ALLOWED_NODES = (
    ast.Module,
    ast.FunctionDef,
    ast.arguments,
    ast.arg,
    ast.Return,

    # Variables and assignments
    ast.Assign,
    ast.AnnAssign,
    ast.AugAssign,
    ast.Name,
    ast.Load,
    ast.Store,

    # Constants and collections
    ast.Constant,
    ast.List,
    ast.ListComp,
    ast.Tuple,
    ast.Set,
    ast.Dict,
    ast.Subscript,
    ast.Slice,

    # Function calls and attributes
    ast.Call,
    ast.Attribute,
    ast.keyword,

    # Conditional statements
    ast.If,
    ast.IfExp,
    ast.UnaryOp,
    ast.Not,
    ast.Compare,
    ast.In,
    ast.NotIn,
    ast.Eq,  
    ast.NotEq,
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE,
    ast.BoolOp,
    ast.And,
    ast.Or,

    # Loops
    ast.For,
    ast.While,
    ast.comprehension,
    ast.Break,
    ast.Continue,

    # Arithmetic
    ast.BinOp,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.FloorDiv,
    ast.Mod,
    ast.Pow,
    ast.USub,
    ast.UAdd,

    # Exceptions
    ast.Raise,
)


ALLOWED_FUNCTIONS = {
    "max": max,
    "min": min,
    "len": len,
    "abs": abs,
    "sum": sum,
    "sorted": sorted,
    "set": set,
    "int": int,
    "str": str,
    "float": float,
    "range": range,
    "enumerate": enumerate,
    "reversed": reversed,
    "all": all,
    "any": any,
    "ValueError": ValueError,
}


ALLOWED_METHODS = {
    "join",
    "lower",
    "upper",
    "strip",
    "count",
}


def run_tests(code, test_cases):

    try:

        tree = ast.parse(code)

        functions = [
            node for node in tree.body
            if isinstance(node, ast.FunctionDef)
        ]

        if len(functions) != 1:
            return {
                "success": False,
                "message": "Exactly one function is required."
            }

        function = functions[0]

        # Determine the number of positional arguments.
        argument_count = (
            len(function.args.posonlyargs)
            + len(function.args.args)
        )

        for node in ast.walk(function):

            if not isinstance(node, ALLOWED_NODES):

                return {
                    "success": False,
                    "message": (
                        "Unsupported construct: "
                        + type(node).__name__
                    )
                }

            # Validate ordinary function calls.
            if isinstance(node, ast.Call):

                if isinstance(node.func, ast.Name):

                    if node.func.id not in ALLOWED_FUNCTIONS:

                        return {
                            "success": False,
                            "message": (
                                "Unsupported function: "
                                + node.func.id
                            )
                        }

                elif isinstance(node.func, ast.Attribute):

                    if node.func.attr not in ALLOWED_METHODS:

                        return {
                            "success": False,
                            "message": (
                                "Unsupported method: "
                                + node.func.attr
                            )
                        }

                else:

                    return {
                        "success": False,
                        "message": "Unsupported function call."
                    }

            # Validate exception types.
            if isinstance(node, ast.Raise):

                if not isinstance(node.exc, ast.Call):
                    return {
                        "success": False,
                        "message": "Unsupported exception."
                    }

                if not isinstance(node.exc.func, ast.Name):
                    return {
                        "success": False,
                        "message": "Unsupported exception type."
                    }

                if node.exc.func.id != "ValueError":
                    return {
                        "success": False,
                        "message": "Only ValueError is allowed."
                    }

        safe_module = ast.Module(
            body=[function],
            type_ignores=[]
        )

        compiled_code = compile(
            safe_module,
            "<nexus>",
            "exec"
        )

        namespace = {
            "__builtins__": {},
            **ALLOWED_FUNCTIONS
        }

        exec(compiled_code, namespace)

        tested_function = namespace[function.name]

        results = []

        for test in test_cases:

            try:

                input_data = test["input"]

                # Support both single-argument and
                # multiple-argument functions.
                if argument_count == 1:

                    actual = tested_function(input_data)

                else:

                    if not isinstance(input_data, (list, tuple)):
                        raise TypeError(
                            "Multiple function arguments must "
                            "be provided as a list or tuple."
                        )

                    if len(input_data) != argument_count:
                        raise ValueError(
                            f"Expected {argument_count} arguments, "
                            f"but received {len(input_data)}."
                        )

                    actual = tested_function(*input_data)

                passed = actual == test["expected"]

                results.append({
                    "input": input_data,
                    "expected": test["expected"],
                    "actual": actual,
                    "passed": passed
                })

            except Exception as error:

                results.append({
                    "input": test.get("input"),
                    "expected": test.get("expected"),
                    "actual": None,
                    "passed": False,
                    "error": str(error)
                })

        passed_count = sum(
            result["passed"] for result in results
        )

        total_count = len(results)

        return {
            "success": (
                total_count > 0
                and passed_count == total_count
            ),
            "total_tests": total_count,
            "passed": passed_count,
            "failed": total_count - passed_count,
            "results": results
        }

    except Exception as error:

        return {
            "success": False,
            "message": str(error)
        }
