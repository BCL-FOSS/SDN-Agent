from fastmcp import FastMCP
from sdn_tools.UniFiNetAPI import UniFiNetAPI
import logging

mcp = FastMCP(name="UniFiAutomation")

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('passlib').setLevel(logging.ERROR)
logger = logging.getLogger(__name__)

@mcp.tool
async def active_clients(cntlr_data:dict, site: str) -> dict:
    host=cntlr_data.get('ip')
    port=cntlr_data.get('port')
    uname=cntlr_data.get('uname')
    passwd=cntlr_data.get('pwd')

    ubnt = UniFiNetAPI(controller_ip=host, controller_port=port, username=uname, password=passwd)
    auth_rslt = await ubnt.authenticate()
    logger.debug(auth_rslt)

    current_clients = await ubnt.active_clients(site=site)
    logger.debug(current_clients)
    return current_clients

@mcp.tool
async def active_routes(cntlr_data:dict, site: str) -> dict:
    host=cntlr_data.get('ip')
    port=cntlr_data.get('port')
    uname=cntlr_data.get('uname')
    passwd=cntlr_data.get('pwd')

    ubnt = UniFiNetAPI(controller_ip=host, controller_port=port, username=uname, password=passwd)
    auth_rslt = await ubnt.authenticate()
    logger.debug(auth_rslt)

    routes=await ubnt.active_routes(site=site)
    logger.debug(routes)
    return routes

@mcp.tool
async def alarm_data(cntlr_data:dict, site: str) -> dict:
    host=cntlr_data.get('ip')
    port=cntlr_data.get('port')
    uname=cntlr_data.get('uname')
    passwd=cntlr_data.get('pwd')

    ubnt = UniFiNetAPI(controller_ip=host, controller_port=port, username=uname, password=passwd)
    auth_rslt = await ubnt.authenticate()
    logger.debug(auth_rslt)
    
    alarms = await ubnt.alarm_data(site=site)
    logger.debug(alarms)
    return alarms

@mcp.tool
async def all_clients(cntlr_data:dict, site: str) -> dict:
    host=cntlr_data.get('ip')
    port=cntlr_data.get('port')
    uname=cntlr_data.get('uname')
    passwd=cntlr_data.get('pwd')

    ubnt = UniFiNetAPI(controller_ip=host, controller_port=port, username=uname, password=passwd)
    auth_rslt = await ubnt.authenticate()
    logger.debug(auth_rslt)

    clients=await ubnt.all_clients(site=site)
    logger.debug(clients)
    return clients

@mcp.tool
async def auth_audit(cntlr_data:dict, site: str, start: str, end: str) -> dict:
    host=cntlr_data.get('ip')
    port=cntlr_data.get('port')
    uname=cntlr_data.get('uname')
    passwd=cntlr_data.get('pwd')

    ubnt = UniFiNetAPI(controller_ip=host, controller_port=port, username=uname, password=passwd)
    auth_rslt = await ubnt.authenticate()
    logger.debug(auth_rslt)

    auth_list=await ubnt.auth_audit(site=site, start=start, end=end)
    logger.debug(auth_list)
    return auth_list

@mcp.tool
async def client_dpi_data(cntlr_data:dict, site: str, macs: list = [], type: bool = False) -> dict:
    host=cntlr_data.get('ip')
    port=cntlr_data.get('port')
    uname=cntlr_data.get('uname')
    passwd=cntlr_data.get('pwd')

    ubnt = UniFiNetAPI(controller_ip=host, controller_port=port, username=uname, password=passwd)
    auth_rslt = await ubnt.authenticate()
    logger.debug(auth_rslt)

    client_dpi = None

    if macs != []:
        client_dpi = await ubnt.client_dpi_data(site=site, type=type, macs=macs)
    else:
        client_dpi = await ubnt.client_dpi_data(site=site, type=type)

    logger.debug(client_dpi)
    return client_dpi

@mcp.tool
async def controller_health_data(cntlr_data:dict) -> dict:
    host=cntlr_data.get('ip')
    port=cntlr_data.get('port')
    uname=cntlr_data.get('uname')
    passwd=cntlr_data.get('pwd')

    ubnt = UniFiNetAPI(controller_ip=host, controller_port=port, username=uname, password=passwd)
    auth_rslt = await ubnt.authenticate()

    logger.debug(auth_rslt)
    cntlr_hlth_data=await ubnt.controller_health_data()
    logger.debug(cntlr_hlth_data)
    return cntlr_hlth_data


@mcp.tool
async def device_data(cntlr_data:dict, site: str, macs: list = []) -> dict:
    host=cntlr_data.get('ip')
    port=cntlr_data.get('port')
    uname=cntlr_data.get('uname')
    passwd=cntlr_data.get('pwd')

    ubnt = UniFiNetAPI(controller_ip=host, controller_port=port, username=uname, password=passwd)
    auth_rslt = await ubnt.authenticate()
    logger.debug(auth_rslt)

    dev_data=None

    if macs != []:
        dev_data=await ubnt.device_data(site=site, macs=macs)
    else:
        dev_data=await ubnt.device_data(site=site)

    logger.debug(dev_data)
    return dev_data

@mcp.tool
async def device_data_basic(cntlr_data:dict, site: str) -> dict:
    host=cntlr_data.get('ip')
    port=cntlr_data.get('port')
    uname=cntlr_data.get('uname')
    passwd=cntlr_data.get('pwd')

    ubnt = UniFiNetAPI(controller_ip=host, controller_port=port, username=uname, password=passwd)
    auth_rslt = await ubnt.authenticate()
    logger.debug(auth_rslt)

    dev_data=await ubnt.device_data_basic(site=site)
    logger.debug(dev_data)
    return dev_data

@mcp.tool
async def dynamic_dns_config(cntlr_data:dict, cmd: str, site: str) -> dict:
    host=cntlr_data.get('ip')
    port=cntlr_data.get('port')
    uname=cntlr_data.get('uname')
    passwd=cntlr_data.get('pwd')

    ubnt = UniFiNetAPI(controller_ip=host, controller_port=port, username=uname, password=passwd)
    auth_rslt = await ubnt.authenticate()
    logger.debug(auth_rslt)

    dns_config=await ubnt.dynamic_dns_config(cmd=cmd, site=site)
    logger.debug(dns_config)
    return dns_config

@mcp.tool
async def dynamic_dns_info(cntlr_data:dict, site: str) -> dict:
    host=cntlr_data.get('ip')
    port=cntlr_data.get('port')
    uname=cntlr_data.get('uname')
    passwd=cntlr_data.get('pwd')

    ubnt = UniFiNetAPI(controller_ip=host, controller_port=port, username=uname, password=passwd)
    auth_rslt = await ubnt.authenticate()
    logger.debug(auth_rslt)

    dns_info=await ubnt.dynamic_dns_info(site=site)
    logger.debug(dns_info)
    return dns_info

@mcp.tool
async def event_data(cntlr_data:dict, site: str) -> dict:
    host=cntlr_data.get('ip')
    port=cntlr_data.get('port')
    uname=cntlr_data.get('uname')
    passwd=cntlr_data.get('pwd')

    ubnt = UniFiNetAPI(controller_ip=host, controller_port=port, username=uname, password=passwd)
    auth_rslt = await ubnt.authenticate()
    logger.debug(auth_rslt)
    events=await ubnt.event_data(site=site)
    logger.debug(events)
    return events

@mcp.tool
async def firewall_groups(cntlr_data:dict, cmd: str, site: str) -> dict:
    host=cntlr_data.get('ip')
    port=cntlr_data.get('port')
    uname=cntlr_data.get('uname')
    passwd=cntlr_data.get('pwd')

    ubnt = UniFiNetAPI(controller_ip=host, controller_port=port, username=uname, password=passwd)
    auth_rslt = await ubnt.authenticate()
    logger.debug(auth_rslt)

    fw_groups=await ubnt.firewall_groups(cmd=cmd, site=site)
    logger.debug(fw_groups)
    return fw_groups

@mcp.tool
async def firewall_rules(cntlr_data:dict, cmd: str, site: str) -> dict:
    host=cntlr_data.get('ip')
    port=cntlr_data.get('port')
    uname=cntlr_data.get('uname')
    passwd=cntlr_data.get('pwd')

    ubnt = UniFiNetAPI(controller_ip=host, controller_port=port, username=uname, password=passwd)
    auth_rslt = await ubnt.authenticate()
    logger.debug(auth_rslt)

    fw_rules=await ubnt.firewall_rules(cmd=cmd, site=site)
    logger.debug(fw_rules)
    return fw_rules

@mcp.tool
async def get_system_info(cntlr_data:dict, opt: dict) -> dict:
    host=cntlr_data.get('ip')
    port=cntlr_data.get('port')
    uname=cntlr_data.get('uname')
    passwd=cntlr_data.get('pwd')

    ubnt = UniFiNetAPI(controller_ip=host, controller_port=port, username=uname, password=passwd)
    auth_rslt = await ubnt.authenticate()
    logger.debug(auth_rslt)

    sys_info=await ubnt.get_sysinfo()
    logger.debug(sys_info)
    return sys_info

@mcp.tool
async def list_port_profiles(cntlr_data:dict, site: str) -> dict:
    host=cntlr_data.get('ip')
    port=cntlr_data.get('port')
    uname=cntlr_data.get('uname')
    passwd=cntlr_data.get('pwd')

    ubnt = UniFiNetAPI(controller_ip=host, controller_port=port, username=uname, password=passwd)
    auth_rslt = await ubnt.authenticate()
    logger.debug(auth_rslt)

    port_profiles=await ubnt.list_port_profiles(site=site)
    logger.debug(port_profiles)
    return port_profiles

@mcp.tool
async def list_admins(cntlr_data:dict) -> dict:
    host=cntlr_data.get('ip')
    port=cntlr_data.get('port')
    uname=cntlr_data.get('uname')
    passwd=cntlr_data.get('pwd')

    ubnt = UniFiNetAPI(controller_ip=host, controller_port=port, username=uname, password=passwd)
    auth_rslt = await ubnt.authenticate()
    logger.debug(auth_rslt)

    admins=await ubnt.list_admins()
    logger.debug(admins)
    return admins

@mcp.tool
async def manage_clients(cntlr_data:dict, cmd: str, mac: str) -> dict:
    host=cntlr_data.get('ip')
    port=cntlr_data.get('port')
    uname=cntlr_data.get('uname')
    passwd=cntlr_data.get('pwd')

    ubnt = UniFiNetAPI(controller_ip=host, controller_port=port, username=uname, password=passwd)
    auth_rslt = await ubnt.authenticate()
    logger.debug(auth_rslt)

    managed_client=await ubnt.mgr_clients(cmd=cmd, mac=mac)
    logger.debug(managed_client)
    return managed_client

@mcp.tool
async def manage_devices(cntlr_data:dict, cmd: str, mac: str, port_idx: str = '', url: str = '') -> dict:
    host=cntlr_data.get('ip')
    port=cntlr_data.get('port')
    uname=cntlr_data.get('uname')
    passwd=cntlr_data.get('pwd')

    ubnt = UniFiNetAPI(controller_ip=host, controller_port=port, username=uname, password=passwd)
    auth_rslt = await ubnt.authenticate()
    logger.debug(auth_rslt)

    managed_device=None
    if url != '':
        managed_device=await ubnt.mgr_devices(cmd=cmd, mac=mac, url=url)
    elif port_idx != '':
        managed_device=await ubnt.mgr_devices(cmd=cmd, mac=mac, port_idx=port_idx)
    else:
        managed_device=await ubnt.mgr_devices(cmd=cmd, mac=mac)

    logger.debug(managed_device)
    return managed_device

@mcp.tool
async def manage_sites(cntlr_data:dict, cmd: str, name: str, mac: str, site_id: str='', desc: str='') -> dict:
    host=cntlr_data.get('ip')
    port=cntlr_data.get('port')
    uname=cntlr_data.get('uname')
    passwd=cntlr_data.get('pwd')

    ubnt = UniFiNetAPI(controller_ip=host, controller_port=port, username=uname, password=passwd)
    auth_rslt = await ubnt.authenticate()
    logger.debug(auth_rslt)

    managed_site=None

    match cmd.strip():
        case 'g':
            managed_site=await ubnt.mgr_sites(cmd=cmd)

        case 'a':
            managed_site=await ubnt.mgr_sites(cmd=cmd, name=name, desc=desc)
                   
        case 'u':
            managed_site=await ubnt.mgr_sites(cmd=cmd, name=name, desc=desc)
       
        case 'r':
            managed_site=await ubnt.mgr_sites(cmd=cmd, name=name)
                    
        case 'm':
            managed_site=await ubnt.mgr_sites(cmd=cmd, site_id=site_id, mac=mac)
                    
        case 'd':
            managed_site=await ubnt.mgr_sites(cmd=cmd, mac=mac)

    logger.debug(managed_site)
    return managed_site

@mcp.tool
async def port_forwards(cntlr_data:dict, site: str) -> dict:
    host=cntlr_data.get('ip')
    port=cntlr_data.get('port')
    uname=cntlr_data.get('uname')
    passwd=cntlr_data.get('pwd')

    ubnt = UniFiNetAPI(controller_ip=host, controller_port=port, username=uname, password=passwd)
    auth_rslt = await ubnt.authenticate()
    logger.debug(auth_rslt)

    ports=await ubnt.port_forwards(site=site)
    logger.debug(ports)
    return ports

@mcp.tool
async def radius_accounts(cntlr_data:dict, cmd: str, site: str) -> dict:
    host=cntlr_data.get('ip')
    port=cntlr_data.get('port')
    uname=cntlr_data.get('uname')
    passwd=cntlr_data.get('pwd')

    ubnt = UniFiNetAPI(controller_ip=host, controller_port=port, username=uname, password=passwd)
    auth_rslt = await ubnt.authenticate()
    logger.debug(auth_rslt)

    accounts=await ubnt.radius_accounts(cmd=cmd, site=site)
    logger.debug(accounts)
    return accounts

@mcp.tool
async def radius_profiles(cntlr_data:dict, cmd: str, site: str) -> dict:
    host=cntlr_data.get('ip')
    port=cntlr_data.get('port')
    uname=cntlr_data.get('uname')
    passwd=cntlr_data.get('pwd')

    ubnt = UniFiNetAPI(controller_ip=host, controller_port=port, username=uname, password=passwd)
    auth_rslt = await ubnt.authenticate()
    logger.debug(auth_rslt)

    profiles=await ubnt.radius_profiles(cmd=cmd, site=site)
    logger.debug(profiles)
    return profiles

@mcp.tool
async def reports(cntlr_data:dict, site: str, macs: list) -> dict:
    host=cntlr_data.get('ip')
    port=cntlr_data.get('port')
    uname=cntlr_data.get('uname')
    passwd=cntlr_data.get('pwd')

    ubnt = UniFiNetAPI(controller_ip=host, controller_port=port, username=uname, password=passwd)
    auth_rslt = await ubnt.authenticate()
    logger.debug(auth_rslt)

    report=None

    if macs != []:
        report=await ubnt.reports(macs=macs, site=site)
    else:
        report=await ubnt.reports(site=site)

    logger.debug(report)
    return report

@mcp.tool
async def rf_scan_results(cntlr_data:dict, mac: str, cmd: str, site: str) -> dict:
    host=cntlr_data.get('ip')
    port=cntlr_data.get('port')
    uname=cntlr_data.get('uname')
    passwd=cntlr_data.get('pwd')

    ubnt = UniFiNetAPI(controller_ip=host, controller_port=port, username=uname, password=passwd)
    auth_rslt = await ubnt.authenticate()
    logger.debug(auth_rslt)

    scan_result=await ubnt.rf_scan_results(mac=mac, cmd=cmd, site=site)
    logger.debug(scan_result)
    return scan_result

@mcp.tool
async def rogue_aps(cntlr_data:dict, site: str, seen_last: int=0) -> dict:
    host=cntlr_data.get('ip')
    port=cntlr_data.get('port')
    uname=cntlr_data.get('uname')
    passwd=cntlr_data.get('pwd')

    ubnt = UniFiNetAPI(controller_ip=host, controller_port=port, username=uname, password=passwd)
    auth_rslt = await ubnt.authenticate()
    logger.debug(auth_rslt)

    aps=None
    if seen_last != 0:
        aps=await ubnt.rogue_aps(seen_last=seen_last, site=site)
    else: 
        aps=await ubnt.rogue_aps(site=site)

    logger.debug(aps)
    return aps


@mcp.tool
async def site_dpi_data(cntlr_data:dict, cmd: str, site: str, type: bool = False) -> dict:
    host=cntlr_data.get('ip')
    port=cntlr_data.get('port')
    uname=cntlr_data.get('uname')
    passwd=cntlr_data.get('pwd')

    ubnt = UniFiNetAPI(controller_ip=host, controller_port=port, username=uname, password=passwd)
    auth_rslt = await ubnt.authenticate()
    logger.debug(auth_rslt)

    dpi_data = await ubnt.site_dpi_data(site=site, cmd=cmd, type=type)
    logger.debug(dpi_data)
    return dpi_data

@mcp.tool
async def site_settings(cntlr_data:dict, cmd: str, site: str, key: str='', id: str='') -> dict:
    host=cntlr_data.get('ip')
    port=cntlr_data.get('port')
    uname=cntlr_data.get('uname')
    passwd=cntlr_data.get('pwd')

    ubnt = UniFiNetAPI(controller_ip=host, controller_port=port, username=uname, password=passwd)
    auth_rslt = await ubnt.authenticate()
    logger.debug(auth_rslt)

    settings=await ubnt.site_settings(key=key, id=id, cmd=cmd, site=site)
    logger.debug(settings)
    return settings

@mcp.tool
async def site_stats(cntlr_data:dict) -> dict:
    host=cntlr_data.get('ip')
    port=cntlr_data.get('port')
    uname=cntlr_data.get('uname')
    passwd=cntlr_data.get('pwd')

    ubnt = UniFiNetAPI(controller_ip=host, controller_port=port, username=uname, password=passwd)
    auth_rslt = await ubnt.authenticate()
    logger.debug(auth_rslt)

    stats=await ubnt.site_stats()
    logger.debug(stats)
    return stats

@mcp.tool
async def sites(cntlr_data:dict) -> dict:
    host=cntlr_data.get('ip')
    port=cntlr_data.get('port')
    uname=cntlr_data.get('uname')
    passwd=cntlr_data.get('pwd')

    ubnt = UniFiNetAPI(controller_ip=host, controller_port=port, username=uname, password=passwd)
    auth_rslt = await ubnt.authenticate()
    logger.debug(auth_rslt)

    sites=await ubnt.sites()
    logger.debug(sites)
    return sites

@mcp.tool
async def udm_poweroff(cntlr_data:dict) -> dict:
    host=cntlr_data.get('ip')
    port=cntlr_data.get('port')
    uname=cntlr_data.get('uname')
    passwd=cntlr_data.get('pwd')

    ubnt = UniFiNetAPI(controller_ip=host, controller_port=port, username=uname, password=passwd)
    auth_rslt = await ubnt.authenticate()
    logger.debug(auth_rslt)

    off=await ubnt.udm_poweroff()
    logger.debug(off)
    return off

@mcp.tool
async def udm_reboot(cntlr_data:dict, opt: dict) -> dict:
    host=cntlr_data.get('ip')
    port=cntlr_data.get('port')
    uname=cntlr_data.get('uname')
    passwd=cntlr_data.get('pwd')

    ubnt = UniFiNetAPI(controller_ip=host, controller_port=port, username=uname, password=passwd)
    auth_rslt = await ubnt.authenticate()
    logger.debug(auth_rslt)

    cycle=await ubnt.udm_reboot()
    logger.debug(cycle)
    return cycle

@mcp.tool
async def wlans(cntlr_data:dict, cmd: str, site: str, name: str='', pwd: str='', site_id: str='', wlan_id: str='') -> dict:
    host=cntlr_data.get('ip')
    port=cntlr_data.get('port')
    uname=cntlr_data.get('uname')
    passwd=cntlr_data.get('pwd')

    ubnt = UniFiNetAPI(controller_ip=host, controller_port=port, username=uname, password=passwd)
    auth_rslt = await ubnt.authenticate()
    logger.debug(auth_rslt)

    wlan=await ubnt.wlans(cmd=cmd, site=site, wlan_name=name, psswd=pwd, site_id=site_id, wlan_id=wlan_id)
    logger.debug(wlan)
    return wlan

if __name__ == "__main__":
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=6000,
        path="ubnt/mcp/",
        log_level="debug",
    )