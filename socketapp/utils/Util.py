import uuid
import re
from wtforms.validators import ValidationError
import string
import random
from quart import flash
import logging
import os
import sys
from pathlib import Path
import subprocess
import asyncio
from quart import (flash, redirect, url_for)

class Util:
    def __init__(self):
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

    def gen_id(self):
        id = uuid.uuid4()
        if id:
            return str(id)
        else:
            return None
        
    def string_search_extraction(self, search_string="", start_chars='', end_chars=''):
        pattern = re.escape(start_chars) + r"(.*?)" + re.escape(end_chars)

        matches = re.findall(pattern, search_string)

        return matches
    
    def gen_company(self, company=""):
        company_id = f'{self.company_global_namespace}{company}'
        company_namespace = f'{company_id}{self.gen_id()}:' 
        company_data_id = f'{company_namespace}{self.company_data_global_namespace}{self.gen_id()}'
        
        return company_id, company_namespace, company_data_id

    def gen_user(self, email="", username=""):
        user_namespace = f'{self.user_global_namespace}{email}{self.gen_id()}:'
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
    
    def ansible_event_handler(self, data):
        self.logger.info(data)
                
    def get_ssh_public_key(self, username, key_type):
        home_dir = f"/home/{username}"
        ssh_dir = os.path.join(home_dir, ".ssh")
        #pub_key = os.path.join(home_dir, ".ssh", f"id_{key_type}.pub")
        #priv_key = os.path.join(home_dir, ".ssh", f"id_{key_type}")
        
        if not os.path.exists(home_dir):
            self.logger.error(f"Error: User '{username}' does not exist or does not have a home directory.")
            return None
        
        if not os.path.exists(ssh_dir):
            self.logger.error(f"Error: No SSH keys found for user '{username}' at {ssh_dir}.")
            return None

        main_path = Path(ssh_dir).rglob('*')
        if main_path:
            for file_path in main_path:
                with open(file_path, "r") as key_file:

                    if file_path.suffix == '.pub':
                        ssh_pub_key = key_file.read().strip()
                    ssh_priv_key = key_file.read().strip()

        self.logger.info(ssh_pub_key)
        self.logger.info(ssh_priv_key)
                
        return ssh_pub_key, ssh_priv_key
    
    async def install_unifi(self, host: str, user: str, password: str):
        command = (
            f"sshpass -p '{password}' ssh -tt -o StrictHostKeyChecking=no "
            f"{user}@{host} 'bash /usr/local/bin/ubnt-install.sh bcladmin@baughcl.com {host}'"
            # f"{user}@{host} 'echo {password} | sudo -S bash /usr/local/bin/ubnt-install.sh bcladmin@baughcl.com {host}'"
            )
        process = await asyncio.create_subprocess_shell(
            command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()
    
        self.logger.error(stderr.decode())
        
        self.logger.info(stdout.decode())
        
        return_code = await process.wait()  
        
        self.logger.info(return_code)
    
    async def config_unifi_ssl(self, host: str, user: str, password: str):
        command = (
            f"sshpass -p '{password}' ssh -tt -o StrictHostKeyChecking=no "
            f"{user}@{host} 'bash /usr/local/bin/ubnt-ssl-config.sh {host}'"
            # f"{user}@{host} 'echo {password} | sudo -S bash /usr/local/bin/ubnt-ssl-config.sh {host}'"
            )
        process = await asyncio.create_subprocess_shell(
            command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()
    
        self.logger.error(stderr.decode())
        
        self.logger.info(stdout.decode())
        
        return_code = await process.wait()  
        
        self.logger.info(return_code)
    
    async def ssh_connect(self, host: str, user: str, password: str):
        command = (
            f"sshpass -p '{password}' ssh -o StrictHostKeyChecking=accept-new "
            f"{user}@{host} 'hostname -f && cat /usr/local/bin/ubnt-install.sh && cat /usr/local/bin/ubnt-ssl-config.sh'"
            )
        process = await asyncio.create_subprocess_shell(
            command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()
    
        self.logger.error(stderr.decode())
        
        self.logger.info(stdout.decode())
        
        return_code = await process.wait()  
        
        self.logger.info(return_code) 
    
   


    
        
        
        
        




