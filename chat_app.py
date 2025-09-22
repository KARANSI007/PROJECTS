import socket
import threading
import tkinter as tk
from tkinter import simpledialog, ttk, filedialog, messagebox
from datetime import datetime
import os
import base64
from PIL import Image, ImageTk

# ================= SERVER =================
clients = []

def handle_client(client_socket, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    while True:
        try:
            message = client_socket.recv(4096).decode("utf-8")
            if not message:
                break
            broadcast(message, client_socket)
        except:
            break

    if client_socket in clients:
        clients.remove(client_socket)
    client_socket.close()
    print(f"[DISCONNECTED] {addr} disconnected.")

def broadcast(message, sender_socket):
    for client in clients:
        if client != sender_socket:
            try:
                client.send(message.encode("utf-8"))
            except:
                client.close()
                if client in clients:
                    clients.remove(client)

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", 5000))
    server.listen()
    print("[STARTED] Server is listening on 127.0.0.1:5000")

    while True:
        client_socket, addr = server.accept()
        clients.append(client_socket)
        thread = threading.Thread(target=handle_client, args=(client_socket, addr))
        thread.daemon = True
        thread.start()

# ================= CLIENT GUI =================
class ChatClient:
    def __init__(self, master):
        self.master = master
        self.master.title("Python Chat App")
        self.master.geometry("550x650")

        if not os.path.exists("downloads"):
            os.makedirs("downloads")

        # Chat area
        self.chat_frame = tk.Frame(master)
        self.chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.canvas = tk.Canvas(self.chat_frame)
        self.scrollbar = tk.Scrollbar(self.chat_frame, command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Bottom frame
        bottom_frame = tk.Frame(master)
        bottom_frame.pack(fill=tk.X, pady=5)

        self.emojis = ["😀", "😂", "😍", "👍", "🙏", "🔥", "❤️", "🎉"]
        self.emoji_var = tk.StringVar()
        self.emoji_menu = ttk.Combobox(bottom_frame, textvariable=self.emoji_var,
                                       values=self.emojis, width=5, state="readonly")
        self.emoji_menu.set("😀")
        self.emoji_menu.pack(side=tk.LEFT, padx=5)

        self.entry = tk.Entry(bottom_frame, width=30, font=("Arial", 11))
        self.entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.entry.bind("<Return>", self.send_message)

        self.send_button = tk.Button(bottom_frame, text="Send",
                                     command=self.send_message, bg="#4CAF50", fg="white")
        self.send_button.pack(side=tk.LEFT, padx=5)

        self.file_button = tk.Button(bottom_frame, text="📎 File",
                                     command=self.send_file, bg="#2196F3", fg="white")
        self.file_button.pack(side=tk.RIGHT, padx=5)

        # Networking
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect(("127.0.0.1", 5000))

        self.username = simpledialog.askstring("Username", "Enter your name:", parent=self.master)
        self.images = []

        receive_thread = threading.Thread(target=self.receive_messages)
        receive_thread.daemon = True
        receive_thread.start()

    def receive_messages(self):
        while True:
            try:
                message = self.client.recv(4096).decode("utf-8")
                if not message:
                    break

                if message.startswith("[FILE]"):
                    header, filename, filedata = message.split("||", 2)
                    file_bytes = base64.b64decode(filedata.encode("utf-8"))
                    filepath = os.path.join("downloads", filename)

                    with open(filepath, "wb") as f:
                        f.write(file_bytes)

                    if filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
                        self.display_image(filepath, f"📷 {filename}")
                    else:
                        self.display_message(f"📁 File received: {filename} (saved in downloads/)")
                else:
                    self.display_message(message)

            except:
                self.display_message("❌ Disconnected from server.")
                self.client.close()
                break

    def send_message(self, event=None):
        message = self.entry.get()
        emoji = self.emoji_var.get()
        if message.strip():
            timestamp = datetime.now().strftime("%H:%M")
            full_message = f"[{timestamp}] {self.username}: {message} {emoji}"
            self.client.send(full_message.encode("utf-8"))
            self.entry.delete(0, tk.END)

    def send_file(self):
        filepath = filedialog.askopenfilename()
        if not filepath:
            return
        try:
            with open(filepath, "rb") as f:
                filedata = f.read()

            filename = os.path.basename(filepath)
            encoded_data = base64.b64encode(filedata).decode("utf-8")

            file_message = f"[FILE]||{filename}||{encoded_data}"
            self.client.send(file_message.encode("utf-8"))

            if filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
                self.display_image(filepath, f"📤 You sent: {filename}")
            else:
                self.display_message(f"📤 You sent a file: {filename}")

        except Exception as e:
            messagebox.showerror("Error", f"Could not send file: {e}")

    def display_message(self, message):
        label = tk.Label(self.scrollable_frame, text=message,
                         font=("Arial", 11), anchor="w", justify="left", wraplength=400)
        label.pack(fill="x", padx=5, pady=2)
        self.canvas.yview_moveto(1.0)

    def display_image(self, filepath, caption=""):
        try:
            img = Image.open(filepath)
            img.thumbnail((200, 200))
            photo = ImageTk.PhotoImage(img)
            self.images.append(photo)

            if caption:
                cap_label = tk.Label(self.scrollable_frame, text=caption,
                                     font=("Arial", 10, "italic"), fg="gray")
                cap_label.pack(fill="x", padx=5, pady=2)

            img_label = tk.Label(self.scrollable_frame, image=photo)
            img_label.pack(padx=5, pady=2)
            self.canvas.yview_moveto(1.0)

        except Exception as e:
            self.display_message(f"⚠️ Could not display image: {e}")

# ================= MAIN =================
if __name__ == "__main__":
    # Start server in background thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # Start GUI client
    root = tk.Tk()
    app = ChatClient(root)
    root.mainloop()
