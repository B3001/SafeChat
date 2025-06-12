import socket
import threading
import SafeChat_Verschlüsselung as crypt
import time
import tkinter as tk
from tkinter import scrolledtext

class ChatProcessor:
    def __init__(self):
        self.final_keys = {}  # {IP: key} (später halt Benutzer)
        self.sock_lock = threading.Lock()
        self.private_key = crypt.DH_generate_private_key()
        self.tcp_s = None
        self.gui = None 

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
                        decrypto = crypt.Str_encrypt(message, self.final_keys[source])
                        print(f"\n Nachricht von {source}: {decrypto}")
                        
                        if self.gui:
                            self.gui.root.after(0, self.gui.show_message, source, decrypto)
                            
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
            while True:
                if (destination_client in self.final_keys) or (self.final_keys["Server"] == destination_client):
                    # break, wenn Key vorhanden oder "Client nicht verfügbar"
                    break
                else:
                    time.sleep(1)

        if self.final_keys["Server"] != destination_client:
            crypto = crypt.Str_encrypt(message, self.final_keys[destination_client])
            data = destination_client + "$" + crypto

            self.sock_lock.acquire()
            self.tcp_s.sendall(data.encode())
            self.sock_lock.release()
        else:
            self.final_keys["Server"] = ""
            print("Client nicht verfügbar")

class ChatInterface:
    def __init__(self, processor: ChatProcessor):
        self.processor = processor
        self.processor.gui = self
        self.root = tk.Tk()
        self.root.title("SafeChat")
        self.root.geometry("400x300")
        self.root.resizable(False, False)
        
        # Erstellt ein mehrzeiliges Textfeld mit Scrollbar
        self.chat_display = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, state='disabled', font=("Arial", 11))
        self.chat_display.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)

        # Erstellt ein Textfeld für Nachrichten
        self.message_entry = tk.Entry(self.root, font=("Arial", 12))
        self.message_entry.grid(row=2, column=0, columnspan=2, sticky="ew", padx=(10, 5), pady=(0, 10))
        self.message_entry.bind("<Return>", self.send_message)

        # Empfängerfeld für die IP
        self.receiver_label = tk.Label(self.root, text="Empfänger-IP:", font=("Arial", 10))
        self.receiver_label.grid(row=1, column=0, padx=10, pady=(0, 5), sticky="w")
        self.receiver_entry = tk.Entry(self.root, font=("Arial", 11))
        self.receiver_entry.grid(row=1, column=1, columnspan=2, sticky="ew", padx=10, pady=(0, 5))

        # Erstellt ein Senden-Button
        self.send_button = tk.Button(self.root, text="▶", bg="#58855C", fg="white", font=("Arial", 12, "bold"), command=self.send_message)
        self.send_button.grid(row=2, column=2, sticky="ew", padx=(5, 10), pady=(0, 10))

        # Fenster bleibt auf ihrer gleichen Auflösung, egal ob es sich maximiert oder sonst was
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

    def send_message(self, event=None):
        destination_client = self.receiver_entry.get().strip()
        message = self.message_entry.get().strip()

        if not destination_client or not message:
            return  # Felder dürfen nicht leer sein

        if "$" in destination_client:
            self.chat_display.config(state='normal')
            self.chat_display.insert(tk.END, "Es darf kein $ in der Adresse sein!\n")
            self.chat_display.config(state='disabled')
            return
        
        if len(message) > (1024-15): # 15 ist max len von einer IP
            self.chat_display.config(state='normal')
            self.chat_display.insert(tk.END, f"Nachricht zu lang! Max. 1009 Zeichen erlaubt.\n")
            self.chat_display.config(state='disabled')
            return
        
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, f"Du: {message}\n")
        self.chat_display.config(state='disabled')
        self.processor.send_data(destination_client, message)
        self.message_entry.delete(0, tk.END)
        
    def show_message(self, sender, message):
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, f"{sender}: {message}\n")
        self.chat_display.config(state='disabled')
        self.chat_display.yview(tk.END)
    
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
        # GUI laufen lassen
        self.root.mainloop()
            
        self.processor.tcp_s.close()

if __name__ == "__main__":
    processor = ChatProcessor()
    interface = ChatInterface(processor)
    interface.start()
