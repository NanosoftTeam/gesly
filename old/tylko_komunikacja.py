import socket
import stun
import threading
import sys


def sluchaj(soc):
    """Odbieranie wiadomości w tle."""
    while True:
        try:
            data, addr = soc.recvfrom(1024)
            print(f"\n[KOLEGA {addr}]: {data.decode('utf-8')}")
            print("Ty: ", end="", flush=True)
        except:
            break


def start_chat():
    # 1. Lista serwerów, które u Ciebie działają
    serwery_stun = [
        'stun1.l.google.com',
        'stun2.l.google.com',
        'stun.l.google.com',
        'stun.ekiga.net'
    ]

    local_port = 54320
    external_ip = None
    external_port = None
    nat_type = None

    print(f"--- Inicjalizacja (Port lokalny: {local_port}) ---")

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

    print("\n" + "=" * 40)
    print(f"TWOJE DANE DLA KOLEGI (Kopiuj wszystko!):")
    print(f"IP:   {external_ip}")
    print(f"PORT: {external_port}")
    print(f"NAT:  {nat_type}")
    print("=" * 40 + "\n")

    # 3. Tworzenie gniazda do rozmowy
    soc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        soc.bind(('0.0.0.0', local_port))
    except Exception as e:
        print(f"Błąd bindowania portu: {e}")
        return

    # 4. Dane kolegi
    try:
        peer_ip = input("Podaj IP KOLEGI: ").strip()
        peer_port = int(input("Podaj PORT KOLEGI: ").strip())
    except ValueError:
        print("Błędny port!")
        return

    # 5. Start czatu
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
        sys.exit()