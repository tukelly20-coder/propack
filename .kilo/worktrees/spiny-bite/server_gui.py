import tkinter as tk
import threading
import sys
import os
import subprocess

class ServerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Server Control")
        self.root.geometry("300x150")

        self.server_process = None
        self.is_running = False

        # Label
        self.label = tk.Label(root, text="Server Status: Stopped", font=("Arial", 12))
        self.label.pack(pady=10)

        # Start Button
        self.start_button = tk.Button(root, text="Start Server", command=self.start_server, bg="green", fg="white")
        self.start_button.pack(pady=5)

        # Stop Button
        self.stop_button = tk.Button(root, text="Stop Server", command=self.stop_server, bg="red", fg="white", state=tk.DISABLED)
        self.stop_button.pack(pady=5)

        # Exit Button
        self.exit_button = tk.Button(root, text="Exit", command=self.exit_app)
        self.exit_button.pack(pady=5)

    def start_server(self):
        if not self.is_running:
            try:
                # Chạy server.py trong subprocess
                self.server_process = subprocess.Popen([sys.executable, 'server.py'])
                self.is_running = True
                self.label.config(text="Server Status: Running")
                self.start_button.config(state=tk.DISABLED)
                self.stop_button.config(state=tk.NORMAL)
            except Exception as e:
                self.label.config(text=f"Error starting server: {e}")

    def stop_server(self):
        if self.is_running and self.server_process:
            try:
                self.server_process.terminate()
                self.server_process.wait()
                self.is_running = False
                self.label.config(text="Server Status: Stopped")
                self.start_button.config(state=tk.NORMAL)
                self.stop_button.config(state=tk.DISABLED)
            except Exception as e:
                self.label.config(text=f"Error stopping server: {e}")

    def exit_app(self):
        self.stop_server()
        self.root.quit()

if __name__ == "__main__":
    root = tk.Tk()
    gui = ServerGUI(root)
    root.mainloop()