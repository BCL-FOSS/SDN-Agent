from quart import Quart
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
import secrets
from quart_wtf.csrf import CSRFProtect
import nest_asyncio
import logging
import os
from quart_rate_limiter import (RateLimiter, RateLimit, timedelta)
import logging

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
                },
                "post": {
                    "summary": f"Create a new {endpoint[1:]}",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "title": {"type": "string", "example": "My Title"},
                                        "body": {"type": "string", "example": "Post content"},
                                        "userId": {"type": "integer", "example": 1}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "Resource created",
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

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('passlib').setLevel(logging.ERROR)
logger = logging.getLogger(__name__)

app = Quart(__name__)
app.config.from_object("config")
# app.config['SECRET_KEY'] = secrets.token_urlsafe()
# app.config['SECURITY_PASSWORD_SALT'] = str(secrets.SystemRandom().getrandbits(128))

# Trust Proxy Headers (IMPORTANT for reverse proxy)
# app.config["PREFERRED_URL_SCHEME"] = "https"
# app.config["SERVER_NAME"] = os.environ.get('SERVER_NAME')
# app.config["WTF_CSRF_HEADERS"] = ["X-Forwarded-For", "X-Forwarded-Proto"]

# LLM Config
memory = MemorySaver()

ALLOW_DANGEROUS_REQUEST = True

api_spec = _get_api_spec()

toolkit = RequestsToolkit(
    requests_wrapper=TextRequestsWrapper(headers={}),
    allow_dangerous_requests=ALLOW_DANGEROUS_REQUEST,
)

tools = toolkit.get_tools()

llm = ChatOpenAI(model="gpt-3.5-turbo")

llm_config = {"configurable": {"thread_id": "1"}}

system_message = """
You have access to an API to help answer user queries.
Here is documentation on the API:
{api_spec}
""".format(api_spec=api_spec)

agent_executor = create_react_agent(llm, tools, prompt=system_message, checkpointer=memory)

RateLimiter(
    app,
    default_limits=[
        RateLimit(1, timedelta(seconds=1)),
        RateLimit(20, timedelta(minutes=1)),
    ],
)

nest_asyncio.apply()