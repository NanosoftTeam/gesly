import sys
from utils.rentry_session import RentrySession
from utils.p2p_session import P2PSession


# Inicjalizacja sesji P2P
p2p_session = P2PSession()

# Wyszukiwanie działającego serwera STUN
stun_result = p2p_session.findWorkingSTUN()
if not stun_result:
    print("❌ Nie udało się odnaleźć działającego serwera STUN.")
    sys.exit(1)

external_ip, external_port = stun_result
print(f"\n🌍 Twój adres zewnętrzny: {external_ip}:{external_port}")

# Rejestracja użytkownika
nickname = input("Twój nick: ")
rentry_session = RentrySession(nickname)
rentry_session.updateIP(external_ip, external_port)

# Wyświetlenie dostępnych użytkowników
print("\n📋 Dostępni użytkownicy:")
for user in rentry_session.getUsers():
    print(user)

# Wybór rozmówcy
target_nick = input("\nNick rozmówcy: ")
peer = rentry_session.getUser(nick=target_nick)
print(peer)

# Start nasłuchu połączeń
p2p_session.start()

# Dane drugiej strony
peer_ip, peer_port = peer[1].split(":")
peer_port = int(peer_port)

# NAT Hole Punching
print("\n🔓 Otwieranie NAT (PING)...")
p2p_session.send(peer_ip, peer_port, "PING")

# Pętla czatu
print("\n💬 Możesz pisać wiadomości (wpisz 'exit', aby zakończyć)\n")
while True:
    message = input("Ty: ")
    if message.lower() == "exit":
        print("👋 Zakończono rozmowę.")
        rentry_session.deleteIP()  # Usunięcie wpisu z Rentry
        break
    p2p_session.send(peer_ip, peer_port, message)