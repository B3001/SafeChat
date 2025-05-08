import socket
import threading
import SafeChat_Verschlüsselung as crypt

#nur eine connection wird benötigt wenn man mit einem thread jeweils nur empfangt und der andere sendet

# Funktion erstellen für key_exchange und Variable mit IP und jeweiligen Schlüssel (Funktion wird immer aufgerufen, wenn man mit einem anderen Client schreibt).
# Verschlüsselung muss noch ausgebaut werden, sodass man nicht gleichzeitig absenden muss.

# Funktion für den Empfänger-Thread, um die Nachrichten im richtigen Format zu bekommen.
def receive_data(sock): # Mit return fixen
    while True:
        try:
            received_data = sock.recv(1024).decode()
            if received_data:
                destination, message = received_data.split("$", 1)
                return message
                print(f"\n Nachricht von {destination}: {message}")
            else:
                break
        except Exception as e:
            print("Fehler beim Empfangen:", e)
            break
        
def receive_encrypted_data(sock, key): # Entschlüsselung noch
    while True:
        try:
            received_data = sock.recv(1024).decode()
            if received_data:
                destination, message = received_data.split("$", 1)
                print(f"Message: {message}")
                decrypto = crypt.Str_encrypt(message, key)
                print(f"\n Nachricht von {destination}: {decrypto}")
            else:
                break
        except Exception as e:
            print("Fehler beim Empfangen:", e)
            break


# Socket erstellen
udp_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
udp_s.settimeout(5)

# Schickt an alle eine Nachricht: "SafeChat_Client". Alle die es erwarten.
udp_s.sendto(b"SafeChat_Client", ("<broadcast>", 5005))

try:
    # Warten auf Antwort von dem Server
    data, server = udp_s.recvfrom(1024)
    if data == b"SafeChat_Server":
        print("Server gefunden unter IP:", server[0])

        # Hier wird die TCP-Verbindung aufgebaut
        tcp_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_s.connect((server[0], 3001))
        
        #Hier DH
        private_key = crypt.DH_generate_private_key()
        print(f"private_key: {private_key}")
        per1change = crypt.DH_calculate_change(private_key)
        print(f"per1change: {per1change}")
        per1change = str(per1change)
        IP = input("IP-Adresse eingeben: ")
        per_data = IP + "$" + per1change
        tcp_s.sendall(per_data.encode())
        per2change = receive_data(tcp_s)
        print(f"per2change: {per2change}")
        per2change = int(per2change)
        final_key = crypt.DH_calculate_change(private_key, per2change)
        print(f"Final key: {final_key}")
    
        receive_thread = threading.Thread(target=receive_encrypted_data, args=(tcp_s, final_key), daemon=True)
        receive_thread.start()
        
    
        while True: # Verschlüsseln der Nachricht (passt jz hoffentlich)
            while True:
                destination_client = input("Empfänger eingeben (z.B. 127.0.0.1) oder exit zum beenden: ")
                if "$" in destination_client:
                    print("Es darf kein $ in der Adresse sein!")
                else:
                    break
            if destination_client == "exit":
                break
            
            message = input("Nachricht eingeben: ")
            
            crypto = crypt.Str_encrypt(message, final_key)
            
            data = destination_client + "$" + crypto
            tcp_s.sendall(data.encode())
        
    tcp_s.close()
    
except socket.timeout:
    print("Kein Server gefunden – Timeout.")