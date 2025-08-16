import aiohttp
import uuid
import aiohttp
import manuf
import logging

vendor_lookup = manuf.MacParser()
error_codes = [460, 472, 489]

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('passlib').setLevel(logging.ERROR)

class UniFiNetAPI():

    def __init__(self, is_udm=False, **kwargs):
        self.base_url = f"https://{kwargs.get('controller_ip')}:{kwargs.get('controller_port')}"
        self.url = kwargs.get('controller_ip')
        self.inform_url = f"https://{kwargs.get('controller_ip')}:8080/inform"
        self.port = kwargs.get('controller_port')
        self.username = kwargs.get('username')
        self.password = kwargs.get('password')
        self.token = None
        self.is_udm = is_udm
        self.auth_check = False
        self.id = ''
        self.name = ''
        self.ubiquipy_client_session = aiohttp.ClientSession()
        self.url_string = f"{self.base_url}/api/s/" if self.is_udm else f"{self.base_url}/proxy/network/api/"
        self.logger = logging.getLogger(__name__)
        """
        if is_udm:
            self.url_string = f"{self.base_url}/api/"
        else:
            self.url_string = f"{self.base_url}/proxy/network/api/"
        """
        
    def get_profile_data(self):
        return {
            "id": self.id,
            "profile_name": self.name,
            "base_url": self.base_url,
            "url": self.url,
            "inform_url": self.inform_url,
            "port" : self.port,
            "username": self.username,
            "token": self.token,
            "is_udm" : self.is_udm
        }
    
    def gen_id(self):
        try:
            id = uuid.uuid4()
        except Exception as e:
            return {"status_msg": "ID Gen Failed",
                    "status_code": e}
        return str(id)
    
    async def make_async_request(self, cmd='', url='', payload={}):
        headers={
                    'Content-Type':'application/json',
                    'Cookie':self.token
                }
        async with self.ubiquipy_client_session as session:
            try:
                match cmd.strip():
                    case 'e':
                         
                        async with session.put(url=url, headers=headers, json=payload) as response:
                            if response.status == 200:
                                data = await response.json()
                                nested_data = data['data']
                                return data
                            else:
                                response.close()
                                return {"message": "Site DPI stat retrieval failed", "status_code": response.status}
                    
                    case 'p':
                       
                        async with session.post(url=url, headers=headers, json=payload) as response:
                            if response.status == 200:
                                data = await response.json()
                                nested_data = data['data']
                                return data
                            else:
                                response.close()
                                return {"message": "Site DPI stat retrieval failed", "status_code": response.status}

                    case 'g':
                        headers.pop('Content-Type')
                        async with session.get(url=url, headers=headers) as response:
                            if response.status == 200:
                                data = await response.json()
                                nested_data = data['data']
                                return data
                            else:
                                response.close()
                                return {"message": "Site DPI stat retrieval failed", "status_code": response.status}
            except aiohttp.ClientError as e:
                response.close()
                return {"error": str(e), "status_code": 500}
            except Exception as error:
                response.close()
                return {"error": str(error)}
            finally:
                response.close()
            
    async def authenticate(self):

        if self.is_udm is True:
            auth_url = f"{self.base_url}/proxy/network/api/auth/login"
        else:
            auth_url = f"{self.base_url}/api/login"

        payload = {"username": self.username, "password": self.password}

        async with self.ubiquipy_client_session as session:
            try:
                # Asynchronous POST request to UniFi API
                async with session.post(url=auth_url, json=payload) as response:
                    if response.status == 200:
                        #response_data = await response.json()
                        header_data = response.headers.getall('Set-Cookie', [])
                        for cookie in header_data:
                            if 'unifises' in cookie:
                               unifises_token = cookie.split(';')[0].split('=')[1]
                            if 'csrf_token' in cookie:
                                csrf_token = cookie.split(';')[0].split('=')[1]

                        unifises = str(unifises_token)
                        #self.logger.debug(unifises)
                        csrf = str(csrf_token)
                        #self.logger.debug(csrf)
                        session_token = "unifises="+unifises + ";"+ "csrf_token="+csrf + ";"
                        self.token = session_token
                        self.id = self.gen_id()
                        self.auth_check = True
                        response.close()
                        #self.logger.debug({"message": "Authentication successful", "data": response_data, "token": session_token, "id": self.id})
                        return self.get_profile_data()
                    else:
                        response.close()
                        return {"message": "Authentication failed", "status_code": response.status}
            except aiohttp.ClientError as e:
                response.close()
                return {"error": str(e), "status_code": 500}
            except Exception as error:
                response.close()
                return {"error": str(error)}

    async def sign_out(self):
        url = f"{self.url_string}/logout"

        payload={"":""} 
        
        response = await self.make_async_request(url=url, payload=payload, cmd='p')

        self.ubiquipy_client_session.close()

        return response
            
    async def site_dpi_data(self, site='', type=False, cmd=''):

        url = f"{self.url_string}/s/{site}/stat/sitedpi"

        if type is False:
            payload = {'type': 'by_app'}
        else:
            payload = {'type': 'by_cat'}

        match cmd.strip():
            case 'p':

                response = await self.make_async_request(url=url, payload=payload, cmd=cmd)

                return response
                    
            case 'g':

                response = await self.make_async_request(url=url, cmd=cmd)

                return response    

    async def client_dpi_data(self, site='', type=False, macs=[]):

        if type is False and macs != []:
            payload = {'type': 'by_app',
                       'macs': macs}
        elif type is True and macs != []:
            payload = {'type': 'by_cat',
                       'macs': macs}
        elif type is False:
            payload = {'type': 'by_app'}
        else:
            payload = {'type': 'by_cat'}

        url = f"{self.url_string}/s/{site}/stat/stadpi"
        
        response = await self.make_async_request(url=url, payload=payload, cmd='p')

        #nested_data = response['data']

        return response

    async def event_data(self, site=''):

        url = f"{self.url_string}/s/{site}/stat/event"
        
        response = await self.make_async_request(url=url, cmd='g')

        #nested_data = response['data']

        return response

    async def alarm_data(self, site=''):

        url = f"{self.url_string}/s/{site}/stat/alarm"

        response = await self.make_async_request(url=url, cmd='g')

        #nested_data = response['data']

        return response 

    async def controller_health_data(self):

        url = f"{self.url_string}/s/default/stat/health"

        response = await self.make_async_request(url=url, cmd='g')

        #nested_data = response['data']

        return response

    async def site_stats(self):

        url = f"{self.url_string}/stat/sites"

        response = await self.make_async_request(url=url, cmd='g')

        #nested_data = response['data']

        return response

    async def sites(self):

        url = f"{self.url_string}/self/sites"

        response = await self.make_async_request(url=url, cmd='g')

        #nested_data = response['data']

        return response

    async def list_admins(self):

        url = f"{self.url_string}/stat/admin"

        response = await self.make_async_request(url=url, cmd='g')

        #nested_data = response['data']

        return response

    async def udm_poweroff(self):

        
        if self.is_udm is True:

            url = f"{self.url_string}/system/poweroff"

        else:
            return {"Controller Compatability Error":"This command does not work with self hosted controllers. Please reinitialize the object with is_udm=True and set the URL as the IP address of the UDM or hardware Cloud Gateway"}
        
        payload = {"":""}

        response = await self.make_async_request(url=url, payload=payload, cmd='p')

        #nested_data = response['data']

        return response

    async def udm_reboot(self):

        if self.is_udm is True:

            url = f"{self.url_string}/system/reboot"

        else:
            return {"Controller Compatability Error":"This command does not work with self hosted controllers. Please reinitialize the object with is_udm=True and set the URL as the IP address of the UDM or hardware Cloud Gateway"}

        payload = {"":""}

        response = await self.make_async_request(url=url, payload=payload, cmd='p')

        #nested_data = response['data']

        return response

    async def get_sysinfo(self):

        url = f"{self.url_string}/s/default/stat/sysinfo"

        response = await self.make_async_request(url=url, cmd='g')

        #nested_data = response['data']

        return response

    async def active_clients(self, site=''):

        url = f"{self.url_string}/s/{site}/stat/sta"

        response = await self.make_async_request(url=url, cmd='g')

        #nested_data = response['data']

        return response

    async def all_clients(self, site=''):

        url = f"{self.url_string}/s/{site}/rest/user"

        response = await self.make_async_request(url=url, cmd='g')

        #nested_data = response['data']

        return response

    async def device_data_basic(self, site=''):

        url = f"{self.url_string}/s/{site}/stat/device-basic"

        response = await self.make_async_request(url=url, cmd='g')

        #nested_data = response['data']

        return response

    async def device_data(self, macs=[], site=''):

        url = f"{self.url_string}/s/{site}/stat/device"

        if self.is_udm is False and macs != []: 
            payload = {'macs': macs} 

            response = await self.make_async_request(url=url, payload=payload, cmd='p')

            #nested_data = response['data']

            return response
                    
        else:
            response = await self.make_async_request(url=url, cmd='g')

            #nested_data = response['data']

            return response

    async def site_settings(self, key='', id='', cmd='', site=''):

        if key and id != '':
            url = f"{self.url_string}/s/{site}/rest/setting/{key}/{id}"
        else:
            url = f"{self.url_string}/s/{site}/rest/setting"

        match cmd.strip():
            case 'e':
                payload = {'': ''}
                response = await self.make_async_request(url=url, payload=payload, cmd='e')

                #nested_data = response['data']

                return response
                       
            case 'g':

                response = await self.make_async_request(url=url, cmd='g')

                #nested_data = response['data']

                return response

    async def active_routes(self, site=''):

        url = f"{self.url_string}/s/{site}/stat/routing"

        response = await self.make_async_request(url=url, cmd='g')

        #nested_data = response['data']

        return response

    async def firewall_rules(self, cmd='', site=''):

        url = f"{self.url_string}/s/{site}/rest/firewallrule"

        match cmd.strip():
            case 'e':
                payload = {'': ''}
                response = await self.make_async_request(url=url, payload=payload, cmd='e')

                #nested_data = response['data']

                return response
                       
            case 'g':

                response = await self.make_async_request(url=url, cmd='g')

                #nested_data = response['data']

                return response

    async def firewall_groups(self, cmd='', site=''):

        url = f"{self.url_string}/s/{site}/rest/firewallgroup"

        match cmd.strip():
            case 'e':
                payload = {'': ''}
                response = await self.make_async_request(url=url, payload=payload, cmd='e')

                #nested_data = response['data']

                return response
                       
            case 'g':

                response = await self.make_async_request(url=url, cmd='g')

                #nested_data = response['data']

                return response

    async def wlans(self, wlan_name='', psswd='', site_id='', wlan_id='', cmd='', site=''):

        payload = {
                "name": wlan_name,
                "password": psswd,
                "site_id": site_id,
                "usergroup_id": "660e8cf02260b651d2585910",
                "ap_group_ids": [
                    "660e8cf02260b651d2585914"
                ],
                "ap_group_mode": "all",
                "wpa_mode": "wpa2",
                "x_passphrase": psswd
            }
        
        

        match cmd.strip():
            case 'e':

                    url = f"{self.url_string}/s/{site}/rest/wlanconf/{wlan_id}"

                    response = await self.make_async_request(url=url, payload=payload, cmd=cmd)

                    #nested_data = response['data']

                    return response
                            
            case 'p':

                    url = f"{self.url_string}/s/{site}/rest/wlanconfs"

                    response = await self.make_async_request(url=url, payload=payload, cmd=cmd)

                    #nested_data = response['data']

                    return response

            case 'g':

                    url = f"{self.url_string}/s/{site}/rest/wlanconfs"

                    response = await self.make_async_request(url=url, cmd=cmd)

                    #nested_data = response['data']

                    return response

    async def rogue_aps(self, seen_last=0, site=''):   

        url = f"{self.url_string}/s/{site}/stat/rogueap"
        
        if seen_last != 0: 
                    
            payload = {'within': seen_last}

            response = await self.make_async_request(url=url, payload=payload, cmd='p')

            #nested_data = response['data']

            return response

        else:
            
            response = await self.make_async_request(url=url, payload=payload, cmd='g')

            #nested_data = response['data']

            return response

    async def dynamic_dns_info(self, site=''):

        url = f"{self.url_string}/s/{site}/stat/dynamicdns"

        response = await self.make_async_request(url=url, cmd='g')

        #nested_data = response['data']

        return response

    async def dynamic_dns_config(self, cmd='', site=''):

        url = f"{self.url_string}/s/{site}/rest/dynamicdns"

        match cmd.split():
            case 'e':
                payload = {'': ''}

                response = await self.make_async_request(url=url, payload=payload, cmd='e')

                #nested_data = response['data']

                return response

            case 'g':
                response = await self.make_async_request(url=url, cmd='g')

                #nested_data = response['data']

                return response

    async def list_port_profiles(self, site=''):

        url = f"{self.url_string}/s/{site}/rest/portconf"

        response = await self.make_async_request(url=url, cmd='g')

        #nested_data = response['data']

        return response

    async def rf_scan_results(self, mac='', cmd='', site=''):
        payload = {'': ''}

        

        match cmd.strip():
                case 's':

                    url = f"{self.url_string}/s/{site}/stat/spectrumscan/{mac}"

                    response = await self.make_async_request(url=url, cmd='g')

                    #nested_data = response['data']

                    return response

                case 'g':

                    url = f"{self.url_string}/s/{site}/stat/spectrumscan"

                    response = await self.make_async_request(url=url, cmd='g')

                    #nested_data = response['data']

                    return response

    async def radius_profiles(self, cmd='', site=''):

        url = f"{self.url_string}/s/{site}/rest/radiusprofile"

        match cmd.strip():
            case 'e':
                payload = {'': ''}

                response = await self.make_async_request(url=url, payload=payload, cmd=cmd)

                #nested_data = response['data']

                return response
                       
            case 'p':
                payload = {'': ''}

                response = await self.make_async_request(url=url, payload=payload, cmd=cmd)

                #nested_data = response['data']

                return response
                       
            case 'g':

                response = await self.make_async_request(url=url, payload=payload, cmd=cmd)

                #nested_data = response['data']

                return response

    async def radius_accounts(self, cmd='', site=''):

        url = f"{self.url_string}/s/{site}/rest/account"

        match cmd.strip():
            case 'e':
                payload = {'': ''}

                response = await self.make_async_request(url=url, payload=payload, cmd=cmd)

                #nested_data = response['data']

                return response
                       
            case 'p':
                payload = {'': ''}

                response = await self.make_async_request(url=url, payload=payload, cmd=cmd)

                #nested_data = response['data']

                return response
                       
            case 'g':

                response = await self.make_async_request(url=url, payload=payload, cmd=cmd)

                #nested_data = response['data']

                return response

    async def port_forwards(self, site=''):

        url = f"{self.url_string}/s/{site}/rest/portforward"

        response = await self.make_async_request(url=url, cmd='g')

        #nested_data = response['data']

        return response

    async def reports(self, interval='5', type='site', returned_data='bytes', macs=[], site='' ):

        url = f"{self.url_string}/s/{site}/stat/report/{interval}.{type}"
       
        if macs != []:
            payload = {'macs': macs}

            response = await self.make_async_request(url=url, cmd='p', payload=payload)

            #nested_data = response['data']

            return response      

        else:
            payload = {'': ''}

            response = await self.make_async_request(url=url, cmd='p', payload=payload)

            #nested_data = response['data']

            return response  

    async def auth_audit(self, start='', end='', site=''):

        url = f"{self.url_string}/s/{site}/stat/authorization/"

        payload = {'start': start, 'end': end}

        response = await self.make_async_request(url=url, cmd='p', payload=payload)

        #nested_data = response['data']

        return response   

    async def mgr_sites(self, **kwargs):

        url = f"{self.url_string}/s/default/cmd/sitemgr/"

        match str(kwargs.get('cmd')).strip():
                case 'g':
                    payload = {'cmd': 'get-admins'}

                case 'a':
                    payload = {'cmd': 'add-site', 'name': str(kwargs.get('name')), 'desc': str(kwargs.get('desc'))}
                
                case 'u':
                    payload = {'cmd': 'update-site',
                                      'name': kwargs.get('name'),
                                      'desc': kwargs.get('desc')}
                    
                case 'r':
                    payload = {'cmd': 'delete-site',
                                      'name': kwargs.get('name')}
                    
                case 'm':
                    payload = {'cmd': 'move-device',
                                      'mac': str(kwargs.get('mac')),
                                      'site_id': str(kwargs.get('site_id'))}
                    
                case 'd':
                    payload = {'cmd': 'delete-device',
                                      'mac': str(kwargs.get('mac'))}
                    
        response = await self.make_async_request(url=url, cmd='p', payload=payload)

        #nested_data = response['data']

        return response 

    async def mgr_clients(self, **kwargs):

        url = f"{self.url_string}/s/default/cmd/stamgr/"

        match str(kwargs.get('cmd')).strip():
            case 'b':
                payload = {'cmd': 'block-sta',
                                      'mac': kwargs.get('mac')}
                    
            case 'k':
                payload = {'cmd': 'kick-sta',
                                      'mac': kwargs.get('mac')}
                    
            case 'u':
                payload = {'cmd': 'unblock-sta',
                                      'mac': kwargs.get('mac')}
                    
            case 'f':
                payload = {'cmd': 'forget-sta',
                                      'mac': kwargs.get('mac')}
                    
            case 'r':
                payload = {'cmd': 'unauthorize-guest',
                                      'mac': kwargs.get('mac')}
                
        response = await self.make_async_request(url=url, cmd='p', payload=payload)

        #nested_data = response['data']

        return response

    async def mgr_devices(self, **kwargs):

        url = f"{self.url_string}/s/default/cmd/stamgr/"

        match str(kwargs.get('cmd')).strip():
                case 'a':
                    payload = {'cmd': 'adopt',
                                      'mac': kwargs.get('mac')}
                case 'r':
                    payload = {'cmd': 'restart',
                                      'mac': kwargs.get('mac')}
                case 'f':
                    payload = {'cmd': 'force-provision',
                                      'mac': kwargs.get('mac')}
                case 'p':
                    payload = {'cmd': 'power-cycle',
                                      'mac': kwargs.get('mac'),
                                      'port_idx': kwargs.get('port_idx')}
                case 's':
                    payload = {'cmd': 'speedtest',
                                      'mac': kwargs.get('mac')}
                case 'S':
                    payload = {'cmd': 'speedtest-status',
                                      'mac': kwargs.get('mac')}
                case 'l':
                    payload = {'cmd': 'set-locate',
                                      'mac': kwargs.get('mac')}
                case 'L':
                    payload = {'cmd': 'unset-locate',
                                      'mac': kwargs.get('mac')}
                case 'u':
                    payload = {'cmd': 'upgrade',
                                      'mac': kwargs.get('mac')}
                case 'U':
                    if url.strip() == '':
                        self.logger.debug('Enter the URL for the firmware to update to.')
                    else:
                        self.logger.debug('Updating...')
                        payload = {'cmd': 'upgrade-external',
                                        'mac': kwargs.get('mac'),
                                        'url': kwargs.get('url')}
                case 'm':
                    if self.inform_url.strip() == '':
                        self.logger.debug('Enter the new inform URL to migrate the device: %s to.' % kwargs.get('mac'))
                    else:
                        ('Migrating...')
                        payload = {'cmd': 'migrate',
                                        'mac': kwargs.get('mac'),
                                        'inform_url': self.inform_url}
                case 'M':
                    payload = {'cmd': 'cancel-migrate',
                                      'mac': kwargs.get('mac')}
                case 'w':
                    payload = {'cmd': 'spectrum-scan',
                                      'mac': kwargs.get('mac')}
                    
        response = await self.make_async_request(url=url, cmd='p', payload=payload)

        #nested_data = response['data']

        return response