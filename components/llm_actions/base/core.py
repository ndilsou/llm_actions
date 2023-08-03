from abc import ABC, abstractmethod
from typing import Any, ClassVar, TypeVar, Generic, Literal, Annotated


from pydantic import BaseModel, Field


Record = dict[str, Any]
IGNORED = frozenset({"title", "description"})

S = TypeVar("S")

class Ok(BaseModel, Generic[S]):
    status: Literal["success"] = "success"
    result: S

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


class ActionModel(BaseModel, ABC, Generic[S, E]):
    _openai_schema: ClassVar[Record]

    @classmethod
    def openai_schema(cls) -> Record:
        if not hasattr(cls, "_openai_schema"):
            cls._openai_schema = _construct_openai_schema(cls.model_json_schema())

        return cls._openai_schema


    # openai_schema: ClassVar[Record] = property(_openai_schema_fn)

    @classmethod
    def openai_schema_name(cls) -> str:
        return cls.openai_schema()["name"]

    def do(self) -> Result[S, E]:
        ...

    @abstractmethod
    def _do(self) -> Result[S, E]:
        raise NotImplementedError

    async def ado(self) -> Result[S, E]:
        ...

    @abstractmethod
    async def _ado(self) -> Result[S, E]:
        raise NotImplementedError


T = TypeVar("T", bound=BaseModel)


def map_functions(*args: ActionModel) -> dict[str, dict[str, Any]]:
    fns = (fn.openai_schema() for fn in args)
    return {fn["name"]: fn for fn in fns}


def list_functions(*args: ActionModel) -> list[Record]:
    return [fn.openai_schema() for fn in args]
