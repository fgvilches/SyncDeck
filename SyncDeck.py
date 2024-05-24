import os
import platform
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from tkinter import ttk  # Importing ttk module for Combobox
import json
import shutil
import subprocess

class SyncDeck:
    def __init__(self, root):
        self.root = root
        self.root.title("SyncDeck Manager")
        
        self.games = []
        self.load_games()

        self.os_type = platform.system()
        self.os_label = tk.Label(root, text=f"Detected OS: {self.os_type}")
        self.os_label.pack()

        self.cloud_remote = None  # Initialize cloud_remote attribute
        self.cloud_type = None  # Initialize cloud_type attribute

        # Check if a remote is already configured
        self.has_remote = self.check_for_remote()

        if not self.has_remote:
            # Button to initiate Cloud login
            self.cloud_login_button = tk.Button(root, text="Login to Cloud", command=self.login_to_cloud)
            self.cloud_login_button.pack(pady=5)

        self.add_game_frame = tk.Frame(root)
        self.add_game_frame.pack(pady=10)

        self.name_label = tk.Label(self.add_game_frame, text="Game Name:")
        self.name_label.grid(row=0, column=0)
        self.name_entry = tk.Entry(self.add_game_frame, width=50)
        self.name_entry.grid(row=0, column=1)

        if self.os_type == "Windows":
            self.setup_windows_ui()
        elif self.os_type == "Linux":
            self.setup_linux_ui()
        else:
            messagebox.showerror("Unsupported OS", "This application only supports Windows and Linux.")

        self.add_button = tk.Button(root, text="Add Game", command=self.add_game)
        self.add_button.pack(pady=5)

        self.games_list = tk.Listbox(root, width=80)
        self.games_list.pack(pady=10)
        self.games_list.bind('<Double-1>', self.load_game_for_editing)

        self.sync_button = tk.Button(root, text="Sync Game", command=self.sync_game)
        self.sync_button.pack(pady=5)

        self.save_button = tk.Button(root, text="Save Configuration", command=self.save_games)
        self.save_button.pack(pady=5)

        self.load_games_into_listbox()


    def check_for_remote(self):
        try:
            # Running rclone command to list remotes
            result = subprocess.run(["rclone", "listremotes"], capture_output=True, text=True)
            print(f"rclone listremotes output: {result.stdout}")  # Keep this line for debugging
            if ": " in result.stdout:
                print("Remote found")  # Keep this line for debugging
                return True
            else:
                print("No remote found")  # Keep this line for debugging
                return False
        except Exception as e:
            print(f"Error checking for remote: {e}")  # Keep this line for debugging
            return False

    def browse_cloud_folder(self):
        if self.has_remote and self.cloud_remote:
            initial_dir = self.cloud_remote + ":"
            selected_folder = filedialog.askdirectory(initialdir=initial_dir, title="Select Cloud Folder")
            if selected_folder:
                self.dest_entry.delete(0, tk.END)
                self.dest_entry.insert(0, selected_folder)
        else:
            messagebox.showerror("Remote Not Configured", "No remote configured. Please login to Cloud first.")

    def setup_windows_ui(self):
        self.source_label = tk.Label(self.add_game_frame, text="Cloud Folder:")
        self.source_label.grid(row=1, column=0)
        self.source_entry = tk.Entry(self.add_game_frame, width=50)
        self.source_entry.grid(row=1, column=1)
        if self.os_type == "Windows":
            self.browse_cloud_button = tk.Button(self.add_game_frame, text="Browse", command=self.browse_cloud_folder)
            self.browse_cloud_button.grid(row=1, column=2)
        elif self.os_type == "Linux":
            self.browse_cloud_button = tk.Button(self.add_game_frame, text="Browse", command=self.browse_cloud_folder)
            self.browse_cloud_button.grid(row=2, column=2)

        self.dest_label = tk.Label(self.add_game_frame, text="Destination Folder:")
        self.dest_label.grid(row=2, column=0)
        self.dest_entry = tk.Entry(self.add_game_frame, width=50)
        self.dest_entry.grid(row=2, column=1)
        self.dest_button = tk.Button(self.add_game_frame, text="Browse", command=self.browse_dest)
        self.dest_button.grid(row=2, column=2)

    def setup_linux_ui(self):
        self.source_label = tk.Label(self.add_game_frame, text="Source Folder:")
        self.source_label.grid(row=1, column=0)
        self.source_entry = tk.Entry(self.add_game_frame, width=50)
        self.source_entry.grid(row=1, column=1)
        self.source_button = tk.Button(self.add_game_frame, text="Browse", command=self.browse_source)
        self.source_button.grid(row=1, column=2)

        self.dest_label = tk.Label(self.add_game_frame, text="Cloud Folder:")
        self.dest_label.grid(row=2, column=0)
        self.dest_entry = tk.Entry(self.add_game_frame, width=50)
        self.dest_entry.grid(row=2, column=1)
        self.browse_cloud_button = tk.Button(self.add_game_frame, text="Browse", command=self.browse_cloud)
        self.browse_cloud_button.grid(row=2, column=2)

    def browse_source(self):
        folder = filedialog.askdirectory()
        if folder:
            self.source_entry.delete(0, tk.END)
            self.source_entry.insert(0, folder)

    def browse_dest(self):
        folder = filedialog.askdirectory()
        if folder:
            self.dest_entry.delete(0, tk.END)
            self.dest_entry.insert(0, folder)

    def browse_cloud(self):
        if self.cloud_remote is None:
            messagebox.showerror("Remote Not Configured", "No remote configured. Please login to Cloud first.")
        else:
            try:
                # Running rclone command to browse the remote
                subprocess.run(["rclone", "browse", self.cloud_remote], check=True)
            except Exception as e:
                messagebox.showerror("Browse Error", f"Error browsing cloud: {e}")
    def add_game(self):
        name = self.name_entry.get()
        source = self.source_entry.get()
        dest = self.dest_entry.get()
        if name and source and dest:
            self.games.append({"name": name, "source": source, "destination": dest})
            self.games_list.insert(tk.END, f"Name: {name} | Source: {source} -> Destination: {dest}")
            self.clear_entries()
        else:
            messagebox.showwarning("Input Error", "Game name, source, and destination folders must be specified.")

    def clear_entries(self):
        self.name_entry.delete(0, tk.END)
        self.source_entry.delete(0, tk.END)
        self.dest_entry.delete(0, tk.END)

    def load_game_for_editing(self, event):
        selection = self.games_list.curselection()
        if selection:
            index = selection[0]
            game = self.games[index]
            self.name_entry.delete(0, tk.END)
            self.name_entry.insert(0, game["name"])
            self.source_entry.delete(0, tk.END)
            self.source_entry.insert(0, game["source"])
            self.dest_entry.delete(0, tk.END)
            self.dest_entry.insert(0, game["destination"])
            self.add_button.config(text="Update Game", command=lambda: self.update_game(index))

    def update_game(self, index):
        name = self.name_entry.get()
        source = self.source_entry.get()
        dest = self.dest_entry.get()
        if name and source and dest:
            self.games[index] = {"name": name, "source": source, "destination": dest}
            self.load_games_into_listbox()
            self.clear_entries()
            self.add_button.config(text="Add Game", command=self.add_game)
        else:
            messagebox.showwarning("Input Error", "Game name, source, and destination folders must be specified.")

    def sync_game(self):
        selection = self.games_list.curselection()
        if not selection:
            messagebox.showwarning("Selection Error", "Please select a game to sync.")
            return

        index = selection[0]
        game = self.games[index]

        sync_direction_window = tk.Toplevel(self.root)
        sync_direction_window.title("Select Sync Direction")
        sync_direction_label = tk.Label(sync_direction_window, text="Select sync direction:")
        sync_direction_label.pack()

        sync_direction_var = tk.StringVar()
        sync_direction_combobox = ttk.Combobox(sync_direction_window, textvariable=sync_direction_var, values=["Steamdeck to PC", "PC to Steamdeck"])
        sync_direction_combobox.pack()

        def sync():
            direction = sync_direction_var.get().lower()
            if direction == "steamdeck to pc":
                source = game["source"]
                destination = game["destination"]
            elif direction == "pc to steamdeck":
                source = game["destination"]
                destination = game["source"]
            else:
                messagebox.showwarning("Input Error", "Invalid sync direction. Please select 'Steamdeck to PC' or 'PC to Steamdeck'.")
                return

            try:
                # Constructing the rclone command
                rclone_command = ["rclone", "sync", source, destination, "--filter-from", "X:/Documents/filter-list.txt"]
                # Executing the command
                subprocess.run(rclone_command, check=True)
                messagebox.showinfo("Sync Successful", f"Successfully synced {game['name']} from {source} to {destination}.")
            except subprocess.CalledProcessError as e:
                messagebox.showerror("Sync Error", f"Error syncing {game['name']}: {e.stderr.decode()}")

            sync_direction_window.destroy()

        sync_button = tk.Button(sync_direction_window, text="Sync", command=sync)
        sync_button.pack()

    def login_to_cloud(self):
        try:
            # Running rclone config command to initiate Cloud configuration
            subprocess.run(["rclone", "config"], check=True)
            # Fetching the remote name for later use
            self.cloud_remote = simpledialog.askstring("Remote Name", "Enter your remote name:")
            print("Remote name:", self.cloud_remote)  # Debugging print
            if self.cloud_remote is None:
                messagebox.showwarning("Remote Name", "No remote name entered. Please try again.")
                return
            self.cloud_type = simpledialog.askstring("Remote Type", "Enter your remote type:")
            if self.cloud_type is None:
                messagebox.showwarning("Remote Type", "No remote type entered. Please try again.")
                return
            messagebox.showinfo("Login Successful", "Successfully logged in to Cloud.")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Login Error", f"Error logging in to Cloud: {e.stderr.decode()}")




    def sync_folders(self, source, destination):
        if not os.path.exists(destination):
            os.makedirs(destination)

        for item in os.listdir(source):
            s = os.path.join(source, item)
            d = os.path.join(destination, item)
            if os.path.isdir(s):
                if os.path.exists(d):
                    shutil.rmtree(d)
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)

    def save_games(self):
        with open('sync_config.json', 'w') as f:
            json.dump(self.games, f, indent=4)
        messagebox.showinfo("Save Successful", "Game sync configuration saved successfully.")

    def load_games(self):
        if os.path.exists('sync_config.json'):
            with open('sync_config.json', 'r') as f:
                self.games = json.load(f)

    def load_games_into_listbox(self):
        self.games_list.delete(0, tk.END)
        for game in self.games:
            self.games_list.insert(tk.END, f"Name: {game['name']} | Source: {game['source']} -> Destination: {game['destination']}")

if __name__ == "__main__":
    root = tk.Tk()
    app = SyncDeck(root)
    root.mainloop()
