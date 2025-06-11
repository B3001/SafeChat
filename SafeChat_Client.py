import socket
import threading
import SafeChat_Verschlüsselung as crypt
import time

# lock für final_keys?

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

        # UDB-Broadcast: "SafeChat_Client". 
        udp_s.sendto(b"SafeChat_Client", ("<broadcast>", 5005))

        try:
            # Warten auf Antwort von dem Server
            data, server = udp_s.recvfrom(1024)
            if data == b"SafeChat_Server":
                print("Server gefunden bei IP:", server[0])
                
                # Hier wird die TCP-Verbindung aufgebaut
                self.tcp_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.tcp_s.connect((server[0], 3001))
                print(f"Eigene IP: {self.tcp_s.getsockname()[0]}")
                
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
                print(f"Received: {received_data}")
                if received_data:
                    source, message = received_data.split("$", 1)
                    
                    if source == "Server": # Client, an den gesendet werden soll nicht vorhanden
                        self.final_keys["Server"] = message
                    
                    elif source in self.final_keys: # wenn Key vorhanden einfach decrypten
                        #lock für final keys ?????????????????????????????????????????????????????????????????
                        decrypto = crypt.Str_encrypt(message, self.final_keys[source])
                        print(f"\n Nachricht von {source}: {decrypto}")
                    elif "Server" in message: # wenn in Nachricht "Server" dann DH -> final_key berechnen
                        per2change = int(message.split("$")[1])
                        print(per2change)
                        print(f"source: {source}")
                        self.final_keys[source] = crypt.DH_calculate_change(self.private_key, per2change)
                        print(f"Final key: {self.final_keys[source]}")
                        print(self.final_keys)
                    else:
                        print("Fehler: kein Key für Nachricht vorhanden")   
                else:
                    break
            except Exception as e:
                print("Fehler beim Empfangen:", e)
                break

    def send_data(self, destination_client, message): 
        if destination_client not in self.final_keys:
            # DH, falls noch kein Key für IP vorhanden
            data = "Server$Get_DH_Data" + "$" + str(destination_client)
            self.tcp_s.sendall(data.encode())
            
            # warten bis Key verfügbar
            while True: # lock für final_keys??????????????????????????????????????????????????----------------
                if (destination_client in self.final_keys) or (self.final_keys["Server"] == destination_client):
                    # break, wenn Key vorhanden oder "Client nicht verfügbar"
                    break
                else:
                    time.sleep(1)

        if self.final_keys["Server"] != destination_client:
            crypto = crypt.Str_encrypt(message, self.final_keys[destination_client])
            data = destination_client + "$" + crypto

            self.sock_lock.acquire()#kein lock?-----------------------------------------------
            self.tcp_s.sendall(data.encode())
            self.sock_lock.release()
        else:
            self.final_keys["Server"] = ""
            print("Client nicht verfügbar")

class ChatInterface:
    def __init__(self, processor: ChatProcessor):
        self.processor = processor

    def start(self):
        print(f"private_key: {self.processor.private_key}")

        # Wichtig, weil das Programm bei keinen Server nicht einfach weiterlaufen soll
        if not self.processor.find_server():
            return
        
        self.processor.final_keys["Server"] = ""
        
        # DH_changed senden (Server speichert diesen Wert)
        per1change = crypt.DH_calculate_change(self.processor.private_key)
        print(f"per1change: {per1change}")
        data = "Server" + "$" + str(per1change)
        self.processor.tcp_s.sendall(data.encode())

        # Nachrichten eingeben und senden
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
