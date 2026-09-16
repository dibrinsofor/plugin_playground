import ast

BLOCKED_MODULES = {
    "os",
    "sys",
    "subprocess",
    "socket",
    "urllib",
    "http",
    "ftplib",
    "pathlib",
    "builtins",
}
ALLOWED_IMPORTS = {"mypy", "typing", "collections", "re", "abc", "__future__"}


def validate_plugin(code: str) -> None:
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        raise ValueError(f"Plugin syntax error: {e}")

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                if top in BLOCKED_MODULES:
                    raise ValueError(
                        f"Import of '{alias.name}' is not allowed in plugins"
                    )
                if top not in ALLOWED_IMPORTS:
                    raise ValueError(f"Unknown import '{alias.name}'")
        elif isinstance(node, ast.ImportFrom):
            top = node.module.split(".")[0] if node.module else ""
            if top in BLOCKED_MODULES:
                raise ValueError(f"Import from '{node.module}' is not allowed")
            if top not in ALLOWED_IMPORTS:
                raise ValueError(f"Unknown import '{node.module}'")
        elif isinstance(node, ast.Call):
            # Reject open(), exec(), eval(), __import__()
            if isinstance(node.func, ast.Name) and node.func.id in {
                "open",
                "exec",
                "eval",
                "compile",
                "__import__",
            }:
                raise ValueError(f"Call to '{node.func.id}' is not allowed")
