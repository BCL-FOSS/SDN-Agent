from init_app import (app, agent_executor, llm_config)
from quart import (websocket)
import asyncio
from utils.broker import Broker
from quart import request, jsonify, request
import json
from init_app import app, logger
from quart_rate_limiter import rate_exempt
import os
import aiohttp
from utils.RedisDB import RedisDB
from quart import (websocket)
import asyncio
import jwt
from passlib.hash import bcrypt
import jwt
from collections import defaultdict
import json
from typing import Callable
from utils.WSRateLimiter import WSRateLimiter
from openai import OpenAI

ws_rate_limiter = WSRateLimiter(redis_host=os.environ.get('REDIS_RATE_LIMIT_DB'), 
                                redis_port=os.environ.get('REDIS_RATE_LIMIT_PORT'))

mcp_url = 'https://mcp.baughcl.tech/mcp'

client = OpenAI()

broker = Broker()

async def _receive() -> None:
    while True:
        message = await websocket.receive()
        if isinstance(message, dict) and message.items():
            action=message.get('act')

            match action:
                case 'llm':
                    resp = client.responses.create(
                        model="gpt-4.1",
                        tools=[
                            {
                                "type": "mcp",
                                "server_label": "dice_server",
                                "server_url": f"{url}/mcp/",
                                "require_approval": "never",
                            },
                        ],
                        input="Roll a few dice!",
                    )

                    print(resp.output_text)
                    await broker.publish(message=message)
                case 'mcp_cnfg':
                    mcp_url=message.get('mcp_url')

        
@app.websocket("/ws")
@rate_exempt
async def ws():
    try:
      
        logger.info(websocket.args)

        if websocket.args is not None:

            for key, value in websocket.args.items():
                match key:
                    case 'token':
                        jwt_token = value
                    case 'amp;id':
                        id = value
                    case 'amp;eml':
                        email = value
                
            logger.info(jwt_token)
            logger.info(id)

            # Set rate limit check connection ID to the jwt used to initiate the connection
            client_connection = jwt_token

            # Rate limiter for websocket connections using either probe or user jwt tokens
            if await ws_rate_limiter.check_rate_limit(client_id=client_connection) is True:

                if id is not None or "":
                    cl_sess_db = RedisDB(hostname=os.environ.get('REDIS_CLIENT_SESS_DB'), 
                                                    port=os.environ.get('REDIS_CLIENT_SESS_PORT'))
                    await cl_sess_db.connect_db()
                    cl_sess_data = await cl_sess_db.get_obj_data(key=id)

                    if cl_sess_data is None:
                        await websocket.accept()
                        await websocket.close(1000)

                    logger.info(cl_sess_data)
                    if cl_sess_data:
                        logger.info(cl_sess_data)
                        jwt_key = cl_sess_data.get('jwt_secret')
                        logger.info(jwt_key)
                        decoded_token = jwt.decode(jwt=jwt_token, key=jwt_key , algorithms=["HS256"])
                        logger.info(decoded_token)

                        if decoded_token.get('rand') == cl_sess_data.get('rand'):
                            logger.info('websocket authentication successful')
                            task = asyncio.ensure_future(_receive())
                            async for message in broker.subscribe():
                                await websocket.send(message)
                        else:
                            await websocket.accept()
                            await websocket.close(1000)

                if email is not None or "":
                    cl_auth_db = RedisDB(hostname=os.environ.get('REDIS_CLIENT_AUTH_DB'), 
                                                    port=os.environ.get('REDIS_CLIENT_AUTH_PORT'))
                    await cl_auth_db.connect_db()

                    if await cl_auth_db.get_all_data(match=f'usr:{email}*', cnfrm=True) is True:
                        account_data = await cl_auth_db.get_all_data(match=f'usr:{email}*')
                        logger.info(account_data)
                        sub_dict = next(iter(account_data.values()))
                        logger.info(sub_dict)

                    if account_data is None:
                        await websocket.accept()
                        await websocket.close(1000)

                    jwt_key = sub_dict.get('jwt_secret')
                    logger.info(jwt_key)
                    decoded_token = jwt.decode(jwt=jwt_token, key=jwt_key , algorithms=["HS256"])
                    logger.info(decoded_token)

                    if decoded_token.get('rand') == sub_dict.get('rand'):
                        logger.info('websocket authentication successful')
                        task = asyncio.ensure_future(_receive())
                        async for message in broker.subscribe():
                            await websocket.send(message)
                    else:
                        await websocket.accept()
                        await websocket.close(1000)

            else:
                await websocket.accept()
                await websocket.close(1000)
                return jsonify(error=f"Stream rate limit exceeded..."), 429
        else:
           await websocket.accept()
           await websocket.close(1000)

    except Exception as e:
        if task:
            task.cancel()
            await task
        await websocket.accept()
        await websocket.close(1000)
        raise e
    except asyncio.CancelledError:
        # Handle disconnection here
        if task:
            task.cancel()
            await task
        await websocket.accept()
        await websocket.close(1000)
        raise Exception(asyncio.CancelledError)
    finally:
        task.cancel()
        await task
        await websocket.accept()
        await websocket.close(1000)