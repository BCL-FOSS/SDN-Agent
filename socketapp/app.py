from init_app import (app)
from quart import (websocket, render_template_string)
import asyncio
from utils.broker import Broker
from quart import request, jsonify, request
import json
from init_app import app, logger
from quart_rate_limiter import rate_exempt
import os
from utils.RedisDB import RedisDB
from quart import (websocket)
import asyncio
import jwt
import jwt
import json
from utils.WSRateLimiter import WSRateLimiter
from openai import OpenAI
import redis.asyncio as redis

# Session and Auth Redis DB init
cl_sess_db = RedisDB(hostname=os.environ.get('CLIENT_SESS_DB'), 
                                                    port=os.environ.get('CLIENT_SESS_DB_PORT'))
cl_auth_db = RedisDB(hostname=os.environ.get('CLIENT_AUTH_DB'), 
                                                    port=os.environ.get('CLIENT_AUTH_DB_PORT'))

# Websocket rate limit init
ws_rate_limiter = WSRateLimiter(redis_host=os.environ.get('RATE_LIMIT_DB'), 
                                redis_port=os.environ.get('RATE_LIMIT_DB_PORT'))

# Chat stream pubsub redis init
pubsub_redis=redis.from_url( 
                f"redis://{os.environ.get('AGENT_MSGS_DB')}:{os.environ.get('AGENT_MSGS_DB_PORT')}", 
                encoding="utf-8", decode_responses=True)
if pubsub_redis is None:
        logger.info(f'Redis connection to {os.environ.get('AGENT_MSGS_DB')} failed')
else:
        logger.info(f'Redis connection to {os.environ.get('AGENT_MSGS_DB')} succeeded.')
        pub_sub=pubsub_redis.pubsub()

mntr_url=os.environ.get('SERVER_NAME')

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
                                "server_url": f"{parsed_message['url']}",
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
                key=f'chat:{parsed_message['url']}:{parsed_message['usr']}'
                stream=f'stream:{key}'
                await pubsub_redis.lpush(key, json.dumps(msg_data))
                await pubsub_redis.publish(f"{stream}", json.dumps(msg_data))

                # Trigger frontend chat stream update
                ws_json= {"act":"rsp","url":{parsed_message['url']},"user":{parsed_message['usr']}}
                await websocket.send(json.dumps(ws_json))

            case 'rsp':
                key=f'chat:{parsed_message['url']}:{parsed_message['usr']}'
                chat_stream=f'stream:{key}'

                # Sends all new user and agent repsonses to frontend via websocket
                await pub_sub.subscribe(chat_stream)
                new_message=await pub_sub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if new_message:
                    await broker.publish(message=new_message)
            case 'urls':
                data = {'options': [f"https://{mntr_url}/ubnt/mcp", f"https://{mntr_url}/omada/mcp"]}
                await broker.publish(message=data)

@app.route("/messages", methods=["POST"])
async def messages():
    """ Retrieve the chat history for selected user and connected AI agent """
    logger.info(request.args)
    if request.args is not None:
        for key, value in websocket.args.items():
            match key:
                case 'token':
                    jwt_token = value
                case 'amp;id':
                    id = value
                case 'amp;unm':
                    user = value

    if user and id is not None or "":
                    
        await cl_auth_db.connect_db()
        await cl_sess_db.connect_db()

        if await cl_auth_db.get_all_data(match=f'*{user}*', cnfrm=True) and await cl_sess_db.get_all_data(match=f'{id}', cnfrm=True) is True:
                        
            account_data = await cl_auth_db.get_all_data(match=f'*{user}*')
            if account_data is None:
                return jsonify({"error": "Authentication Error"})
                            
            logger.info(account_data)
            sub_dict = next(iter(account_data.values()))
            logger.info(sub_dict)

            jwt_key = sub_dict.get('usr_jwt_secret')
            logger.info(jwt_key)
            decoded_token = jwt.decode(jwt=jwt_token, key=jwt_key , algorithms=["HS256"])
            logger.info(decoded_token)

            if decoded_token.get('rand') != sub_dict.get('usr_rand'):
                return jsonify({"error": "Authentication Error"})
            else:
                data = await request.get_json()
            
                key=f'chat:{data['mcpurl']}:{data['usr']}'
                messages = await pubsub_redis.lrange(key, 0, -1)
                messages = [json.loads(m) for m in reversed(messages)]  # oldest first
                return jsonify(messages)

@app.route("/send_message", methods=["POST"])
async def send_message():
    """Add new user messages to chat stream in redis and trigger agent response via websocket"""
    logger.info(request.args)
    if request.args is not None:
        for key, value in websocket.args.items():
            match key:
                case 'token':
                    jwt_token = value
                case 'amp;id':
                    id = value
                case 'amp;unm':
                    user = value

    if user and id is not None or "":
                    
        await cl_auth_db.connect_db()
        await cl_sess_db.connect_db()

        if await cl_auth_db.get_all_data(match=f'*{user}*', cnfrm=True) and await cl_sess_db.get_all_data(match=f'{id}', cnfrm=True) is True:
                        
            account_data = await cl_auth_db.get_all_data(match=f'*{user}*')
            if account_data is None:
                return jsonify({"error": "Authentication Error"})
                            
            logger.info(account_data)
            sub_dict = next(iter(account_data.values()))
            logger.info(sub_dict)

            jwt_key = sub_dict.get('usr_jwt_secret')
            logger.info(jwt_key)
            decoded_token = jwt.decode(jwt=jwt_token, key=jwt_key , algorithms=["HS256"])
            logger.info(decoded_token)

            if decoded_token.get('rand') != sub_dict.get('usr_rand'):
                return jsonify({"error": "Authentication Error"})
            else:
                data = await request.get_json()
                msg_data = {
                    "from": data["from"],
                    "msg": data["msg"]
                }
            
                key=f'chat:{data['url']}:{data['usr']}'
                stream=f'stream:{key}'
                await pubsub_redis.lpush(key, json.dumps(msg_data))
                await pubsub_redis.publish(f"{stream}", json.dumps(msg_data))

                ws_json= {"act":"llm","url":{data['url']},"usr":{data['usr']}, "msg": data['msg']}
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
                    case 'amp;unm':
                        user = value
                
            logger.info(jwt_token)
            logger.info(id)

            # Set rate limit check connection ID to the jwt used to initiate the connection
            client_connection = jwt_token

            # Rate limiter for websocket connections using user jwt tokens
            if await ws_rate_limiter.check_rate_limit(client_id=client_connection) is True:

                if user and id is not None or "":
                    
                    await cl_auth_db.connect_db()
                    await cl_sess_db.connect_db()

                    if await cl_auth_db.get_all_data(match=f'*{user}*', cnfrm=True) and await cl_sess_db.get_all_data(match=f'{id}', cnfrm=True) is True:
                        
                        account_data = await cl_auth_db.get_all_data(match=f'*{user}*')
                        if account_data is None:
                            await websocket.accept()
                            await websocket.close(1000)
                        else:
                            logger.info(account_data)
                            sub_dict = next(iter(account_data.values()))
                            logger.info(sub_dict)

                    jwt_key = sub_dict.get('usr_jwt_secret')
                    logger.info(jwt_key)
                    decoded_token = jwt.decode(jwt=jwt_token, key=jwt_key , algorithms=["HS256"])
                    logger.info(decoded_token)

                    if decoded_token.get('rand') == sub_dict.get('usr_rand'):
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

@app.errorhandler(401)
async def need_to_login():
    return await render_template_string(json.dumps({"error": "Authentication error"})), 401
    
@app.errorhandler(404)
async def page_not_found():
    return await render_template_string(json.dumps({"error": "Resource not found"})), 404

@app.errorhandler(500)
async def handle_internal_error(e):
    return await render_template_string(json.dumps({"error": "Internal server error"})), 500