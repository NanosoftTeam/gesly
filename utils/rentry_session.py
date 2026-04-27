import os
import http.cookiejar

import urllib.parse
import urllib.request
from http.cookies import SimpleCookie
from json import loads as json_loads

class UrllibClient:
    """Klient HTTP z obsługą sesji i ciasteczek."""
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

class TunnelCreateException(Exception):
    """Wyjątek zgłaszany przy błędzie tworzenia tunelu."""
    pass
class TunnelRawException(Exception):
    """Wyjątek zgłaszany przy błędzie pobierania tunelu."""
    pass
class TunnelUpdateException(Exception):
    """Wyjątek zgłaszany przy błędzie aktualizacji tunelu."""
    pass
class TunnelSystemUpdateException(Exception):
    """Wyjątek zgłaszany przy błędzie aktualizacji systemu."""
    pass

class RentrySession:
    def __init__(self, userName):
        self.url = "https://rentry.co"
        self.tunnelName = "tunnel-system-gesly"
        self.userName = userName
        self.data = ""
        self._headers = {"Referer": "https://rentry.co"}
        auth = os.getenv("rentry-auth")
        self._headers["rentry-auth"] = auth

    def verifyIfUserExists(self):
        data = self.getData()
        users = self.getUsers(data)

        for user in users:
            if user[0] == self.userName:
                return False
        return True
    
    def getCSRF(self) -> str:
        client, cookie = UrllibClient(), SimpleCookie()
        cookie.load(vars(client.get(f"https://rentry.co", headers=self._headers))['headers']['Set-Cookie'])
        return cookie['csrftoken'].value

    def getData(self):
        # ========================== Pobieranie CSRF tokenu ==========================
        csrftoken = self.getCSRF()
        print(f"CSRF token: {csrftoken}")
        # ============================================================================
        payload = {
            """Pobieranie danych użytkowników z tunelu systemowego lub tunelu użytkownika."""
            "csrfmiddlewaretoken": csrftoken,
            "text": f"tunnel-system-gesly",
        }
        
        result_fetch = UrllibClient().post(f"https://rentry.co/api/raw/{self.tunnelName}",
                                   payload, headers=self._headers).data
        if "errors" in result_fetch:
            print(result_fetch)
            raise TunnelRawException("Błąd pobierania danych użytkowników.")

        return result_fetch

    def getUsers(self, data=None):
        if data is None:
            data = self.getData()
        list = json_loads(data)["content"].splitlines()
        users = [x.split("- ") for x in list]
        return users

    def getUser(self, data=None, nick=""):
        if data is None:
            data = self.getData()
        list = json_loads(data)["content"].splitlines()
        users = [x.split("- ") for x in list]

        for user in users:
            if user[0] == nick:
                return user

        return None


    def updateIP(self, ip, port):
        data = self.getData()
        users = self.getUsers(data)

        # self.deleteIP()
        i = 0
        while i < len(users):
            if users[i][0] == self.userName:
                # print("del")
                # print(users[i])
                del users[i]
            else:
                i += 1
        # ========================== Pobieranie CSRF tokenu ==========================
        csrftoken = self.getCSRF()
        # ============================================================================

        # Nadpisanie daty
        users.append([self.userName, f"{ip}:{port}"])
        data_new = "\n".join(["- ".join(x) for x in users])

        # Zwrot z API
        payload = {
            """Aktualizacja danych użytkowników w tunelu systemowym lub tunelu użytkownika."""
            "csrfmiddlewaretoken": csrftoken,
            "text": f"{data_new}",
            "edit_code": f"GeslySystemPassword123",
        }
        result_update = UrllibClient().post(f"https://rentry.co/api/edit/{self.tunnelName}",
                                    payload, headers=self._headers)

        # Obsługa błędu
        if "errors" in result_update.data:
            raise TunnelUpdateException("Błąd aktualizacji danych użytkowników.")

        print("Zaktualizowano dane użytkowników.")
        return result_update.data

    def deleteIP(self):
        data = self.getData()
        users = self.getUsers(data)
        # ========================== Pobieranie CSRF tokenu ==========================
        csrftoken = self.getCSRF()
        # ============================================================================

        i = 0
        while i < len(users):
            if users[i][0] == self.userName:
                # print("del")
                # print(users[i])
                del users[i]
            else:
                i += 1

        data_new = "\n".join(["- ".join(x) for x in users])
        payload = {
            """Aktualizacja danych użytkowników w tunelu systemowym lub tunelu użytkownika."""
            "csrfmiddlewaretoken": csrftoken,
            "text": f"{data_new}",
            # "update_mode": f"upsert",
            "edit_code": f"GeslySystemPassword123",
        }
        # print(data_new)
        uclient = UrllibClient()
        result_update = uclient.post(f"https://rentry.co/api/edit/{self.tunnelName}",
                                    payload, headers=self._headers)

        # Obsługa błędu
        if "errors" in result_update.data:
            raise TunnelUpdateException("Błąd aktualizacji bazy.")

        print("Zaktualizowano bazę.")

        return result_update.data

    def updateRoom(self):
        return
        # ========================== Pobieranie CSRF tokenu ==========================
        csrftoken = self.getCSRF()
        # ============================================================================

        """Używać tylko w przypadku usuniętego tunelu systemowego."""
        payload = {
            "csrfmiddlewaretoken": csrftoken,
            "text": self.data,
            "edit_code": "GeslySystemPassword123",
            "url": "tunnel-system-gesly",
        }

        # Zwrot z API
        result_update = UrllibClient().post(f"https://rentry.co/api/new", payload, headers=self._headers)

        # Obsługa błędu
        if "errors" in result_update.data:
            raise TunnelSystemUpdateException("Błąd aktualizacji danych systemowych.")

        print("Zaktualizowano dane systemowe.")
        return result_update.data