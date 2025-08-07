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

broker = Broker()

async def _receive() -> None:
    while True:
        message = await websocket.receive()
        async for event in  agent_executor.astream(
                {"messages": [("user", message)]},
                stream_mode="values",
                config=llm_config,
            ):
                response = event["messages"][-1].content
                await broker.publish(response)

@app.websocket("/chat")
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