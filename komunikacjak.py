#!/usr/bin/env python3

import getopt
import http.cookiejar
import sys
import urllib.parse
import urllib.request
from http.cookies import SimpleCookie
from json import loads as json_loads
from os import environ
import ssl
# To wyłącza weryfikację globalnie dla urllib
ssl._create_default_https_context = ssl._create_unverified_context

_headers = {"Referer": f"https://rentry.co"}

class UrllibClient:
    """Simple HTTP Session Client, keeps cookies."""

    def __init__(self):
        self.cookie_jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookie_jar))
        urllib.request.install_opener(self.opener)

    def get(self, url, headers={}):
        request = urllib.request.Request(url, headers=headers)
        return self._request(request)

    def post(self, url, data=None, headers={}):
        postdata = urllib.parse.urlencode(data).encode()
        request = urllib.request.Request(url, postdata, headers)
        return self._request(request)

    def _request(self, request):
        response = self.opener.open(request)
        response.status_code = response.getcode()
        response.data = response.read().decode('utf-8')
        return response

client, cookie = UrllibClient(), SimpleCookie()
cookie.load(vars(client.get(f"https://rentry.co"))['headers']['Set-Cookie'])
csrftoken = cookie['csrftoken'].value

## Then, edit
payload = {
    'csrfmiddlewaretoken': csrftoken,
    'text': 'test update1d!',
    'edit_code' : 'u9emW43R',
    'new_modify_code' : 'm:abc',
}
result_edit = client.post(f"https://rentry.co" + f"/api/edit/viv3snzz", payload, headers=_headers).data
print(result_edit)