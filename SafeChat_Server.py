import socket
import threading

def IP_Handler():
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.bind(("", 5005))  # "" hört auf alle Interfaces

    print("Warten auf IP-Anfrage eines Clients")

    while True:
        data, addr = udp_sock.recvfrom(1024)
        #print(f"UDP: Empfangen von {addr}: {data}")

        if data == b"SafeChat_Client":
            udp_sock.sendto(b"SafeChat_Server", addr)
            print("Antwort auf IP-Anfrage gesendet")


def client_receive(conn, addr):
    print("Neue Client-Verbindung")
    with conn: # conn wird automatisch geschlossen wenn Verbindung getrennt
        while True:
            try:
                #später in client_connections Benutzer dieser Verbindung hinzufügen
                destination_client = conn.recv(15)
                data = conn.recv(1024)
            except:
                print("Fehler")
                break
    #später benutzer und addr aus liste löschen (dictionary mit key: addr und value: benutzer)
            
def client_send(conn, addr): # überprüfen ob client-addr in liste gefunden: wenn ja wird Nachricht gesendet
    with conn:
        try:
            if messages[addr[0]] is not None:
                conn.sendall(messages[addr[0]][0][0]) #vlt addr[1][...
                conn.sendall(messages[addr[0]][0][1])
                #threading lock
                messages[addr[0]][0].pop(0) #aus messages löschen
    
    
def tcp_server():
    tcp_sock = socket.socket() #(socket.AF_INET, socket.SOCK_STREAM)
    tcp_sock.bind(("", 3001))
    tcp_sock.listen(5)  

    #später benutzer und aktuelle addr in liste speichern, damit client_send benutzer weiß (dictionary mit key: addr und value: benutzer)
    global messages
    messages = {} #{IP: [(source, data),...]} (auch später Benutzer)
    while True:
        conn, addr = tcp_sock.accept()
        client_receive_thread = threading.Thread(target=client_receive, args=(conn, addr), daemon=True)
        client_send_thread = threading.Thread(target=client_send, args=(conn, addr), daemon=True)
        client_receive_thread.start()
        client_send_thread.start()
        messages["addr[0]"] = [] #vlt addr[1]


if __name__ == "__main__":
    # IP-Handler starten
    udp_thread = threading.Thread(target=IP_Handler, daemon=True)
    udp_thread.start()

    # TCP-Server starten
    tcp_server()
