import socket
import threading

#nur eine connection wird benötigt wenn man mit einem thread jeweils nur empfangt und der andere sendet

# Funktion für den Empfänger-Thread, um die Nachrichten im richtigen Format zu bekommen.
def receive_data(sock):
    while True:
        try:
            received_data = sock.recv(1024).decode()
            if received_data:
                destination, message = received_data.split("$", 1)
                print(f"\n Nachricht von {destination}: {message}")
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
    
        receive_thread = threading.Thread(target=receive_data, args=(tcp_s, ), daemon=True)
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
            
            message = input("Nachricht eingeben: ")
            
            data = destination_client + "$" + message
            tcp_s.sendall(data.encode())
        
    tcp_s.close()
    
except socket.timeout:
    print("Kein Server gefunden – Timeout.")