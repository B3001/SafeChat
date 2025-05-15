import socket
import threading
import SafeChat_Verschlüsselung as crypt

#nur eine connection wird benötigt wenn man mit einem thread jeweils nur empfangt und der andere sendet

# Funktion erstellen für key_exchange und Variable mit IP und jeweiligen Schlüssel (Funktion wird immer aufgerufen, wenn man mit einem anderen Client schreibt).


class ChatProcessor:
    def __init__(self):
        self.final_keys = {}  # {IP: key} (später halt Benutzer)
        self.sock_lock = threading.Lock()
        self.private_key = crypt.DH_generate_private_key()
        self.tcp_s = None

    def find_server(self):
        # Socket erstellen
        udp_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        udp_s.settimeout(5)

        # Broadcast: "SafeChat_Client". 
        udp_s.sendto(b"SafeChat_Client", ("<broadcast>", 5005))

        try:
            # Warten auf Antwort von dem Server
            data, server = udp_s.recvfrom(1024)
            if data == b"SafeChat_Server":
                print("Server gefunden unter IP:", server[0])
                
                # Hier wird die TCP-Verbindung aufgebaut
                self.tcp_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.tcp_s.connect((server[0], 3001))
                
                thread = threading.Thread(target=self.receive_data, args=(self.tcp_s,), daemon=True)
                thread.start()
                
                return True
        except socket.timeout:
            print("Kein Server gefunden – Timeout.")
            return False

    def receive_data(self, sock):
        while True:
            try:
                received_data = sock.recv(1024).decode()
                if received_data:
                    source, message = received_data.split("$", 1)
                    print(f"Message: {message}")
                    if source in self.final_keys:
                        decrypto = crypt.Str_encrypt(message, self.final_keys[source])
                        print(f"\n Nachricht von {source}: {decrypto}")
                    else:
                        print(f"\n per2change (receive_data): {message}")

                        # sende eigene Änderung
                        per1change = crypt.DH_calculate_change(self.private_key)
                        print(f"per1change (receive_data): {per1change}")
                        per1change = str(per1change)
                        dh_data = source + "$" + per1change
                        while True:
                            try:
                                self.sock_lock.acquire()
                                self.tcp_s.sendall(dh_data.encode())
                                break
                            finally:
                                self.sock_lock.release()

                        per2change = int(message)
                        self.final_keys[source] = crypt.DH_calculate_change(self.private_key, per2change)
                        print(f"Final key: {self.final_keys[source]}")
                else:
                    break
            except Exception as e:
                print("Fehler beim Empfangen:", e)
                break

    def send_data(self, destination_client, message): 
        if destination_client not in self.final_keys: # DH falls noch kein Key vorhanden
            #macht und sendet erste Änderung
            per1change = crypt.DH_calculate_change(self.private_key)
            print(f"per1change: {per1change}")
            per1change = str(per1change)
            dh_data = destination_client + "$" + per1change
            while True:
                try:
                    self.sock_lock.acquire() #lock
                    self.tcp_s.sendall(dh_data.encode())
                    break
                finally:
                    self.sock_lock.release()

            #empfängt geänderten Public Key von anderem Benutzer
            received_change = self.tcp_s.recv(1024).decode() #hier kann noch ein Error auftreten, wenn hier von einem anderen Benutzer empfangen wird wie davor
            source, per2change = received_change.split("$", 1)
            print(f"per2change: {per2change}")

            #macht zweite Änderung und schreibt Key in dictionary
            per2change = int(per2change)
            self.final_keys[source] = crypt.DH_calculate_change(self.private_key, per2change)
            print(f"Final key: {self.final_keys[source]}")

        crypto = crypt.Str_encrypt(message, self.final_keys[destination_client])
        data = destination_client + "$" + crypto

        self.sock_lock.acquire()
        self.tcp_s.sendall(data.encode())
        self.sock_lock.release()

class ChatInterface:
    def __init__(self, processor: ChatProcessor):
        self.processor = processor

    def start(self):
        print(f"private_key: {self.processor.private_key}")

        # Wichtig, weil das Programm bei keinen Server nicht einfach weiterlaufen soll
        if not self.processor.find_server():
            return

        while True:
            while True:
                destination_client = input("Empfänger eingeben (z.B. 127.0.0.1) oder exit zum beenden: ")
                if "$" in destination_client:
                    print("Es darf kein $ in der Adresse sein!")
                else:
                    break

            if destination_client == "exit":
                break

            message = input("Nachricht eingeben: ")
            self.processor.send_data(destination_client, message)

        self.processor.tcp_s.close()


if __name__ == "__main__":
    processor = ChatProcessor()
    interface = ChatInterface(processor)
    interface.start()
