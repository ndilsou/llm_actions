from abc import ABC, abstractmethod
from typing import Any, ClassVar, TypeVar, Generic, Literal, Annotated
from typing import Never
from dataclasses import dataclass


from pydantic import BaseModel, Field, field_serializer


Record = dict[str, Any]
IGNORED = frozenset({"title", "description"})

S = TypeVar("S")
E = TypeVar("E")

class Result(BaseModel, ABC, Generic[S, E]):
    status: Literal["success", "failure"]

    def is_ok(self) -> bool:
        return self.status == "success"

    def is_err(self) -> bool:
        return self.status == "failure"

    @abstractmethod
    def unwrap(self) -> S:
        ...

    @abstractmethod
    def unwrap_err(self) -> E:
        ...
        
class Ok(Result[S, Never]):
    status: Literal["success"] = "success"
    result: S

    def unwrap(self) -> S:
        return self.result
    
    def unwrap_err(self) -> Never:
        raise ValueError("unwrap_err called on Ok")

def ok(result: S) -> Result[S, Never]:
    return Ok(result=result)
              


class Err(Result[Never, E]):
    status: Literal["failure"] = "failure"
    error: E = Field(exclude=True)
    @field_serializer('error')
    def serialize_error(self, error: E, _info):
        return {'message': str(error)}

    def unwrap(self) -> Never:
        raise ValueError("unwrap called on Err")
    
    def unwrap_err(self) -> E:
        return self.error

def err(error: E) -> Result[Never, E]:
    return Err(error=error)

# Result = Annotated[Ok[S] | Err[E],  Field(discriminator='status')]

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
        return self._do()

    @abstractmethod
    def _do(self) -> Result[S, E]:
        raise NotImplementedError

    async def ado(self) -> Result[S, E]:
        return await self._ado()

    @abstractmethod
    async def _ado(self) -> Result[S, E]:
        raise NotImplementedError


T = TypeVar("T", bound=BaseModel)


def map_functions(*args: ActionModel) -> dict[str, dict[str, Any]]:
    fns = (fn.openai_schema() for fn in args)
    return {fn["name"]: fn for fn in fns}


def list_functions(*args: ActionModel) -> list[Record]:
    return [fn.openai_schema() for fn in args]
