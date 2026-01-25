import socket
from xmlrpc import client
import stun
import requests
import threading
import sys
import getopt
import http.cookiejar
import sys
import urllib.parse
import urllib.request
from http.cookies import SimpleCookie
from json import loads as json_loads
from os import environ
from time import sleep
import ssl

# Must have - inaczej nie łączy

ssl._create_default_https_context = ssl._create_unverified_context

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
    
"""
TYP_POLACZENIA:
1 - Pobierz dane użytkowników z tunelu
2 - Wymień swoje stare IPv4 na nowe w tunelu
9 - Aktualizacja systemu (Nie używać)
"""

def zwroc_payloads(type, csrftoken, username, destination_username, data, operateOnSystem):
    """Funkcja polegająca na zwróceniu odpowiednich payloadów do rentry.co"""
    payloads = {
        1: {
            """Pobieranie danych użytkowników z tunelu systemowego lub tunelu użytkownika."""
            "csrfmiddlewaretoken": csrftoken,
            "text": f"tunnel-system-gesly",
            "edit_code": f"GeslySystemPassword123",
        },
        2: {
            """Aktualizacja danych użytkowników w tunelu systemowym lub tunelu użytkownika."""
            "csrfmiddlewaretoken": csrftoken,
            "text": f"{data}",
            "edit_code": f"GeslySystemPassword123",
        },
        9: {
            "csrfmiddlewaretoken": csrftoken,
            "text": data,
            "edit_code": "GeslySystemPassword123",
            "url": "tunnel-system-gesly",
        },
    }
    return payloads[type]

def operacja(TYP_POLACZENIA: int, username: str = "", destination_username: str = "", data: str = "", operateOnSystem: bool = True, ip: str = "") -> str:
    """Funkcja bauzjąca na stronie rentry.co w celu uzyskania IPv4 aktywnych użytkowników."""

    # Pobieranie CSRF tokenu
    client, cookie = UrllibClient(), SimpleCookie()
    cookie.load(vars(client.get(f"https://rentry.co"))['headers']['Set-Cookie'])
    csrftoken = cookie['csrftoken'].value
    
    # W dacie mamy nasze IPv4. Nadpisujemy je naszą nazwą użytkownika.
    if TYP_POLACZENIA == 1 or TYP_POLACZENIA == 2:
        # Dodajemy nazwę użytkownika do danych, jeśli tylko nie jest to sygnał usunięcia
        if data != ">deleteSignal<":
            data = f"{username}- {data}"
    
    _headers = {"Referer": f"https://rentry.co"}
    
    if TYP_POLACZENIA == 1:
        # url = "tunnel-system-gesly"
        url = f"tunnel-system-gesly" if operateOnSystem else f"tunnel-{username}-{destination_username}-gesly"
        
        result_fetch = client.post(f"https://rentry.co/api/fetch/{url}", zwroc_payloads(TYP_POLACZENIA, csrftoken, username, destination_username, data, operateOnSystem), headers=_headers).data
        if "errors" in result_fetch:
            raise TunnelFetchException("Błąd pobierania danych użytkowników.")
        
        return result_fetch
    elif TYP_POLACZENIA == 2:
        # Bierzemy aktualnych użytkowników
        current_users = json_loads(operacja(1, username=username, operateOnSystem=True))["content"]["text"]
        
        # url = "tunnel-system-gesly"
        url = f"tunnel-system-gesly" if operateOnSystem else f"tunnel-{username}-{destination_username}-gesly"
        
        if data == ">deleteSignal<":
            # Usunięcie użytkownika z systemu
            current_users_list = [x.strip() for x in current_users.splitlines()]
            current_users_list = [line for line in current_users_list if line.split("-")[0] != username]
            
            # Nadpisanie daty
            data = "\n".join(current_users_list)
            
            # Payloady
            zwroc_payloads(TYP_POLACZENIA, csrftoken, username, destination_username, data, operateOnSystem)
            result_update = client.post(f"https://rentry.co/api/edit/{url}", zwroc_payloads(TYP_POLACZENIA, csrftoken, username, destination_username, data, operateOnSystem), headers=_headers)
            
            # Obsługa błędu
            if "errors" in result_update.data:
                raise TunnelUpdateException("Błąd aktualizacji bazy.")
            
            print("Zaktualizowano bazę.")
            return(result_update.data)
        else:
            # Nadpisanie daty
            data = current_users + f"\n{data}"
            
            # Zwrot z API
            result_update = client.post(f"https://rentry.co/api/edit/{url}", zwroc_payloads(TYP_POLACZENIA, csrftoken, username, destination_username, data, operateOnSystem), headers=_headers)
            
            # Obsługa błędu
            if "errors" in result_update.data:
                raise TunnelUpdateException("Błąd aktualizacji danych użytkowników.")
            
            print("Zaktualizowano dane użytkowników.")
            return(result_update.data)
    elif TYP_POLACZENIA == 9:
        # Zwrot z API
        result_update = client.post(f"https://rentry.co/api/new", zwroc_payloads(TYP_POLACZENIA, csrftoken, username, destination_username, data, operateOnSystem), headers=_headers)
        
        # Obsługa błędu
        if "errors" in result_update.data:
            raise TunnelSystemUpdateException("Błąd aktualizacji danych systemowych.")
        
        print("Zaktualizowano dane systemowe.")
        return(result_update.data)

def sluchaj(soc):
    """Odbieranie wiadomości w tle."""
    while True:
        try:
            # Magia odbierania wiadomości, omg
            data, addr = soc.recvfrom(1024)
            print(f"\n[KOLEGA {addr}]: {data.decode('utf-8')}")
            print("Ty: ", end="", flush=True)
        except Exception as e:
            print(f"Błąd odbierania wiadomości: {e}")
            break

username_input = input("Twoja nazwa użytkownika: ").strip()

def start_chat():
    
# ========================================================================

    # 1. Lista serwerów, które u Ciebie działają
    serwery_stun = [
        'stun1.l.google.com',
        'stun2.l.google.com',
        'stun.l.google.com',
        'stun.ekiga.net'
    ]

    # Deklaracja zmiennych
    local_port = 6676
    external_ip = None
    external_port = None
    nat_type = None

    print(f"--- Inicjalizacja (Port lokalny: {local_port}) ---")

# ========================================================================

    # 2. Szukanie działającego serwera STUN przy zachowaniu portu
    for host in serwery_stun:
        try:
            print(f"Próba: {host}...", end=" ")
            # Bardzo ważne: source_port musi być taki sam jak port, na którym będziemy słuchać
            nat_type, external_ip, external_port = stun.get_ip_info(
                stun_host=host, 
                source_port=local_port
            )
            if external_ip:
                print("SUKCES!")
                break
        except Exception:
            print("Błąd.")

    if not external_ip:
        print("\nNie udało się połączyć z żadnym serwerem STUN. Sprawdź internet.")
        return

    print("\n" + "="*40)
    print(f"TWOJE DANE:")
    print(f"IP:   {external_ip}")
    print(f"PORT: {external_port}")
    print(f"NAT:  {nat_type}")
    print("="*40 + "\n")

# ========================================================================

    # 3. Tworzenie gniazda do rozmowy
    soc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Bindowanie portu
    try:
        soc.bind(('0.0.0.0', local_port))
    except Exception as e:
        print(f"Błąd bindowania portu: {e}")
        return
    
# ========================================================================
    
    # 4. Wymiana danych z kolegą przez rentry.co
    try:
        users = json_loads(operacja(1, username=username_input, operateOnSystem=True))["content"]["text"].splitlines()    
    except TunnelFetchException as e:
        print(f"Błąd pobierania danych użytkowników: {e}")
        return

    usernames = [x.split()[0].rstrip("-") for x in users]
    ips = [x.split()[1] for x in users]
    
    print("Sprawdzanie, czy podana nazwa użytkownika istnieje w toku...")

    # Czy nazwa użytkownika już istnieje?
    if (username_input in usernames):
        index = usernames.index(username_input)
        if f"{external_ip}:{external_port}" == ips[index]:
            print("Podana nazwa użytkownika należy do Ciebie...")
        else:
            print("Podana nazwa użytkownika należy do kogoś innego. Wybierz inną nazwę.")
            # Powrót to wybierania nazwy użytkownika -> Do implementacji !!!
    else:
        print("Nie wykryto użytkownika o podanej nazwie.")
        print("Nadpisywanie bazy danych w toku...")

        # Nadpisanie bazy danych
        try:
            operacja(2, username=username_input, data=f"{external_ip}:{external_port}", operateOnSystem=True)
        except TunnelUpdateException as e:
            print(f"Błąd aktualizacji danych użytkowników: {e}")
            return        

    print("Oczekiwanie na użytkowników w toku...")
    
# ========================================================================
    
    # 5. Dane kolegi

    while True:
        try:
            # Odświeżanie listy użytkowników
            users = json_loads(operacja(1, username=username_input, operateOnSystem=True))["content"]["text"].splitlines()    
            usernames = [x.split()[0].rstrip("-") for x in users]
            ips = [x.split()[1] for x in users]
            
            # Wyświetlanie dostępnych użytkowników
            if len(usernames) > 1:
                print(f"Dostępni nowi użytkownicy {len(usernames) - 1}:")
                for i, name in enumerate(usernames):
                    if name != username_input:
                        print(f"{i}. {name} ({ips[i]})")
                    
                # Wybór użytkownika
                choice = input("Wybierz użytkownika do czatu (podaj numer): ").strip()
                if choice.isdigit() and 0 <= int(choice) < len(usernames):
                    
                    # Nadpisanie danych peer'a
                    peer_ip, peer_port = ips[int(choice)].split(":")
                    peer_port = int(peer_port)
                    peer_ip = peer_ip.strip()
                    
                    # Pomyślnie wybranie użytkownika
                    print(f"Wybrano użytkownika {usernames[int(choice)]} ({peer_ip}:{peer_port})")
                    break
        except TunnelFetchException as e:
            print("\nZamykanie...")
            try:
                operacja(2, username=username_input, data=">deleteSignal<", operateOnSystem=True)
            except TunnelUpdateException as e:
                print(f"Błąd aktualizacji danych użytkowników: {e}")
            sys.exit()
        sleep(5)

# ========================================================================

    # 6. Start czatu
    threading.Thread(target=sluchaj, args=(soc,), daemon=True).start()

    print("\n--- CZAT AKTYWNY (wpisz 'exit' by wyjść) ---")
    print("Wskazówka: Jeśli wiadomości nie dochodzą, wyślijcie 'test' obaj w tym samym momencie.")
    
    while True:
        msg = input("Ty: ")
        if msg.lower() == 'exit':
            break
        if msg:
            soc.sendto(msg.encode('utf-8'), (peer_ip, peer_port))

if __name__ == "__main__":
    try:
        start_chat()
    except KeyboardInterrupt:
        print("\nZamykanie...")
        try:
            operacja(2, username=username_input, data=">deleteSignal<", operateOnSystem=True)
        except TunnelUpdateException as e:
            print(f"Błąd aktualizacji danych użytkowników: {e}")
        sys.exit()