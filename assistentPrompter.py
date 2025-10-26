import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from openai import OpenAI
import threading

class OpenAIAssistantManager:
    def __init__(self, master):
        self.master = master
        self.master.title("OpenAI Assistant Manager - The XSS Rat Edition")
        self.master.geometry("900x600")

        # Initialize API client
        self.api_key = tk.StringVar()
        self.client = None

        self.setup_ui()

    def setup_ui(self):
        # API Key Entry
        frame_api = tk.Frame(self.master)
        frame_api.pack(pady=10)

        tk.Label(frame_api, text="OpenAI API Key:").pack(side=tk.LEFT, padx=5)
        tk.Entry(frame_api, textvariable=self.api_key, width=50, show="*").pack(side=tk.LEFT, padx=5)
        tk.Button(frame_api, text="Connect", command=self.connect_api).pack(side=tk.LEFT)

        # Assistant list frame
        frame_list = tk.Frame(self.master)
        frame_list.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        columns = ("id", "name", "description", "model")
        self.tree = ttk.Treeview(frame_list, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col.title())
            self.tree.column(col, width=200 if col != "description" else 300)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # CRUD buttons
        frame_buttons = tk.Frame(self.master)
        frame_buttons.pack(pady=10)

        tk.Button(frame_buttons, text="Refresh", command=self.list_assistants).grid(row=0, column=0, padx=5)
        tk.Button(frame_buttons, text="Create", command=self.create_assistant).grid(row=0, column=1, padx=5)
        tk.Button(frame_buttons, text="Read", command=self.read_assistant).grid(row=0, column=2, padx=5)
        tk.Button(frame_buttons, text="Update", command=self.update_assistant).grid(row=0, column=3, padx=5)
        tk.Button(frame_buttons, text="Delete", command=self.delete_assistant).grid(row=0, column=4, padx=5)

        # Manual ID field (for IDOR testing)
        frame_idor = tk.LabelFrame(self.master, text="IDOR Testing / Manual ID Access")
        frame_idor.pack(fill=tk.X, padx=20, pady=10)
        self.manual_id = tk.StringVar()
        tk.Entry(frame_idor, textvariable=self.manual_id, width=60).pack(side=tk.LEFT, padx=10)
        tk.Button(frame_idor, text="Fetch by ID", command=self.fetch_by_id).pack(side=tk.LEFT)

        # Response box
        self.output = tk.Text(self.master, height=10)
        self.output.pack(fill=tk.BOTH, padx=20, pady=10)

    def connect_api(self):
        key = self.api_key.get().strip()
        if not key:
            messagebox.showerror("Error", "Please enter your OpenAI API key.")
            return
        try:
            self.client = OpenAI(api_key=key)
            messagebox.showinfo("Success", "Connected to OpenAI API!")
            self.list_assistants()
        except Exception as e:
            messagebox.showerror("Connection Error", str(e))

    def list_assistants(self):
        if not self.client:
            messagebox.showerror("Error", "Connect to API first.")
            return

        def task():
            self.tree.delete(*self.tree.get_children())
            try:
                assistants = self.client.beta.assistants.list()
                for a in assistants.data:
                    self.tree.insert("", tk.END, values=(a.id, a.name, a.description, a.model))
            except Exception as e:
                messagebox.showerror("Error", str(e))

        threading.Thread(target=task).start()

    def create_assistant(self):
        if not self.client:
            messagebox.showerror("Error", "Connect to API first.")
            return

        name = simpledialog.askstring("Name", "Enter assistant name:")
        model = simpledialog.askstring("Model", "Enter model (e.g. gpt-4o-mini):", initialvalue="gpt-4o-mini")
        description = simpledialog.askstring("Description", "Enter description:")

        if not name or not model:
            messagebox.showerror("Error", "Name and model required.")
            return

        try:
            a = self.client.beta.assistants.create(name=name, model=model, description=description)
            messagebox.showinfo("Success", f"Assistant created: {a.id}")
            self.list_assistants()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def read_assistant(self):
        selected = self.get_selected_assistant()
        if not selected:
            messagebox.showwarning("Select", "Select an assistant to view.")
            return
        self.fetch_by_id(selected[0])

    def update_assistant(self):
        selected = self.get_selected_assistant()
        if not selected:
            messagebox.showwarning("Select", "Select an assistant to update.")
            return

        new_name = simpledialog.askstring("Update", "Enter new name:")
        new_description = simpledialog.askstring("Update", "Enter new description:")

        try:
            updated = self.client.beta.assistants.update(
                selected[0],
                name=new_name or selected[1],
                description=new_description or selected[2]
            )
            messagebox.showinfo("Updated", f"Assistant {updated.id} updated.")
            self.list_assistants()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def delete_assistant(self):
        selected = self.get_selected_assistant()
        if not selected:
            messagebox.showwarning("Select", "Select an assistant to delete.")
            return

        if not messagebox.askyesno("Confirm", f"Delete assistant {selected[0]}?"):
            return

        try:
            self.client.beta.assistants.delete(selected[0])
            messagebox.showinfo("Deleted", f"Assistant {selected[0]} deleted.")
            self.list_assistants()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def fetch_by_id(self, manual=False):
        assistant_id = self.manual_id.get().strip() if not manual else manual
        if not assistant_id:
            messagebox.showerror("Error", "Enter an assistant ID.")
            return

        try:
            a = self.client.beta.assistants.retrieve(assistant_id)
            self.output.delete("1.0", tk.END)
            self.output.insert(tk.END, f"ID: {a.id}\nName: {a.name}\nModel: {a.model}\nDescription: {a.description}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def get_selected_assistant(self):
        selected = self.tree.selection()
        if not selected:
            return None
        return self.tree.item(selected[0], "values")


if __name__ == "__main__":
    root = tk.Tk()
    app = OpenAIAssistantManager(root)
    root.mainloop()

