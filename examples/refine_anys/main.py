from typing import Any

def do_thing(x: int) -> Any:
    return str(x)

reveal_type(do_thing(1))
value: int = do_thing(1)
