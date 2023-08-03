from abc import ABC
from typing import Any, ClassVar, TypeVar, Generic, Literal, Annotated


from pydantic import BaseModel, Field


Record = dict[str, Any]
IGNORED = frozenset({"title", "description"})

S = TypeVar("S")

class Ok(BaseModel, Generic[S]):
    status: Literal["success"] = "success"
    result: T

E = TypeVar("E")

class Err(BaseModel, Generic[E]):
    status: Literal["error"] = "error"
    error: E

Result = Annotated[Ok[S] | Err[E],  Field(discriminator='status')]

def _construct_openai_schema(schema: Record) -> Record:
    name = schema["title"]
    description = schema["description"]
    function_schema: Record = {
        "name": name,
        "description": description,
        "parameters": {k: v for k, v in schema.items() if k not in IGNORED},
    }

    prop: Record
    for prop in function_schema["parameters"]["properties"].values():
        prop = {k: v for k, v in prop.items() if k != "title"}

    return function_schema


class ActionModel(BaseModel, ABC):
    _openai_schema: ClassVar[Record]

    @classmethod
    def _openai_schema_fn(cls) -> Record:
        if not hasattr(cls, "_openai_schema"):
            cls._openai_schema = _construct_openai_schema(cls.model_json_schema())

        return cls._openai_schema


    openai_schema: ClassVar[Record] = property(_openai_schema_fn)

    @classmethod
    def openai_schema_name(cls) -> str:
        return cls._openai_schema_fn()["name"]


T = TypeVar("T", bound=BaseModel)


def map_functions(*args: ActionModel) -> dict[str, dict[str, Any]]:
    fns = (fn._openai_schema_fn() for fn in args)
    return {fn["name"]: fn for fn in fns}


def list_functions(*args: ActionModel) -> list[Record]:
    return [fn._openai_schema_fn() for fn in args]
