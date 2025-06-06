import socket
import threading
import SafeChat_Verschlüsselung as crypt

# Neue Idee: bei Verbindung zum Server wird direkt der veränderte Public Key an den Server gesendet und dieser speichert ihn ab
# wenn ein anderer client jetzt diesem client schreiben will kann er den Wert verwenden


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

    def receive_data(self, sock): # wenn Nachricht von Server, dann DH--------------------------------------------
        while True:
            try:
                received_data = sock.recv(1024).decode()
                if received_data:
                    source, message = received_data.split("$", 1)
                    print(f"Message: {message}")
                    if source in self.final_keys: #--------------------------------------------------------------
                        #lock für final keys ?????????????????????????????????????????????????????????????????
                        decrypto = crypt.Str_encrypt(message, self.final_keys[source])
                        print(f"\n Nachricht von {source}: {decrypto}")
                    elif "Server" in message: # wenn source "Server" dann final_key berechnen
                        per2change = int(message.split("$")[1])
                        print(per2change)
                        self.final_keys[source] = crypt.DH_calculate_change(self.private_key, per2change)
                        print(f"Final key: {self.final_keys[source]}")
                    else: #DH falls noch kein key
                        # muss irgendwie Anfrage senden----------------------
                        print("Noch kein Key vorhanden")
                        
                else:
                    break
            except Exception as e:
                print("Fehler beim Empfangen:", e)
                break

    def send_data(self, destination_client, message): 
        if destination_client not in self.final_keys:
            # DH falls noch kein Key vorhanden---------------------------------------
            data = "Server$Get_DH_Data" + "$" + str(destination_client)
            self.tcp_s.sendall(data.encode())
            #warten bis DH empfangen
            while True: # lock für final_keys??????????????????????????????????????????????????
                if destination_client in self.final_keys: # oda warten auf lock
                    break

        crypto = crypt.Str_encrypt(message, self.final_keys[destination_client])
        data = destination_client + "$" + crypto

        self.sock_lock.acquire()#kein lock?-----------------------------------------------
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
        
        # DH_changed senden----------------------------------------------------------------------------------
        per1change = crypt.DH_calculate_change(self.processor.private_key)
        # senden
        data = "Server" + "$" + str(per1change)
        self.processor.tcp_s.sendall(data.encode())

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
