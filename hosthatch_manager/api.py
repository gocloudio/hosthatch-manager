import requests
from http.cookiejar import LWPCookieJar
from http.cookies import SimpleCookie
from requests.cookies import create_cookie
import os
import logging
import urllib.parse

logger = logging.getLogger(__name__)


class Error(Exception):
    pass


class HostHatchAPI:
    base_uri = "https://cloud.hosthatch.com"
    def __init__(self, cookie_file=None):
        self.default_headers = {
            'x-inertia': 'true',
            'x-inertia-version': '13eb291c15a5460b41299033a48cea5f'
        }

        if not cookie_file:
            cookie_file = os.getenv(
                "HOSTHATCH_COOKIE_FILE", "/tmp/hosthatch.cookie")

        self.cookie_file = cookie_file
        self.jar = LWPCookieJar(self.cookie_file)
        cookie = os.getenv("HOSTHATCH_COOKIE")
        try:
            self.jar.load()
        except FileNotFoundError:
            if not cookie:
                raise Error("cookie file not found and no cookie provided")
        finally:
            if len(self.jar) == 0 and not cookie:
                raise Error("cookie file is empty and no cookie provided")

        if cookie:
            sc = SimpleCookie()
            sc.load(cookie)
            if len(sc.items()) == 0:
                raise Exception(f"failed to load cookie {cookie}")
            for ck in sc.items():
                _, ck = ck
                self.jar.set_cookie(create_cookie(
                    name=ck.key, value=ck.value, domain=".hosthatch.com"))
            self.jar.save(ignore_discard=True)

        self.s = requests.Session()
        self.s.cookies = self.jar
        for cookie in self.s.cookies:
            if cookie.name == "XSRF-TOKEN":
                self.s.headers["X-Xsrf-Token"] = cookie.value

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        _, _,  _ = exc_type, exc_value, traceback
        self.jar.save(ignore_discard=True)

    def make_request(self, uri, method="GET", headers={}, data=None):
        url = f"{self.base_uri}{uri}"
        headers.update(self.default_headers)
        response = self.s.request(method, url, headers=headers, data=data)
        response.raise_for_status()
        return response.json()

    def fetch_servers(self) -> dict:
        logger.info("fetching servers")
        return self.make_request("/servers")["props"]

    def fetch_server_detail(self, server_id: str) -> dict:
        logger.info(f"fetching server detail for {server_id}")
        return self.make_request(
            f"/servers/{server_id}",
            headers={"x-peregrine-request": "Servers/ShowServer"}
        )["props"]
    
    def fetch_server_network(self, server_id: str) -> dict:
        logger.info(f"fetching server network for {server_id}")
        return self.make_request(
            f"/servers/{server_id}/network",
            headers={
                "X-Inertia-Partial-Component": "Servers/ShowServer",
                "X-Inertia-Partial-Data": "network",
            }
        )["props"]

