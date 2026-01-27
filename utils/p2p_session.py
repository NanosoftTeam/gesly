import socket

import stun

import threading


class P2PSession:
    def __init__(self):
        self.servers = {
            'stun1.l.google.com',
            'stun2.l.google.com',
            'stun.l.google.com',
            'stun.ekiga.net'
        }
        self.local_port = 6676
        self.external_ip = None
        self.external_port = None
        self.nat_type = None

    def listen(self):
        """Funkcja odpowiedzialna za nasłuchiwanie na danym gnieździe UDP."""
        while True:
            try:
                data, addr = self.soc.recvfrom(1024)
                print(f"Received message: {data.decode()} from {addr}")
            except Exception as ListeningException:
                print(f"Błąd odbierania wiadomości: {ListeningException}")
                break

    def findWorkingSTUN(self):
        """Funkcja odpowiedzialna za znalezienie działającego serwera STUN."""
        """Zwraca zewnętrzny adres IP i port."""
        for host in self.servers:
            try:
                print(f"Próba: {host}...", end=" ")
                nat_type, external_ip, external_port = stun.get_ip_info(
                    stun_host=host,
                    source_port=self.local_port
                )
                if external_ip:
                    print("Połączenie z serwerem STUN powiodło się.")
                    break
            except Exception as STUNException:
                print(f"Wystąpił błąd podczas połączenia z serwerem STUN: {STUNException}")

        if not external_ip:
            print("\nNie udało się połączyć z żadnym serwerem STUN. Sprawdź łącze internetowe.")
            return

        return external_ip, external_port

    def sluchaj(self):
        """Odbieranie wiadomości w tle."""
        while True:
            try:
                # Magia odbierania wiadomości, omg
                data, addr = self.soc.recvfrom(1024)
                print(f"\n[KOLEGA {addr}]: {data.decode('utf-8')}")
                print("Ty: ", end="", flush=True)
            except Exception as e:
                print(f"Błąd odbierania wiadomości: {e}")
                break

    def start(self):
        # 3. Tworzenie gniazda do rozmowy
        self.soc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Bindowanie portu
        try:
            self.soc.bind(('0.0.0.0', self.local_port))
        except Exception as e:
            print(f"Błąd bindowania portu: {e}")
            return

        threading.Thread(target=self.sluchaj, daemon=True).start()

        # usernames = [x.split()[0].rstrip("-") for x in users]
        # ips = [x.split()[1] for x in users]
        #
        # print("Sprawdzanie, czy podana nazwa użytkownika istnieje w toku...")
        #
        # # Czy nazwa użytkownika już istnieje?
        # if (username_input in usernames):
        #     index = usernames.index(username_input)
        #     if f"{external_ip}:{external_port}" == ips[index]:
        #         print("Podana nazwa użytkownika należy do Ciebie...")
        #     else:
        #         print("Podana nazwa użytkownika należy do kogoś innego. Wybierz inną nazwę.")
        #         # Powrót to wybierania nazwy użytkownika -> Do implementacji !!!
        # else:
        #     print("Nie wykryto użytkownika o podanej nazwie.")
        #     print("Nadpisywanie bazy danych w toku...")
        #
        #     # Nadpisanie bazy danych
        #     # try:
        #     #     operacja(2, username=username_input, data=f"{external_ip}:{external_port}", operateOnSystem=True)
        #     # except TunnelUpdateException as e:
        #     #     print(f"Błąd aktualizacji danych użytkowników: {e}")
        #     #     return
        #
        # print("Oczekiwanie na użytkowników w toku...")

    def send(self, peer_ip, peer_port, msg):
        # while True:
            # msg = input("Ty: ")
            # if msg.lower() == 'exit':
            #     break
        if msg:
            self.soc.sendto(msg.encode('utf-8'), (peer_ip, int(peer_port)))


