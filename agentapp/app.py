from init_app import (app, admin_auth, client_auth, current_admin, current_client, logger,
                      Client, Admin
                      )
from forms.LoginForm import LoginForm
from forms.RegisterForm import RegisterForm
from forms.MCPConfigForm import MCPConfigForm
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
import shutil
import os
import uuid
from quart import Response
from aiofiles import open as aio_open
import aiofiles.os
import asyncio
from quart_rate_limiter import rate_exempt
import jwt

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

@app.route('/')
async def index():
    return await render_template("index/index.html")  

@app.route('/login', methods=['GET', 'POST'])
async def login():
    try:
        form = await LoginForm.create_form()

        if await form.validate_on_submit():
            email = form.email.data
            password = form.password.data

            email = email.replace(" ", "").lower()
            
            await cl_auth_db.connect_db()

            if await cl_auth_db.get_all_data(match=f'*{email}*', cnfrm=True) is True:
              
                account_data = await cl_auth_db.get_all_data(match=f'*{email}*')
                logger.info(account_data)
                sub_dict = next(iter(account_data.values()))
                logger.info(sub_dict)
                password_hash = sub_dict.get('pwd')
                
                if account_data and bcrypt.verify(password, password_hash):
                    logger.info(f'Account credentials verified for {email}')
                    # Assign session ID for authenticated account
                    session_id = util_obj.gen_id()

                    # Client sign in and account sess. data -> sess-redis
                    client_auth.login_user(Client(auth_id=session_id, action=Action.WRITE))

                    await cl_sess_db.connect_db()

                    # Pop password to mitigate potential leaks from redis session storage
                    sub_dict.pop('pwd')
                    #sub_dict['mcp_server'] = mcp_server
                    logger.info(sub_dict)
                        
                    if await cl_sess_db.upload_db_data(id=session_id, data=sub_dict) > 0:
                        company_id = sub_dict.get('cmp_id')
                        session['url_key'] = util_obj.key_gen(size=100)
                                
                        await flash(message=f'Account creation successful for {sub_dict.get('eml')}!', category='success')
                        return redirect(url_for('agent', cmp_id=company_id, obsc=session.get('url_key')))

                else:
                    logger.error(f'Authentication for {email} failed. Invalid password.')
                    await flash(message=f'Login failed for {email}. Invalid password.', category='danger')
                    return redirect(url_for('login'))
            else:
                await flash(message='Account does not exist.', category='danger')
                return redirect(url_for('register'))

        return await render_template('index/login.html', form=form)
    except Exception as e:
        logger.error( json.dumps({
            'status': 'error',
            'message': str(e)
        }), exc_info=True)

        return redirect(url_for('login'))
    
@app.route('/register', methods=['GET', 'POST'])
async def register():
    try:
        form = await RegisterForm.create_form()

        if await form.validate_on_submit():

            fname, lname = form.fname.data.replace(" ", "").lower(), form.lname.data.replace(" ", "").lower()
            email, company = form.email.data.replace(" ", "").lower(), form.company.data.replace(" ", "").lower()
            username, password = form.uname.data.replace(" ", "").lower(), form.password.data

            password_hash = bcrypt.hash(password)

            logger.info("Registering user: %s", email)

            user_nmp, user_id = util_obj.gen_user(email=email, username=username)

            user_obj = {
                "id": user_id,
                "fnm": fname,
                "lnm": lname,
                "eml": email,
                "cmp": company,
                "unm": username,
                "pwd": password_hash,
                "usr_jwt_secret": secrets.token_urlsafe(500),
                "usr_rand": secrets.token_urlsafe(500),
                "last_seen_id": None,
                "mcp_urls": []
            }

            logger.info(f"User ID: {user_obj['id']}")

            await cl_auth_db.connect_db()

            company_exist = await cl_auth_db.get_all_data(match=f'cmp:{company}*', cnfrm=True)

            if company_exist is False:
                company_id, company_nmp, company_data_id, company_tenant_id = util_obj.gen_company(company=company)
                cmp_obj = {"id": company_id, 
                           "tenant_id": company_tenant_id,
                           "name": company, 
                           "nmspce": company_nmp, 
                           "dt_id": company_data_id,
                           "cmp_jwt_secret": secrets.token_urlsafe(500),
                           "cmp_rand": secrets.token_urlsafe(500),
                           "sites": {"default": {}}
                           
                           }

                logger.info(f"Company ID: {cmp_obj['id']}")

                # key for new users
                user_key = f"{company_nmp}:{user_nmp}:{user_id}"

                # Upload company data
                if await cl_auth_db.upload_db_data(id=company_data_id, data=cmp_obj) > 0:
                    # Add company ID & name & tenant ID to user object
                    user_obj['cmp_id'] = company_nmp
                    user_obj['cmp'] = company_id
                    user_obj['cmp_jwt_secret'] = cmp_obj.get('cmp_jwt_secret')
                    user_obj['cmp_rand'] = cmp_obj.get('cmp_rand')
                    user_obj['cmp_dt_id'] = cmp_obj.get('dt_id')
                    user_obj['tnt_id'] = cmp_obj.get('tenant_id')
                    user_obj['db_id'] = user_key

                    logger.info(user_obj)

                    if await cl_auth_db.upload_db_data(id=f"{user_key}", data=user_obj) > 0:
                        await flash(message=f'Registration successful for {email}!', category='success')
                        return redirect(url_for('login'))
                else:
                    await flash(message=f'Registration falied for {email}. Try again.', category='danger')
                    return redirect(url_for('register'))
                
            if await cl_auth_db.get_all_data(match=f'*{email}*', cnfrm=True) is True:
                await flash(message=f'Account for {email} already exist!', category='danger')
                return redirect(url_for('login'))
            else:
                company_data = await cl_auth_db.get_all_data(match=f'cmp:{company}*')

                sub_dict = next(iter(company_data.values()))
                #logger.info(sub_dict.get('id'))
                company_id = sub_dict.get('id')
                company_tnt_id = sub_dict.get('tenant_id')
                company_namespace = sub_dict.get('nmpspce')

                #admin_exist = await cl_auth_db.get_all_data(match=f"adm-{company_namespace}*", cnfrm=True)

                # user key for current existing company
                user_key = f"{company_namespace}:{user_nmp}:{user_id}"

                logger.info(company_data)

                # Add company ID & name & tenant ID to user object
                user_obj['cmp_id'] = company_namespace
                user_obj['cmp'] = company_id
                user_obj['cmp_jwt_secret'] = sub_dict.get('cmp_jwt_secret')
                user_obj['cmp_rand'] = sub_dict.get('cmp_rand')
                user_obj['cmp_dt_id'] = sub_dict.get('dt_id')
                user_obj['tnt_id'] = company_tnt_id
                user_obj['db_id'] = user_key

                logger.info(user_obj)

                if await cl_auth_db.upload_db_data(id=f"{user_key}", data=user_obj) > 0:
                    await flash(message=f'Registration successful for {email}!', category='success')
                    return redirect(url_for('login'))

        return await render_template('index/register.html', form=form)

    except Exception as e:
        logger.error(json.dumps({'status': 'error', 'message': str(e)}), exc_info=True)
        return redirect(url_for('register'))

@app.route("/logout")
@user_login_required
async def logout():
    logout_user()

@app.route('/agent', defaults={'cmp_id': 'bcl','obsc': url_key}, methods=['GET', 'POST'])
@app.route("/agent/<string:cmp_id>/<string:obsc>", methods=['GET', 'POST'])
@user_login_required
async def agent(cmp_id, obsc):
    cur_usr_id = current_client.auth_id

    await cl_auth_db.connect_db()
    await cl_sess_db.connect_db()

    # Retrieve user session data
    cl_sess_data = await cl_sess_db.get_all_data(match=f"{cur_usr_id}")
    cl_sess_data_dict = next(iter(cl_sess_data.values()))
    logger.info(cl_sess_data_dict)

    # Retrieve user JWT secret key from client sess db
    usr_jwt_key = cl_sess_data_dict.get('usr_jwt_secret')
    user_rand = cl_sess_data_dict.get('usr_rand')

    # Generate user JWT to authenticate initial agent websocket connection
    usr_jwt_token = util_obj.generate_ephemeral_token(user_id=cur_usr_id, secret_key=usr_jwt_key, user_rand=user_rand)

    # URL for agent websocket connection initialization
    ws_url = f"ws://socketapp:4000/ws?token={usr_jwt_token}&id={cur_usr_id}&eml={cl_sess_data_dict.get('eml')}"

    return await render_template("app/agent.html", obsc_key=session.get('url_key'), ws_url=ws_url, cmp_id=cmp_id)

@app.route('/settings', defaults={'cmp_id': 'bcl','obsc': url_key}, methods=['GET', 'POST'])
@app.route("/settings/<string:cmp_id>/<string:obsc>", methods=['GET', 'POST'])
@user_login_required
async def settings(cmp_id, obsc):
    cur_usr_id = current_client.auth_id

    await cl_auth_db.connect_db()
    await cl_sess_db.connect_db()

    mcp_form = await MCPConfigForm.create_form()

    # Retrieve user session data
    cl_sess_data = await cl_sess_db.get_all_data(match=f"{cur_usr_id}")
    cl_sess_data_dict = next(iter(cl_sess_data.values()))
    logger.info(cl_sess_data_dict)

    # Probe installer instructions for user
    output = """
        AI is the future
        IT is Dead
        
        $ cd 
        $ sudo chmod +x run.sh
        $ echo "Usage: ./run.sh [--enroll | --unenroll | --start | --stop]"
        """

    data = {'fnm': cl_sess_data_dict.get('fnm'),
            'lnm': cl_sess_data_dict.get('lnm')}
    
    if await mcp_form.validate_on_submit():
        new_server=mcp_form.server.data

        if await cl_auth_db.get_all_data(match=f'*{cl_sess_data_dict.get('eml')}*', cnfrm=True) is True:
            new_urls=cl_sess_data_dict.get('mcp_urls')
            logger.info(new_urls)
            user_obj=new_urls.append(new_server)

            if await cl_auth_db.upload_db_data(id=f"{cl_sess_data_dict.get('db_id')}", data=user_obj) > 0:
                    await flash(message=f'Registration successful for {cl_sess_data_dict.get('eml')}!', category='success')

    return await render_template("app/settings.html", obsc_key=session.get('url_key'), cmp_id=cmp_id, data=data, code_output=output, mcp_form=mcp_form)

@app.errorhandler(Unauthorized)
async def redirect_to_login(*_):
    return redirect(url_for("login"))

@app.errorhandler(CSRFError)
async def handle_csrf_error(e):
    return await render_template('error/csrf_error.html', reason=e.description), 400

@app.errorhandler(401)
async def need_to_login():
    return await render_template("error/401.html"), 401


@app.errorhandler(404)
async def page_not_found():
    return await render_template("error/404.html"), 404

@app.errorhandler(500)
async def handle_internal_error(e):
    return await render_template_string(json.dumps({"error": "Internal server error"})), 500   