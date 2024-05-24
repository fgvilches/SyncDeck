import os
import platform
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from tkinter import ttk  # Importing ttk module for Combobox
import json
import shutil
import subprocess
import re

class RemoteBrowserDialog(tk.Toplevel):
    def __init__(self, parent, remote_name, dest_entry):
        super().__init__(parent)
        self.title("Browse Remote Folders")
        self.remote_name = remote_name
        self.current_path = "/"
        self.dest_entry = dest_entry  # Store the dest_entry widget
        self.path_stack = []  # Stack to keep track of visited paths

        self.folder_tree = ttk.Treeview(self)
        self.folder_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.folder_tree.bind("<<TreeviewOpen>>", self.populate_folder)
        self.folder_tree.bind("<Double-1>", self.on_double_click)  # Bind double click event

        # Button to go back one folder level
        self.back_button = tk.Button(self, text="Back", command=self.go_back)
        self.back_button.pack()

        # Button to select the highlighted folder
        self.select_button = tk.Button(self, text="Select", command=self.select_folder)
        self.select_button.pack()

        self.populate_folder()

    def populate_folder(self, event=None):
        self.folder_tree.delete(*self.folder_tree.get_children())
        folders_output = app.get_folders(self.remote_name, self.current_path)
        if folders_output is not None:
            # Split the output into lines
            folders_lines = folders_output.strip().split('\n')
            for line in folders_lines:
                # Extract the folder name using regex
                match = re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} +(-1|[0-9]+) (.+)', line)
                if match:
                    folder_name = match.group(2)
                    self.folder_tree.insert("", "end", text=folder_name, values=[f"{self.current_path}/{folder_name}"])
        else:
            messagebox.showerror("Error", "Failed to retrieve folder information.")

    def on_double_click(self, event):
        try:
            # Get the selected item
            selected_item = self.folder_tree.selection()[0]
            # Get the path of the selected item
            path = self.folder_tree.item(selected_item, "values")[0]
            # Update current_path
            self.current_path = path
            # Push current path to path stack
            self.path_stack.append(self.current_path)
            # Repopulate the folder tree with subfolders
            self.populate_folder()
        except IndexError:
            messagebox.showinfo("No Folder Selected", "Please select a folder to open.")

    def go_back(self):
        if self.path_stack:
            # Pop the last path from the stack
            self.path_stack.pop()
            if self.path_stack:
                # Set current path to the previous path in the stack
                self.current_path = self.path_stack[-1]
            else:
                # If the stack is empty, set current path to root
                self.current_path = "/"
            # Repopulate the folder tree with subfolders
            self.populate_folder()

    def select_folder(self):
        try:
            selected_item = self.folder_tree.focus()
            path = self.folder_tree.item(selected_item, "values")[0]
            # Remove any leading slash from the path
            if path.startswith("/"):
                path = path[1:]
                path = path[1:]
            # Combine remote name and path, ensuring only one slash separates them
            cloud_folder_path = f"{self.remote_name}{path}"
            self.dest_entry.delete(0, tk.END)
            self.dest_entry.insert(0, cloud_folder_path)
            self.destroy()
        except IndexError:
            messagebox.showinfo("No Folder Selected", "Please select a folder to set as the Cloud Folder.")

class SyncDeck:
    def __init__(self, root):
        self.root = root
        self.root.title("SyncDeck Manager")
        
        self.games = []
        self.load_games()
        self.load_remote_config()
        self.os_type = platform.system()
        self.os_label = tk.Label(root, text=f"Detected OS: {self.os_type}")
        self.os_label.pack()
        # Inside the __init__ method of the SyncDeck class
        #self.remote_label = tk.Label(root, text="Remote:")
        #self.remote_label.pack()

        # Initialize cloud_remote attribute
        self.cloud_remote = None

        # Check for the existence of a remote when the application starts
        self.check_for_remote()

        # Initialize the login button
        #self.cloud_login_button = tk.Button(root, text="Login to Cloud", command=self.login_to_cloud)
        #if self.cloud_remote:
            # Hide the login button if a remote exists
        #    self.cloud_login_button.pack_forget()
        #else:
        #    self.cloud_login_button.pack(pady=5)

        if self.remote_name:
            self.remote_label = tk.Label(root, text=f"Remote: {self.remote_name}")
            self.remote_label.pack()

        if not self.remote_name:
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

    def setup_windows_ui(self):
        self.source_label = tk.Label(self.add_game_frame, text="Destination Folder:")
        self.source_label.grid(row=1, column=0)
        self.source_entry = tk.Entry(self.add_game_frame, width=50)
        self.source_entry.grid(row=1, column=1)
        self.browse_cloud_button = tk.Button(self.add_game_frame, text="Browse", command=self.browse_source)
        self.browse_cloud_button.grid(row=1, column=2)

        self.dest_label = tk.Label(self.add_game_frame, text="Cloud Folder:")
        self.dest_label.grid(row=2, column=0)
        self.dest_entry = tk.Entry(self.add_game_frame, width=50)
        self.dest_entry.grid(row=2, column=1)
        self.dest_button = tk.Button(self.add_game_frame, text="Browse", command=self.browse_cloud_folder)
        self.dest_button.grid(row=2, column=2)

    def setup_linux_ui(self):
        self.source_label = tk.Label(self.add_game_frame, text="Cloud Folder:")
        self.source_label.grid(row=1, column=0)
        self.source_entry = tk.Entry(self.add_game_frame, width=50)
        self.source_entry.grid(row=1, column=1)
        self.source_button = tk.Button(self.add_game_frame, text="Browse", command=self.browse_source)
        self.source_button.grid(row=1, column=2)

        self.dest_label = tk.Label(self.add_game_frame, text="Cloud Folder:")
        self.dest_label.grid(row=2, column=0)
        self.dest_entry = tk.Entry(self.add_game_frame, width=50)
        self.dest_entry.grid(row=2, column=1)
        self.browse_cloud_button = tk.Button(self.add_game_frame, text="Browse", command=self.browse_cloud_folder)
        self.browse_cloud_button.grid(row=2, column=2)

    def load_remote_config(self):
        try:
            with open('remotes.json', 'r') as f:
                remote_config = json.load(f)
                self.remote_name = remote_config.get('remote_name', '')
        except FileNotFoundError:
            # If the file does not exist, initialize with empty values
            self.remote_name = ''
    
    def save_remote_config(self):
        remote_config = {
            'remote_name': self.remote_name
        }
        with open('remotes.json', 'w') as f:
            json.dump(remote_config, f, indent=4)

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
        sync_direction_combobox = ttk.Combobox(sync_direction_window, textvariable=sync_direction_var, values=["Cloud to PC", "PC to Cloud"])
        sync_direction_combobox.pack()

        def sync():
            direction = sync_direction_var.get().lower()
            if direction == "cloud to pc":
                destination = game["source"]
                source = game["destination"]
            elif direction == "pc to cloud":
                destination = game["destination"]
                source = game["source"]
            else:
                messagebox.showwarning("Input Error", "Invalid sync direction. Please select 'Cloud to PC' or 'PC to Cloud'.")
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
            subprocess.run(["rclone", "config"], check=True)
            if not self.remote_name:
                self.remote_name = simpledialog.askstring("Remote Name", "Enter your remote name:")
                self.save_remote_config()
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
            if isinstance(game, dict):
                name = game.get('name', '')
                source = game.get('source', '')
                destination = game.get('destination', '')
                self.games_list.insert(tk.END, f"Name: {name} | Source: {source} -> Destination: {destination}")
            else:
                # Handle the case where game is not a dictionary
                self.games_list.insert(tk.END, f"Invalid game data: {game}")

    def get_folders(self, remote, path):
        try:
            # Run the 'rclone ls' command to list the contents of the remote path
            #print("remote -> ", remote)
            #print("path -> ", path)
            result = subprocess.run(['rclone', 'lsd', f'{remote}{path}'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout
            else:
                print(f"Error listing folders: {result.stderr}")
                return None
        except Exception as e:
            print(f"Error getting folders: {e}")
            return None

    def browse_cloud_folder(self):
        if self.cloud_remote:
            browser_dialog = RemoteBrowserDialog(self.root, self.cloud_remote, self.dest_entry)
            self.root.wait_window(browser_dialog)
        else:
            messagebox.showerror("Remote Not Configured", "No remote configured. Please login to Cloud first.")

    def login_to_cloud(self):
        try:
            # Running rclone listremotes command to get the list of configured remotes
            result = subprocess.run(["rclone", "listremotes"], capture_output=True, text=True)
            if result.returncode == 0:
                remotes = result.stdout.splitlines()
                if remotes:
                    # Extract the first remote name
                    cloud_remote = remotes[0]
                    # Save the remote name to the JSON file
                    self.save_remote_name(cloud_remote)
                    # Update the cloud_remote attribute
                    self.cloud_remote = cloud_remote
                    # Update the label to display the remote name 
                    self.update_remote_label(cloud_remote)
                    messagebox.showinfo("Login Successful", f"Successfully logged in to Cloud. Remote: {cloud_remote}")
                else:
                    # If no remotes are configured, open rclone config
                    self.open_rclone_config()
            else:
                messagebox.showerror("Login Error", f"Error getting remotes: {result.stderr}")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Login Error", f"Error logging in to Cloud: {e.stderr.decode()}")

    def save_remote_name(self, remote_name):
        try:
            with open('remotes.json', 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}

        data["remote_name"] = remote_name

        with open('remotes.json', 'w') as f:
            json.dump(data, f, indent=4)

    def update_remote_label(self, remote_name):
        # Update the label to display the remote name
        self.remote_label.config(text=f"Remote: {remote_name}")

    def open_rclone_config(self):
        # Open rclone config
        subprocess.run(["rclone", "config"])

    def check_for_remote(self):
        try:
            # Running rclone listremotes command to check for existing remotes
            result = subprocess.run(["rclone", "listremotes"], capture_output=True, text=True)
            if result.returncode == 0:
                remotes = result.stdout.strip().split('\n')
                if remotes:
                    # If remotes exist, set the first remote as the cloud_remote
                    self.cloud_remote = remotes[0]
        except subprocess.CalledProcessError as e:
            print(f"Error checking for remotes: {e.stderr}")

        # Inside the SyncDeck class
    
    def update_remote_label(self, remote_name):
        self.remote_label.config(text=f"Remote: {remote_name}")

if __name__ == "__main__":
    root = tk.Tk()
    app = SyncDeck(root)
    root.mainloop()