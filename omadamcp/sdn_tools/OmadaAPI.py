import aiohttp

class OmadaAPI():
    def __init__(self):
        pass

    async def get_omada_session(self):
        session = aiohttp.ClientSession()
        login_data = {
            "username": OMADA_USERNAME,
            "password": OMADA_PASSWORD
        }
        async with session.post(f"{OMADA_BASE_URL}/api/v1/login", json=login_data) as resp:
            await resp.text()
        return session

    async def get_omada_clients_and_aps(self):
        session = await self.get_omada_session()
        async with session.get(f"{OMADA_BASE_URL}/api/v1/clients") as resp:
            clients = await resp.json()
        async with session.get(f"{OMADA_BASE_URL}/api/v1/accesspoints") as resp:
            aps = await resp.json()
        await session.close()
        return clients["data"], aps["data"]

    async def omada_track(self):
        clients, aps = await self.get_omada_clients_and_aps()
        ap_map = {ap["mac"]: ap["name"] for ap in aps}

        for client in clients:
            mac = client.get("mac")
            ap_mac = client.get("ap_mac")
            if mac and ap_mac:
                ap_name = ap_map.get(ap_mac, "Unknown")
                self.store_device_ap_history(mac, ap_mac, ap_name)

        return {"status": "tracked", "count": len(clients)}