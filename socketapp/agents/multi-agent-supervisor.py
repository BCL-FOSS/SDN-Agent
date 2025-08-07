from typing import Annotated

from langchain_core.tools import tool

from typing import Literal
from typing_extensions import TypedDict

from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState, END
from langgraph.types import Command
import nest_asyncio
import logging
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits.openapi.toolkit import RequestsToolkit
from langchain_community.utilities.requests import TextRequestsWrapper
from typing import Any, Dict, Union
import requests
import yaml
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph_supervisor import create_supervisor
from langgraph.prebuilt import create_react_agent

logger = logging.getLogger(__name__)
memory = MemorySaver()

def _get_schema(response_json: Union[dict, list]) -> dict:
        if isinstance(response_json, list):
            response_json = response_json[0] if response_json else {}
        return {key: type(value).__name__ for key, value in response_json.items()}

def _get_api_spec() -> str:
        base_url = "https://jsonplaceholder.typicode.com"
        endpoints = [
            "/posts",
            "/comments",
        ]
        common_query_parameters = [
            {
                "name": "_limit",
                "in": "query",
                "required": False,
                "schema": {"type": "integer", "example": 2},
                "description": "Limit the number of results",
            }
        ]
        openapi_spec: Dict[str, Any] = {
            "openapi": "1.0.0",
            "info": {"title": "SDN Automation API", "version": "1.0.0"},
            "servers": [{"url": base_url}],
            "paths": {},
        }
        # Iterate over the endpoints to construct the paths
        for endpoint in endpoints:
            response = requests.get(base_url + endpoint)
            if response.status_code == 200:
                schema = _get_schema(response.json())
                openapi_spec["paths"][endpoint] = {
                    "get": {
                        "summary": f"Get {endpoint[1:]}",
                        "parameters": common_query_parameters,
                        "responses": {
                            "200": {
                                "description": "Successful response",
                                "content": {
                                    "application/json": {
                                        "schema": {"type": "object", "properties": schema}
                                    }
                                },
                            }
                        },
                    }
                }
        return yaml.dump(openapi_spec, sort_keys=False)

ALLOW_DANGEROUS_REQUEST = True

api_spec =_get_api_spec()

toolkit = RequestsToolkit(
                requests_wrapper=TextRequestsWrapper(headers={}),
                allow_dangerous_requests=ALLOW_DANGEROUS_REQUEST,
            )

tools = toolkit.get_tools()

llm = ChatOpenAI(model="gpt-3.5-turbo")

llm_config = {"configurable": {"thread_id": "1"}}

members = ["researcher", "coder"]
    # Our team supervisor is an LLM node. It just picks the next agent to process
    # and decides when the work is completed
options = members + ["FINISH"]

system_prompt = (
        "You are a supervisor tasked with managing a conversation between the"
        f" following workers: {members}. Given the following user request,"
        " respond with the worker to act next. Each worker will perform a"
        " task and respond with their results and status. When finished,"
        " respond with FINISH."
    )


class Router(TypedDict):
    """Worker to route to next. If no workers needed, route to FINISH."""

    next: Literal["monitor", "admin", "FINISH"]

class State(MessagesState):
    next: str


def supervisor_node(state: State) -> Command[Literal["monitor", "admin", "__end__"]]:
    messages = [
            {"role": "system", "content": system_prompt},
        ] + state["messages"]
    response = llm.with_structured_output(Router).invoke(messages)
    goto = response["next"]
    if goto == "FINISH":
            goto = END

    return Command(goto=goto, update={"next": goto})




monitor_agent = create_react_agent(
    llm, tools=[tools], prompt="You are a researcher. DO NOT do any math."
)


def monitor_node(state: State) -> Command[Literal["supervisor"]]:
    result = monitor_agent.invoke(state)
    return Command(
        update={
            "messages": [
                HumanMessage(content=result["messages"][-1].content, name="researcher")
            ]
        },
        goto="supervisor",
    )


# NOTE: THIS PERFORMS ARBITRARY CODE EXECUTION, WHICH CAN BE UNSAFE WHEN NOT SANDBOXED
admin_agent = create_react_agent(llm, tools=[python_repl_tool])


def admin_node(state: State) -> Command[Literal["supervisor"]]:
    result = admin_agent.invoke(state)
    return Command(
        update={
            "messages": [
                HumanMessage(content=result["messages"][-1].content, name="coder")
            ]
        },
        goto="supervisor",
    )


builder = StateGraph(State)
builder.add_edge(START, "supervisor")
builder.add_node("supervisor", supervisor_node)
builder.add_node("monitor", monitor_node)
builder.add_node("admin", admin_node)
graph = builder.compile()

