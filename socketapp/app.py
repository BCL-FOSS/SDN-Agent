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
import redis.asyncio as redis

ws_rate_limiter = WSRateLimiter(redis_host=os.environ.get('RATE_LIMIT_DB'), 
                                redis_port=os.environ.get('RATE_LIMIT_PORT'))

pubsub_redis=redis.from_url( 
                f"redis://{os.environ.get('AGENT_MSGS_DB')}:{os.environ.get('AGENT_MSGS_DB_PORT')}", 
                encoding="utf-8", decode_responses=True)
if pubsub_redis is None:
        logger.info(f'Redis connection to {os.environ.get('AGENT_MSGS_DB')} failed')
else:
        logger.info(f'Redis connection to {os.environ.get('AGENT_MSGS_DB')} succeeded.')
        pub_sub=pubsub_redis.pubsub()

client = OpenAI()

broker = Broker()

async def _receive() -> None:
    while True:
        message = await websocket.receive_json()
        parsed_message=json.loads(message)
        action=parsed_message['act']
        logger.debug(action)

        match action:
            case 'llm':
                resp = client.responses.create(
                        model="gpt-4.1",
                        tools=[
                            {
                                "type": "mcp",
                                "server_label": "dice_server",
                                "server_url": f"{parsed_message['url']}/mcp/",
                                "require_approval": "never",
                            },
                        ],
                        input=f"{parsed_message['msg']}",
                    )

                logger.debug(resp.output_text)
                msg_data = {
                        "from": "agent",
                        "msg": resp.output_text
                    }
                
                # Update chat stream with agent response in chat redis
                key=f'chat:{parsed_message['url']}:{parsed_message['eml']}'
                stream=f'stream:{key}'
                await pubsub_redis.lpush(key, json.dumps(msg_data))
                await pubsub_redis.publish(f"{stream}", json.dumps(msg_data))

                # Trigger frontend chat stream update
                ws_json= {"act":"rsp","url":{parsed_message['url']},"eml":{parsed_message['eml']}}
                await websocket.send(json.dumps(ws_json))

            case 'rsp':
                key=f'chat:{parsed_message['url']}:{parsed_message['eml']}'
                chat_stream=f'stream:{key}'

                # Sends all new user and agent repsonses to frontend via websocket
                await pub_sub.subscribe(chat_stream)
                new_message=await pub_sub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if new_message:
                    await broker.publish(message=new_message)

@app.route("/messages", methods=["POST"])
async def get_messages():
    """ Retrieve the chat history for selected user and connected AI agent """
    data = await request.get_json()
 
    key=f'chat:{data['url']}:{data['eml']}'
    messages = await pubsub_redis.lrange(key, 0, -1)
    messages = [json.loads(m) for m in reversed(messages)]  # oldest first
    return jsonify(messages)

@app.route("/send_message", methods=["POST"])
async def send_message():
    """Add new user messages to chat stream in redis and trigger agent response via websocket"""
    data = await request.get_json()
    msg_data = {
        "from": data["from"],
        "msg": data["msg"]
    }
 
    key=f'chat:{data['url']}:{data['eml']}'
    stream=f'stream:{key}'
    await pubsub_redis.lpush(key, json.dumps(msg_data))
    await pubsub_redis.publish(f"{stream}", json.dumps(msg_data))

    ws_json= {"act":"llm","url":{data['url']},"eml":{data['eml']}, "msg": data['msg']}
    await websocket.send(json.dumps(ws_json))
    return jsonify({"status": "ok"})
    
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
                    cl_sess_db = RedisDB(hostname=os.environ.get('CLIENT_SESS_DB'), 
                                                    port=os.environ.get('CLIENT_SESS_PORT'))
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
                    cl_auth_db = RedisDB(hostname=os.environ.get('CLIENT_AUTH_DB'), 
                                                    port=os.environ.get('CLIENT_AUTH_PORT'))
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