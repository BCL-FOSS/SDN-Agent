from init_app import (app, admin_auth, client_auth, current_admin, current_client, logger,
                      Client, Admin
                      )
from forms.LoginForm import LoginForm
from forms.RegisterForm import RegisterForm
from forms.ContactForm import ContactForm
from forms.SitesForm import SitesForm
from forms.SiteSelect import SiteSelect
from forms.OTPForm import OTPForm
from quart import (render_template_string, render_template, flash, redirect, url_for, session)
from quart_wtf.csrf import CSRFError
from quart_auth import (
    logout_user, Action
)
from quart_auth import Unauthorized
from functools import wraps
from utils.Util import Util
from utils.RedisDB import RedisDB
import json
import os
from passlib.hash import bcrypt
import secrets
from forms.APIKeyGenForm import APIKeyGenForm
from forms.ProbeConfigGenForm import ProbeConfigGenForm
import shutil
import os
import uuid
from quart import Response
from aiofiles import open as aio_open
import aiofiles.os

util_obj = Util()
url_key = util_obj.key_gen(size=100)

cl_auth_db = RedisDB(hostname=os.environ.get('REDIS_CLIENT_AUTH_DB'), 
                                 port=os.environ.get('REDIS_CLIENT_AUTH_PORT'))
            
cl_sess_db = RedisDB(hostname=os.environ.get('REDIS_CLIENT_SESS_DB'), 
                                 port=os.environ.get('REDIS_CLIENT_SESS_PORT'))

def admin_login_required(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        await cl_sess_db.connect_db()
        await cl_auth_db.connect_db()

        if current_admin.auth_id is not None and await cl_sess_db.get_all_data(match=f"{current_admin.auth_id}", cnfrm=True) is True: 
            admin_data = await cl_sess_db.get_all_data(match=f"{current_admin.auth_id}")
            admin_data_sub_dict = next(iter(admin_data.values()))

            if admin_data_sub_dict.get('adm_key') is not None or "".strip():
                if await cl_auth_db.get_all_data(match=f"{admin_data_sub_dict.get('db_id')}", cnfrm=True) is True:
                    admin_auth_data = await cl_auth_db.get_all_data(match=f"{admin_data_sub_dict.get('db_id')}")
                    admin_auth_data_sub_dict = next(iter(admin_auth_data.values()))

                    if admin_data_sub_dict.get('adm_key') == admin_auth_data_sub_dict.get('adm_key'):
                        return await app.ensure_async(func)(*args, **kwargs)
                    else:
                        return Unauthorized()
                else:
                    return Unauthorized()
            else:
                return Unauthorized()
        elif current_client.auth_id is not None and await cl_sess_db.get_all_data(match=f"{current_client.auth_id}", cnfrm=True) is True:
            user_data = await cl_sess_db.get_all_data(match=f"{current_client.auth_id}")
            user_data_sub_dict = next(iter(user_data.values()))
            if await cl_auth_db.get_all_data(match=f"{user_data_sub_dict.get('db_id')}", cnfrm=True) is True:
                await flash(message='Not authorized to access that resource. Contact your umjiniti administrator for assistance.')
                return redirect(url_for('hm', cmp_id=user_data_sub_dict.get('cmp_id'), obsc=session.get('url_key'), site=session.get('cur_site')))
        else:
            raise Unauthorized()
    return wrapper

def user_login_required(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        await cl_sess_db.connect_db()
        await cl_auth_db.connect_db()

        auth_id = current_client.auth_id

        if auth_id is not None or "".strip() and await cl_sess_db.get_all_data(match=f"{auth_id}", cnfrm=True) is True:

            return await app.ensure_async(func)(*args, **kwargs)
        else:
            return Unauthorized()
    return wrapper

@app.route('/favicon.ico')
async def favicon():
    return '', 204