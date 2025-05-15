import socket
import threading
import time

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
                data = conn.recv(1024).decode()
                print("Nachricht bekommen")
                
                #Nachricht in messages schreiben
                destination, message = data.split("$", 1) #split destination$message
                
                #messages locken
                while True:
                    try:
                        tupel_lock.acquire()
                        if destination not in messages:
                            messages[destination] = []
                        messages[destination].append((addr, message))
                        break
                    except:
                        time.sleep(1)
                        print("warten auf lock")
                    finally:
                        tupel_lock.release()
                print(messages)
            except:
                print("Fehler bei client_receive")
                break
    print("Client-Verbindung geschlossen")
    #später benutzer und addr aus liste löschen (dictionary mit key: addr und value: benutzer)
            
def client_send(conn, addr): # überprüfen ob Nachricht für addr vorhanden ist und sendet diese
    with conn:
        while True:
            try:
                #{IP: [(source, message),...]}
                print(messages)
                #if messages[addr] is not None or not []: #messages["192.168.85.1"] fehler weil noch nicht addr vorhanden in tupel!!!!!!!
                if addr in messages and messages[addr]: #if liste: ist True wenn etwas in der liste ist
                    print("vor lock")
                    try:
                        #lock
                        tupel_lock.acquire()
                        
                        source = str(messages[addr][0][0][0]) #source??????????????
                        #print(destination)
                        message = str(messages[addr][0][1])
                        #print(message)
                        
                        data = source + "$" + message #destination + "$" + message
                        conn.sendall(data.encode())
                        messages[addr].pop(0) #aus messages löschen
                        print("Nachricht weitergeleitet")
                    finally:
                        tupel_lock.release()
                time.sleep(1)
            except Exception as e:
                print("Fehler bei client_send: ", e)
                time.sleep(1)
            except:
                print("Fehler bei client_send")
                time.sleep(1)
    
    
def tcp_server():
    tcp_sock = socket.socket()
    tcp_sock.bind(("", 3001))
    tcp_sock.listen(5)  

    #später benutzer und aktuelle addr in liste speichern, damit client_send benutzer weiß (dictionary mit key: addr und value: benutzer)
    global messages
    messages = {} #{IP: [(source, message),...]} (auch später Benutzer)
    
    while True:
        conn, addr = tcp_sock.accept()
        #print(addr)
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
