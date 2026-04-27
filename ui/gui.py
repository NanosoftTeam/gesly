import tkinter as tk                                                                                                                                                                                                                          
from tkinter import messagebox
from tkinter import simpledialog

from utils import rentry_session
                                
import sys
from utils.rentry_session import RentrySession
from utils.p2p_session import P2PSession
             
def debug(DEBUG_MODE, DEBUG_MESSAGE):
    if DEBUG_MODE:
        print(f"\n [DEBUG] {DEBUG_MESSAGE}")
    
                                                                                                                                                                                                                                            
class Application(tk.Frame):                                                                                                                                                                                                                  
    def __init__(self, master=None):                                                                                                                                                                                                          
        super().__init__(master)                                                                                                                                                                                                              
        self.master = master
        # Zmieniać na True, aby wyłączyć debugowanie
        self.DEBUG_MODE = True
        self.pack()
        
        # ========= Funkcjonalność main.py ==========
        
        # Inicjalizacja sesji P2P
        self.p2p_session = P2PSession()
        
        stun_result = self.p2p_session.findWorkingSTUN()
        if not stun_result:
            debug(self.DEBUG_MODE, "❌ Nie udało się odnaleźć działającego serwera STUN.")
            sys.exit(1)
        
        self.external_ip, self.external_port = stun_result
        debug(self.DEBUG_MODE, f"\n [DEBUG] 🌍 Twój adres zewnętrzny: {self.external_ip}:{self.external_port}")
        
        self.create_widgets(self.login())
        
        # ==========================================
                
    def login(self):
        username = tk.simpledialog.askstring("Zaloguj się", "Wprowadź nazwę użytkownika:")
        if not username:
            return False
        
        self.rentry_session = RentrySession(username)
        if not self.rentry_session.verifyIfUserExists():
            messagebox.showerror("Error", "Użytkownik o takim nicku już istnieje. Wybierz inny.")
            self.master.destroy()
            return False
        self.rentry_session.updateIP(self.external_ip, self.external_port)
        return username

    def create_widgets(self, username):
        if not username:
            messagebox.showerror("Error", "Coś nie wyszło. Spróbuj ponownie.")
            self.master.destroy()
            return
        # Profile section at top
        profile_frame = tk.Frame(self, bg="lightgray", height=80)
        profile_frame.pack(side="top", fill="x")
        
        profile_label = tk.Label(profile_frame, text="Profile", font=("Arial", 12, "bold"), bg="lightgray")
        profile_label.pack(anchor="w", padx=10)
        
        user_label = tk.Label(profile_frame, text=f"User: {username}", bg="lightgray")
        user_label.pack(anchor="w", padx=10)
        
        # Messages section at bottom
        messages_frame = tk.Frame(self, bg="white")
        messages_frame.pack(side="bottom", fill="both", expand=True)
        
        messages_label = tk.Label(messages_frame, text="Messages", font=("Arial", 12, "bold"), bg="white")
        messages_label.pack(anchor="w", padx=10)
        
        self.messages_text = tk.Text(messages_frame, height=15, width=50, state="disabled")
        self.messages_text.pack(fill="both", expand=True, padx=10)
        
        # Input section
        input_frame = tk.Frame(self)
        input_frame.pack(side="bottom", fill="x")
        
        self.message_input = tk.Entry(input_frame)
        self.message_input.pack(side="left", fill="x", expand=True, padx=5)
        
        send_button = tk.Button(input_frame, text="Send", command=self.send_message)
        send_button.pack(side="right", padx=5)
        
        self.quit = tk.Button(self, text="QUIT", fg="red",
                            command=self.on_quit)
        self.quit.pack(side="bottom", pady=5)

    def send_message(self):
        message = self.message_input.get()
        if message:
            self.message_input.delete(0, tk.END)
            self.update_diagnostics()

    def on_quit(self):
        print("hello")
        self.master.destroy()

    def update_diagnostics(self):
        # TO DO: implement diagnostics logic
        pass

root = tk.Tk()
root.geometry("400x500+100+100")
root.resizable(False, False)
# 1. Hide the standard title bar
root.overrideredirect(True)

# 2. Force it to show in the Taskbar (Windows specific)
root.after(10, lambda: root.wm_attributes("-toolwindow", True))
# Or use this trick to force it back onto the taskbar:
root.lift()
root.attributes("-topmost", True) # Optional: keeps it on top
app = Application(master=root)
app.mainloop()