"""Tool for asking human input."""

from typing import Callable, Optional

from pydantic import Field

from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain.tools.base import BaseTool
import requests

local_addr = "http://127.0.0.1:8000"
deploy_addr = "https://usecase2-agent.azurewebsites.net:8000"

addr = deploy_addr

def _print_func(text: str) -> None:
    print("\n")
    print(text)


def chat_input():
    res = ""

    while not res:
        reply = requests.get(f"{addr}/user", timeout=15).json()
        print(f"Reply: {reply}")
        res = reply['msg']

    print(f"Message: {res} received.")
    return res


class HumanInputRun(BaseTool):
    """Tool that asks user for input."""

    name = "human"
    description = (
        "You can ask a human for guidance when you think you "
        "got stuck or you are not sure what to do next. "
        "The input should be a question for the human."
    )
    prompt_func: Callable[[str], None] = Field(default_factory=lambda: _print_func)
    input_func: Callable = None

    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Use the Human input tool."""
        self.prompt_func(query)
        return chat_input()

    async def _arun(
        self,
        query: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        """Use the Human tool asynchronously."""
        raise NotImplementedError("Human tool does not support async")