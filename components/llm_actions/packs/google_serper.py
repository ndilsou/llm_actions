"""Sleeping action pack. The pack contains simple actions that allow the agent to sleep for a specified amount of time."""

import asyncio
from datetime import timedelta
from time import sleep
from pydantic import Field, BaseModel

from llm_actions.base import Result, ok, ActionModel

class GoogleSearchResult(BaseModel):
    pass

class SearchGoogle(ActionModel[GoogleSearchResult, None]):
    """Pauses the program and sleep for a specified number of seconds."""

    duration: int | timedelta = Field(..., description="Time to sleep in seconds")

    def _do(self) -> Result[str, None]:
        duration: int
        if isinstance(self.duration, timedelta):
            duration = int(self.duration.total_seconds())
        else:
            duration = self.duration

        sleep(duration)
        return ok(f"Slept for {duration} seconds")
    
    async def _ado(self) -> Result[str, None]:
        duration: int
        if isinstance(self.duration, timedelta):
            duration = int(self.duration.total_seconds())
        else:
            duration = self.duration

        await asyncio.sleep(duration)
        return ok(f"Slept for {duration} seconds")
