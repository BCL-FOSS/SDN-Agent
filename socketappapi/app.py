from init_app import (app, logger)
from utils.Util import Util
from utils.UniFiNetAPI import UniFiNetAPI
from utils.RedisDB import RedisDB
from passlib.hash import bcrypt
from quart import request
import os

url_key = Util().key_gen(size=100)

util_obj=Util()

def get_token():
    token = request.headers.get("Authorization")
    if token and token.startswith("Bearer "):
        return token[7:]
    return None

@app.route('/ubnt_auth', defaults={'obsc': url_key}, methods=['POST'])
@app.route("/ubnt_auth/<string:obsc>", methods=['POST'])
async def ubnt_auth():
    if request.method == 'POST':
        token = request.headers.get("Authorization")
        api_user_company = request.headers.get("X-CMP-ID")
        api_user_email = request.headers.get("X-API-USER-EMAIL")
        if token and token.startswith("Bearer "):
            api_key = token[7:]
            cl_auth_db = RedisDB(hostname=os.environ.get('REDIS_CLIENT_AUTH_DB'), 
                                 port=os.environ.get('REDIS_CLIENT_AUTH_PORT'))
            
            await cl_auth_db.connect_db()

            if await cl_auth_db.get_all_data(match=f'usr:{api_user_email}*', cnfrm=True) is True:
                account_data = await cl_auth_db.get_all_data(match=f'usr:{api_user_email}*')
                logger.info(account_data)
                sub_dict = next(iter(account_data.values()))
                logger.info(sub_dict)
                api_key_hash = str(sub_dict.get('api_key'))

                if api_key_hash.strip() == "" or api_key_hash == None:
                    return 670
                
                if account_data and bcrypt.verify(api_key, api_key_hash):
                    logger.info(f'API key verified for {api_user_email}')
                    sub_dict.pop('pwd')
                    logger.info(sub_dict)
                    data_value = await request.get_json()
                    ubnt = UniFiNetAPI( is_udm=data_value['is_udm'], username=data_value['username'], 
                                       password=data_value['password'], controller_ip=data_value['ip'], 
                                       controller_port=data_value['port'])
                    
                    ubnt_response = await ubnt.authenticate()
                    logger.info(ubnt_response)
                else:
                    return 890
            else:
                return 750
