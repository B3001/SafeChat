"""
Dieser Code stellt ein Prototyp für die GUI dar. Als Beispiel gibt sie alles aus, was der Benutzer eingibt.
Dieser Code dient zur Darstellungszwecken und kann beim Endcode abweichen.
"""

import tkinter as tk
from tkinter import scrolledtext

# Funktion, für das Textfeld um Nachrichten zu schreiben und es dann ins Display anzuzeigen
def send_message(event=None):
    # Nimmt die Nachricht aus dem geschriebenen Textfeld
    message = textfeld.get()
    # Falls eine Nachricht dann existiert, soll die Nachricht im richtigen Format ausgegeben werden
    if message:
        display_message("Du", message)
        # Löscht die gesamte Eingabe im Textfeld, stört weniger
        textfeld.delete(0, tk.END)

# Funktionseinstellungen für das Display
def display_message(sender, message):
    # Displaykonfiguration muss umgestellt werden, da man sonst nichts reinschreiben kann
    chat_display.config(state='normal')
    # Sender und Nachricht reinschreiben
    chat_display.insert(tk.END, f"{sender}: {message}\n")
    # Scrollt automatisch mit, wenn es notwendig ist
    chat_display.yview(tk.END)
    # Displaykonfiguration wieder zurück auf disabled umstellen, sonst kann man da irgendwas reinschreiben ausversehen
    chat_display.config(state='disabled')

# Fenster erstellen
root = tk.Tk()
root.title("SafeChat")
root.geometry("400x300")
# Fenster kann nicht größer und kleiner gemacht werden
root.resizable(False, False)

# Erstellt ein mehrzeiliges Textfeld mit Scrollbar
chat_display = scrolledtext.ScrolledText(root, wrap=tk.WORD, state='disabled', font=("Arial", 11))
chat_display.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)

# Erstellt ein Textfeld
textfeld = tk.Entry(root, font=("Arial", 12))
textfeld.grid(row=1, column=0, sticky="ew", padx=(10, 5), pady=(0, 10))
# Wenn man die Entertaste drückt, wird auch send_message aufgerufen)
textfeld.bind("<Return>", send_message)

# Erstellt ein Senden-Button
send_button = tk.Button(root, text="▶", bg="#58855C", fg="white", font=("Arial", 12, "bold"), command=send_message)
send_button.grid(row=1, column=1, sticky="ew", padx=(5, 10), pady=(0, 10))

# Fenster bleibt auf ihrer gleichen Auflösung, egal ob es sich maximiert oder sonst was
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)

root.mainloop()
