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
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

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
0 - Stwórz nowy tunel
1 - Pobierz dane użytkowników z tunelu
2 - Wymień swoje stare IPv4 na nowe w tunelu
3 - Wymaż tunel (konwersacja zostaje na komputyerach użytkowników)
9 - Aktualizacja "siebie" w systemie
"""

def algorytm(tekst1, tekst2):
    # Łączymy zmienne w jeden ciąg
    polaczone = tekst1 + tekst2
    
    # Sortujemy znaki (sorted zwraca listę) i łączymy je z powrotem w string
    wynik = "".join(sorted(polaczone))
    
    return wynik

def wymien_aktywnych_uzytkownikow(TYP_POLACZENIA: int, username: str = "", destination_username: str = "", data: str = "", operateOnSystem: bool = True) -> str:
    """Funkcja bauzjąca na stronie rentry.co w celu uzyskania IPv4 aktywnych użytkowników."""

    client, cookie = UrllibClient(), SimpleCookie()
    cookie.load(vars(client.get(f"https://rentry.co"))['headers']['Set-Cookie'])
    csrftoken = cookie['csrftoken'].value


    URLs = {
        0: "https://rentry.co/api/new",
        1: f"https://rentry.co/api/fetch/tunnel-{username}-{destination_username}-gesly",
        2: "https://rentry.co/api/edit/",
        3: "https://rentry.co/api/delete/tunnel-{username}-{destination_username}-gesly",
        9: "https://rentry.co/api/edit/tunnel-system-gesly",
    }
    
    # W dacie mamy nasze IPv4. Nadpisujemy je naszą nazwą użytkownika.
    if TYP_POLACZENIA == 1 or TYP_POLACZENIA == 2:
        data = f"{username}:{data}"
    
    _headers = {"Referer": f"https://rentry.co"}
    
    payloads = {
        0: {
            "csrfmiddlewaretoken": csrftoken,
            "text": data,
            "edit_code": f"{algorytm(username, destination_username)}",
            "url": f"tunnel-{username}-{destination_username}-gesly",
        },
        1: {
            "csrfmiddlewaretoken": csrftoken,
            "text": f"tunnel-system-gesly" if operateOnSystem else f"tunnel-{username}-{destination_username}-gesly",
            "edit_code": f"GeslySystemPassword123" if operateOnSystem else f"{algorytm(username, destination_username)}",
        },
        2: {
            "do": "zaimplementowania",
        },
        3: {
            "do": "zaimplementowania",
        },
        9: {
            "csrfmiddlewaretoken": csrftoken,
            "text": data,
            "edit_code": "GeslySystemPassword123",
            "url": "tunnel-system-gesly",
        },
    }
    
    if TYP_POLACZENIA == 0:
        result_create = client.post(f"https://rentry.co/api/new", payloads[TYP_POLACZENIA], headers=_headers)
        # print(result_create)
        return "Stworzono tunel."
    elif TYP_POLACZENIA == 1:
        url = f"tunnel-system-gesly" if operateOnSystem else f"tunnel-{username}-{destination_username}-gesly"
        result_fetch = client.post(f"https://rentry.co/api/fetch/{url}", payloads[TYP_POLACZENIA], headers=_headers).data
        # print(result_fetch)
        return result_fetch
    elif TYP_POLACZENIA == 9:
        result_update = client.post(f"https://rentry.co/api/new", payloads[TYP_POLACZENIA], headers=_headers)
        print(result_update.data)
        return "Zaktualizowano dane systemowe."

wymien_aktywnych_uzytkownikow(9, data="Zawartosc")

# def sluchaj(soc):
#     """Odbieranie wiadomości w tle."""
#     while True:
#         try:
#             data, addr = soc.recvfrom(1024)
#             print(f"\n[KOLEGA {addr}]: {data.decode('utf-8')}")
#             print("Ty: ", end="", flush=True)
#         except:
#             break

# def start_chat():
#     # 1. Lista serwerów, które u Ciebie działają
#     serwery_stun = [
#         'stun1.l.google.com',
#         'stun2.l.google.com',
#         'stun.l.google.com',
#         'stun.ekiga.net'
#     ]

#     local_port = 2137
#     external_ip = None
#     external_port = None
#     nat_type = None

#     print(f"--- Inicjalizacja (Port lokalny: {local_port}) ---")

#     # 2. Szukanie działającego serwera STUN przy zachowaniu portu
#     for host in serwery_stun:
#         try:
#             print(f"Próba: {host}...", end=" ")
#             # Bardzo ważne: source_port musi być taki sam jak port, na którym będziemy słuchać
#             nat_type, external_ip, external_port = stun.get_ip_info(
#                 stun_host=host, 
#                 source_port=local_port
#             )
#             if external_ip:
#                 print("SUKCES!")
#                 break
#         except Exception:
#             print("Błąd.")

#     if not external_ip:
#         print("\nNie udało się połączyć z żadnym serwerem STUN. Sprawdź internet.")
#         return

#     print("\n" + "="*40)
#     print(f"TWOJE DANE:")
#     print(f"IP:   {external_ip}")
#     print(f"PORT: {external_port}")
#     print(f"NAT:  {nat_type}")
#     print("="*40 + "\n")

#     # 3. Tworzenie gniazda do rozmowy
#     soc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#     soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
#     try:
#         soc.bind(('0.0.0.0', local_port))
#     except Exception as e:
#         print(f"Błąd bindowania portu: {e}")
#         return
    
#     # 4. Wymiana danych z kolegą przez rentry.co
#     username = input("Twoja nazwa użytkownika: ").strip()
    
#     wymi
    

#     # 5. Dane kolegi

    

#     # 6. Start czatu
#     threading.Thread(target=sluchaj, args=(soc,), daemon=True).start()

#     print("\n--- CZAT AKTYWNY (wpisz 'exit' by wyjść) ---")
#     print("Wskazówka: Jeśli wiadomości nie dochodzą, wyślijcie 'test' obaj w tym samym momencie.")
    
#     while True:
#         msg = input("Ty: ")
#         if msg.lower() == 'exit':
#             break
#         if msg:
#             soc.sendto(msg.encode('utf-8'), (peer_ip, peer_port))

# if __name__ == "__main__":
#     try:
#         start_chat()
#     except KeyboardInterrupt:
#         print("\nZamykanie...")
#         sys.exit()
