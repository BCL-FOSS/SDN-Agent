import nest_asyncio
import logging
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_community.agent_toolkits.openapi.toolkit import RequestsToolkit
from langchain_community.utilities.requests import TextRequestsWrapper
from typing import Any, Dict, Union
import requests
import yaml
from langgraph.checkpoint.memory import MemorySaver

class UBNT_AGNT():
    def __init__(self):
            # LLM Config
        memory = MemorySaver()

        ALLOW_DANGEROUS_REQUEST = True

        api_spec = self._get_api_spec()

        toolkit = RequestsToolkit(
            requests_wrapper=TextRequestsWrapper(headers={}),
            allow_dangerous_requests=ALLOW_DANGEROUS_REQUEST,
        )

        tools = toolkit.get_tools()

        llm = ChatOpenAI(model="gpt-3.5-turbo")

        self.llm_config = {"configurable": {"thread_id": "1"}}

        system_message = """
        You have access to an API to help answer user queries.
        Here is documentation on the API:
        {api_spec}
        """.format(api_spec=api_spec)

        self.agent_executor = create_react_agent(llm, tools, prompt=system_message, checkpointer=memory)
        self.logger = logging.getLogger(__name__)
        

    def _get_schema(self, response_json: Union[dict, list]) -> dict:
        if isinstance(response_json, list):
            response_json = response_json[0] if response_json else {}
        return {key: type(value).__name__ for key, value in response_json.items()}

    def _get_api_spec(self) -> str:
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
                schema = self._get_schema(response.json())
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
    
    