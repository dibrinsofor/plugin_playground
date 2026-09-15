from __future__ import annotations

from collections.abc import Callable

from mypy.errorcodes import ErrorCode
from mypy.plugin import (
    FunctionBodyContext,
    FunctionBodyResult,
    FunctionDefContext,
    FunctionDefHookResult,
    Plugin,
)
from mypy.types import AnyType, TypeOfAny, UnionType, get_proper_type


UNION_RETURN = ErrorCode(
    code="union-return",
    description="Disallow union return annotations",
    category="General",
)

def inspect_function_definition(ctx: FunctionDefContext) -> FunctionDefHookResult | None:
    declared_return = get_proper_type(ctx.declared_signature.ret_type)
    if isinstance(declared_return, UnionType):
        ctx.api.fail(
            "Union return types are not allowed",
            ctx.definition,
            code=UNION_RETURN,
        )

    return None

class ElaborationPlugin(Plugin):
    def get_function_def_hook(
        self, fullname: str
    ) -> Callable[[FunctionDefContext], FunctionDefHookResult | None] | None:
        return inspect_function_definition


def plugin(version: str) -> type[ElaborationPlugin]:
    return ElaborationPlugin


