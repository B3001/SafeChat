import socket
import threading
import time

# lock für DH_Data

def IP_Handler(): # antwortet auf UDP-Anfrage
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.bind(("", 5005))  # "" hört auf alle Interfaces

    print("Warten auf IP-Anfrage eines Clients")

    while True:
        data, addr = udp_sock.recvfrom(1024)

        if data == b"SafeChat_Client":
            udp_sock.sendto(b"SafeChat_Server", addr)
            print("Antwort auf IP-Anfrage gesendet")


def client_receive(conn, addr):
    print("Neue Client-Verbindung")
    with conn: # conn wird automatisch geschlossen wenn Verbindung getrennt
        
        # veränderten Public Key empfangen und zwischenspeichern
        try:
            message = conn.recv(1024).decode()
            DH_Data[addr[0]] = message
        except:
            print("Fehler beim empfangen von DH-Daten")
        print("DH_Data: ", end = "")
        print(DH_Data)
        
        
        while True:
            try:
                # auf Nachricht warten
                data = conn.recv(1024).decode()
                print(f"Nachricht bekommen: {data}")
                
                # Nachricht in messages schreiben
                destination, message = data.split("$", 1) #split destination$message oder Server$DH-Wert
                
                # Nachricht verarbeiten
                while True:
                    try:
                        tupel_lock.acquire()
                        if (destination not in messages) and not ("Get_DH_Data" in message):
                            messages[destination] = []
                        if addr[0] not in messages:
                            messages[addr[0]] = []
                        
                        print("DH_Data: ", end="")
                        print(DH_Data)
                        
                        if "Get_DH_Data" in message:
                            destination = message.split("$")[1]
                            
                            if destination not in messages:
                                messages[destination] = []
                                
                            try:
                                # DH-Daten an beide Clients senden
                                if addr[0] in DH_Data:
                                    if destination != addr[0]:
                                        print(f"desti: {destination}, dh: {DH_Data[destination]}")
                                        messages[addr[0]].append((destination, DH_Data[destination]))
                                    messages[destination].append((addr[0], DH_Data[addr[0]]))
                            except: # falls addr[0] nicht in DH_Data, dann gibt es den Client nicht
                                messages[addr[0]].append(("Server", destination)) #Client nicht verfügbar
                        else: # falls kein Key-Exchange wird Nachricht weitergeleitet
                            messages[destination].append((addr[0], message))
                    except:
                        time.sleep(1)
                        print("Fehler bei client_receive")
                    finally:
                        tupel_lock.release()
                        break
                print("Messages: ", end="")
                print(messages)
            except:
                print("Client-Verbindung geschlossen")
                break
    del DH_Data[addr[0]]
    del messages[addr[0]]
            
def client_send(conn, addr): # überprüfen ob eine Nachricht für addr vorhanden ist und diese senden
    with conn:
        while True:
            try:
                #{IP: [(source, message),...]}
                if addr in messages and messages[addr]: # ist True wenn etwas in der Liste ist
                    try:
                        tupel_lock.acquire()
                        
                        source = str(messages[addr][0][0])#[0])----------------------------------------------
                        message = str(messages[addr][0][1])
                        
                        data = source + "$" + message
                        conn.sendall(data.encode())
                        messages[addr].pop(0) # gesendete Nachricht aus messages löschen
                        print("Nachricht weitergeleitet")
                        print(messages)
                    finally:
                        tupel_lock.release()
                time.sleep(1)
            except:
                print("Fehler bei client_send")
                time.sleep(1)
    
    
def tcp_server():
    tcp_sock = socket.socket()
    tcp_sock.bind(("", 3001))
    tcp_sock.listen(5) # bis zu 5 Clients

    # globale Variablen
    global messages
    messages = {} #{IP: [(source, message),...]}
    global DH_Data
    DH_Data = {} #{IP: veränderter Public Key}
    
    # Threads für Verbindungen starten
    while True:
        conn, addr = tcp_sock.accept()
        client_receive_thread = threading.Thread(target=client_receive, args=(conn, addr), daemon=True)
        client_send_thread = threading.Thread(target=client_send, args=(conn, addr[0]), daemon=True)
        client_receive_thread.start()
        client_send_thread.start()


tupel_lock = threading.Lock()

if __name__ == "__main__":
    # IP-Handler starten
    udp_thread = threading.Thread(target=IP_Handler, daemon=True)
    udp_thread.start()

    # TCP-Server starten
    tcp_server()
