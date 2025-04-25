import socket
import threading

# Funktion für den Empfänger-Thread, um die Nachrichten im richtigen Format zu bekommen.
def receive_data(sock):
    while True:
        source_client = sock.recv(1024).decode()
        data = sock.recv(1024).decode()
        print(f"\n Nachricht von {source_client}: {data}")

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
    
        receive_thread = threading.Thread(target=receive_data, args=(tcp_s,), daemon=True)
        receive_thread.start()
    
        while True:
            destination_client = input()
            if destination_client == "exit":
                break  
            data = input()
            tcp_s.sendall(destination_client.encode())
            tcp_s.sendall(data.encode())
        
    tcp_s.close()
    
except socket.timeout:
    print("Kein Server gefunden – Timeout.")