def some_method_with_union_return(some_input: str | int) -> str | int:
    return some_input

def some_other_method() -> None:
    some_method_with_union_return(5)

def another_method() -> None:
    some_method_with_union_return("foo")
