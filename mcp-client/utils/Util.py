import uuid
import re
from wtforms.validators import ValidationError
import string
import random
import logging
import os
from pathlib import Path
import asyncio
import secrets
from quart import (send_file)
import shutil
import os
import uuid
from pathlib import Path
import zipfile
import aiohttp
from datetime import datetime, timedelta
import secrets
from zoneinfo import ZoneInfo
from tzlocal import get_localzone
import jwt


class Util:
    def __init__(self):
        self.umj_api_conn_session = aiohttp.ClientSession()
        self.logger = logging.getLogger(__name__)
        self.company_global_namespace = 'cmp:'
        self.company_data_global_namespace = 'dta:'
        self.user_global_namespace = 'usr:'
        self.user_id_global_namespace = 'uid:'
        self.public_email_domains = [
            "gmail.com",
            "yahoo.com",
            "hotmail.com",
            "outlook.com",
            "aol.com",
            "icloud.com",
            "protonmail.com",
            "zoho.com",
            "mail.com",
            "gmx.com"
        ]
        self.REDIS_INJECTION_REGEX = re.compile(
            r"(\b(?:eval|evalsha|config|flushall|flushdb|del|keys|rename|script|debug|monitor)\b|"
            r"['\"]\s*(?:\w+\s*[\|\&\;]\s*\w+|.+\*.+|[\|\&\;]))(?<!\bGET\b|\bSET\b)",
            re.IGNORECASE
        )
        self.CQL_INJECTION_REGEX = re.compile(
            r"(?i)(\bOR\b|\bAND\b)\s+\w+\s*=\s*\w+|(--|//|;|/\*|\*/)|'[^']*'|\"[^\"]*\"|\bSELECT\b.*\bFROM\b|\bINSERT\b.*\bINTO\b|\bUPDATE\b.*\bSET\b|\bDELETE\b.*\bFROM\b|\bDROP\b.*\bTABLE\b|\bTRUNCATE\b.*\bTABLE\b|\bBATCH\b.*\bAPPLY\b|\bUSE\b\s+\w+|\bALTER\b.*\bTABLE\b"
        )
        self.domain_pattern = r"@(?:" + "|".join(re.escape(domain) for domain in self.public_email_domains) + r")\b"

    def gen_id(self) -> str:
        return str(uuid.uuid4())
        
    def string_search_extraction(self, search_string="", start_chars='', end_chars=''):
        pattern = re.escape(start_chars) + r"(.*?)" + re.escape(end_chars)

        matches = re.findall(pattern, search_string)

        return matches
    
    def gen_company(self, company=""):
        company_key=self.key_gen(size=50)
        company_id = f'{self.company_global_namespace}{company}'
        company_tenant_id=f'{company_id}{company_key}'
        company_namespace = f'{company_id}{self.gen_id()}' 
        company_data_id = f'{company_namespace}:{self.company_data_global_namespace}{self.gen_id()}'
        
        return company_id, company_namespace, company_data_id, company_tenant_id

    def gen_user(self, email="", username=""):
        user_namespace = f'{self.user_global_namespace}{email}{self.gen_id()}'
        user_id = f'{self.user_id_global_namespace}{username}{self.gen_id()}'

        return user_namespace, user_id
    
    def form_input_validation(self, string_to_check=""):
        if not self.REDIS_INJECTION_REGEX.match(string_to_check or "") or not self.CQL_INJECTION_REGEX.match(string_to_check or ""):
            raise ValidationError("Invalid user input")
        else:
            self.logger.info('No DB Injection Found')

    def form_input_pblc_email_check(self, string_to_check=""):
        matches = re.findall(self.domain_pattern, string_to_check)
        return 1 if matches else None 
    
    def key_gen(self, size=6, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.SystemRandom().choice(chars) for _ in range(size))
    
    def generate_api_key(self) -> str:
        return str(uuid.uuid4())

    async def generate_probe_installer(self, probe_dir: str, installer_type: str):
        command = (
            f"chmod +x {probe_dir}/build_package.sh && {probe_dir}/build_package.sh {installer_type} && ls {probe_dir}/build"
            )
        process = await asyncio.create_subprocess_shell(
            command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()
    
        self.logger.error(stderr.decode())
        
        self.logger.info(stdout.decode())
        
        return_code = await process.wait()  
        
        self.logger.info(return_code) 

    def zip_installer(self, dest_dir):
        zip_name = "umj_prb_install.zip"
        zip_path = f"{dest_dir}/{zip_name}"

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(dest_dir):
                for file in files:
                    if '.pkg' or '.txz' or '.deb' or '.rpm' in file:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, dest_dir)
                        zipf.write(file_path, arcname)
                    else:
                        return None

        return zip_path, zip_name

    async def download_installer(self, dest_dir: str, prb_data_dir: str, install_type: str):

        shutil.copytree(src=prb_data_dir, dst=dest_dir)

        await self.generate_probe_installer(probe_dir=dest_dir, installer_type=install_type)
        
        zip_path, zip_name = self.zip_installer(dest_dir=dest_dir)
        
        return zip_path, zip_name if zip_path and zip_name else None
    
    async def make_async_request(self, cmd: str, url: str, payload: dict, headers={'Content-Type':'application/json'}):
        async with self.umj_api_conn_session as session:
            try:
                async with session.request(method=cmd, url=url, headers=headers, json=payload) as response:
                            if response.status == 200:
                                data = await response.json()
                                return data
                            else:
                                response.close()
                                return response.status
            except aiohttp.ClientError as e:
                response.close()
                return {"error": str(e), "status_code": 500}
            except Exception as error:
                response.close()
                return {"error": str(error)}
            finally:
                response.close()

    def generate_ephemeral_token(self, user_id: str, user_rand: str,  secret_key: str) -> str:

        local_tz = get_localzone()  
        now = datetime.now(local_tz)
        
        payload = {
            'iss': 'https://baughcl.com/',
            'id': user_id,
            'rand': user_rand,
            'exp': now + timedelta(hours=1),
        }

        encoded_jwt = jwt.encode(payload=payload, key=secret_key, algorithm="HS256")

        return encoded_jwt
   


    
        
        
        
        




