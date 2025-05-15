import socket
import threading
import SafeChat_Verschlüsselung as crypt

#nur eine connection wird benötigt wenn man mit einem thread jeweils nur empfangt und der andere sendet

# Funktion erstellen für key_exchange und Variable mit IP und jeweiligen Schlüssel (Funktion wird immer aufgerufen, wenn man mit einem anderen Client schreibt).
# Verschlüsselung muss noch ausgebaut werden, sodass man nicht gleichzeitig absenden muss. (mit Thread)


# glogbale Variable mit keys? Tupel: {IP: key}   (ohne extra $$$)
def receive_data(sock): # nicht gleichzeitig senden müssen???????????????????
    while True:
        try:
            received_data = sock.recv(1024).decode()
            if received_data:
                source, message = received_data.split("$", 1)
                print(f"Message: {message}")
                if source in final_keys:
                    decrypto = crypt.Str_encrypt(message, final_keys[source])
                    print(f"\n Nachricht von {source}: {decrypto}")
                else:
                    print(f"\n per2change (receive_data): {message}")
                    
                    #senden von eigener Änderung
                    per1change = crypt.DH_calculate_change(private_key)
                    print(f"per1change (receive_data): {per1change}")
                    per1change = str(per1change)
                    dh_data = source + "$" + per1change
                    while True:
                        try:
                            sock_lock.acquire() #lock
                            tcp_s.sendall(dh_data.encode())
                            break
                        finally:
                            sock_lock.release()
                    
                    #finalen Key berechnen
                    per2change = int(message)
                    final_keys[source] = crypt.DH_calculate_change(private_key, per2change)
                    print(f"Final key: {final_keys[source]}")
            else:
                break
        except Exception as e:
            print("Fehler beim Empfangen:", e)
            break
        

#Globale Variable mit Keys
global final_keys
final_keys = {} # {IP: Key} (später halt Benutzer)

#Lock erstellen für senden in receive_data()  (und später send_data)
global sock_lock
sock_lock = threading.Lock()

# DH
global private_key
private_key = crypt.DH_generate_private_key()
print(f"private_key: {private_key}")

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
        tcp_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_s.connect((server[0], 3001))
        
        receive_thread = threading.Thread(target=receive_data, args=(tcp_s,), daemon=True)
        receive_thread.start()
        
        
        while True:
            while True:
                destination_client = input("Empfänger eingeben (z.B. 127.0.0.1) oder exit zum beenden: ")
                if "$" in destination_client:
                    print("Es darf kein $ in der Adresse sein!")
                else:
                    break
            if destination_client == "exit":
                break
            
            
            if destination_client not in final_keys: # DH falls noch kein Key vorhanden
                #macht und sendet erste Änderung
                per1change = crypt.DH_calculate_change(private_key)
                print(f"per1change: {per1change}")
                per1change = str(per1change)
                dh_data = destination_client + "$" + per1change
                while True:
                    try:
                        sock_lock.acquire() #lock
                        tcp_s.sendall(dh_data.encode())
                        break
                    finally:
                        sock_lock.release()
                
                #empfängt geänderten Public Key von anderem Benutzer
                received_change = tcp_s.recv(1024).decode()  #hier kann noch ein Error auftreten, wenn hier von einem anderen Benutzer empfangen wird wie davor
                source, per2change = received_change.split("$", 1) 
                print(f"per2change: {per2change}")
                
                #macht zweite Änderung und schreibt Key in dictionary
                per2change = int(per2change)
                final_keys[source] = crypt.DH_calculate_change(private_key, per2change)
                print(f"Final key: {final_keys[source]}")
                
            
            message = input("Nachricht eingeben: ")
            
            crypto = crypt.Str_encrypt(message, final_keys[destination_client])
            
            data = destination_client + "$" + crypto
            
            sock_lock.acquire()
            tcp_s.sendall(data.encode())
            sock_lock.release()

    tcp_s.close()
    
except socket.timeout:
    print("Kein Server gefunden – Timeout.")