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
class TunnelFetchException(Exception):
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
        self._headers = {"Referer": f"https://rentry.co"}

    def getCSRF(self) -> str:
        client, cookie = UrllibClient(), SimpleCookie()
        cookie.load(vars(UrllibClient().get(f"https://rentry.co"))['headers']['Set-Cookie'])
        return cookie['csrftoken'].value

    def getData(self):
        # ========================== Pobieranie CSRF tokenu ==========================
        csrftoken = self.getCSRF()
        # ============================================================================
        payload = {
            """Pobieranie danych użytkowników z tunelu systemowego lub tunelu użytkownika."""
            "csrfmiddlewaretoken": csrftoken,
            "text": f"tunnel-system-gesly",
            "edit_code": f"GeslySystemPassword123",
        }
        result_fetch = UrllibClient().post(f"https://rentry.co/api/fetch/{self.tunnelName}",
                                   payload, headers={"Referer": f"https://rentry.co"}).data
        if "errors" in result_fetch:
            raise TunnelFetchException("Błąd pobierania danych użytkowników.")

        return result_fetch

    def getUsers(self, data=None):
        if data is None:
            data = self.getData()
        list = json_loads(data)["content"]["text"].splitlines()
        users = [x.split("- ") for x in list]
        return users

    def getUser(self, data=None, nick=""):
        if data is None:
            data = self.getData()
        list = json_loads(data)["content"]["text"].splitlines()
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
                                    payload, headers={"Referer": f"https://rentry.co"})

        # Obsługa błędu
        if "errors" in result_update.data:
            raise TunnelUpdateException("Błąd aktualizacji danych użytkowników.")

        print("Zaktualizowano dane użytkowników.")
        return result_update.data

    def deleteIP(self): #dlaczego to nie działa?
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

        # print(users)

        # # Usunięcie użytkownika z systemu
        # current_users_list = [x.strip() for x in current_users.splitlines()]
        # current_users_list = [line for line in current_users_list if line.split("-")[0] != self.userName]

        # # Nadpisanie daty
        # data = "\n".join(current_users_list)

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
                                    payload, headers={"Referer": f"https://rentry.co"})

        print(payload)

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

# session = RentrySession(input("nazwa: "))
# session.updateIP("172.16.31.10", "1234")
# session.deleteIP()
# print(session.getUsers())