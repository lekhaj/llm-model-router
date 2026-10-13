import ast
from pathlib import Path


def load_is_valid_json():
    source = Path("examples/simulated_demo.py").read_text()
    tree = ast.parse(source)
    function = next(
        node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "is_valid_json"
    )
    namespace = {"json": __import__("json")}
    exec(compile(ast.Module(body=[function], type_ignores=[]), "simulated_demo.py", "exec"), namespace)
    return namespace["is_valid_json"]


def test_is_valid_json_requires_summary_in_an_object():
    is_valid_json = load_is_valid_json()

    assert is_valid_json('{"summary": "caf\u00e9 \ud83c\udf1f"}')
    assert not is_valid_json('"summary"')
    assert not is_valid_json('["summary"]')
    assert not is_valid_json('')
