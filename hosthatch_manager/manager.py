from hosthatch_manager import api
from pymongo import MongoClient
from concurrent.futures import ThreadPoolExecutor
import logging
import os

class Manager:
    def __init__(self, mongo_uri: str, api_client: api.HostHatchAPI):
        self.mongo_cli = MongoClient(mongo_uri)
        self.api_client = api_client
    
    def sync_server(self, server: dict):
        server_detail = self.api_client.fetch_server_detail(server["id"])
        server_network = self.api_client.fetch_server_network(server["id"])
        server["detail"] = server_detail
        server["network"] = server_network
        return server

    def sync_all(self):
        servers = self.api_client.fetch_servers()
        executor = ThreadPoolExecutor(max_workers=10)
        servers_detail = executor.map(self.sync_server, servers["servers"])
        servers["servers"] = list(servers_detail)

        self.mongo_cli.prod.servers.update_one(
            {"provider": "hosthatch"},
            {"$set": {"servers": servers}},
            upsert=True
        )

def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        raise Exception("MONGO_URI not set")

    with api.HostHatchAPI() as api_client:
        manager = Manager(
            mongo_uri=mongo_uri,
            api_client=api_client
        )
        manager.sync_all()
