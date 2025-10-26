import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from openai import OpenAI
import threading
import os

class OpenAIGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("OpenAI Control Center - The XSS Rat Edition")
        self.root.geometry("1000x700")

        self.api_key = tk.StringVar()
        self.client = None

        self.build_ui()

    # ============================== UI ==============================
    def build_ui(self):
        top_frame = tk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(top_frame, text="OpenAI API Key:").pack(side=tk.LEFT)
        tk.Entry(top_frame, textvariable=self.api_key, width=60, show="*").pack(side=tk.LEFT, padx=5)
        tk.Button(top_frame, text="Connect", command=self.connect).pack(side=tk.LEFT)

        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(fill=tk.BOTH, expand=True)

        self.tab_assistants = self.make_assistant_tab()
        self.tab_files = self.make_file_tab()
        self.tab_threads = self.make_thread_tab()
        self.tab_messages = self.make_message_tab()
        self.tab_runs = self.make_run_tab()
        self.tab_models = self.make_model_tab()

        self.tabs.add(self.tab_assistants, text="Assistants")
        self.tabs.add(self.tab_files, text="Files")
        self.tabs.add(self.tab_threads, text="Threads")
        self.tabs.add(self.tab_messages, text="Messages")
        self.tabs.add(self.tab_runs, text="Runs")
        self.tabs.add(self.tab_models, text="Models")

    def connect(self):
        key = self.api_key.get().strip()
        if not key:
            messagebox.showerror("Error", "Please enter an API key.")
            return
        try:
            self.client = OpenAI(api_key=key)
            messagebox.showinfo("Connected", "Successfully connected to OpenAI API!")
        except Exception as e:
            messagebox.showerror("Connection Error", str(e))

    # ============================== ASSISTANTS ==============================
    def make_assistant_tab(self):
        frame = tk.Frame(self.tabs)
        self.assistant_tree = ttk.Treeview(frame, columns=("id", "name", "description", "model"), show="headings")
        for col in ("id", "name", "description", "model"):
            self.assistant_tree.heading(col, text=col.title())
            self.assistant_tree.column(col, width=200)
        self.assistant_tree.pack(fill=tk.BOTH, expand=True, pady=10)

        btn_frame = tk.Frame(frame)
        btn_frame.pack(pady=5)
        for (text, cmd) in [
            ("List", self.list_assistants),
            ("Create", self.create_assistant),
            ("Update", self.update_assistant),
            ("Delete", self.delete_assistant)
        ]:
            tk.Button(btn_frame, text=text, command=cmd).pack(side=tk.LEFT, padx=5)

        id_frame = tk.Frame(frame)
        id_frame.pack(pady=10)
        tk.Label(id_frame, text="Manual ID (IDOR test):").pack(side=tk.LEFT)
        self.assistant_id_entry = tk.Entry(id_frame, width=50)
        self.assistant_id_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(id_frame, text="Fetch", command=self.fetch_assistant_by_id).pack(side=tk.LEFT)

        self.assistant_output = tk.Text(frame, height=10)
        self.assistant_output.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        return frame

    def list_assistants(self):
        self.assistant_tree.delete(*self.assistant_tree.get_children())
        if not self.client:
            return messagebox.showerror("Error", "Connect first.")
        try:
            data = self.client.beta.assistants.list()
            for a in data.data:
                self.assistant_tree.insert("", tk.END, values=(a.id, a.name, a.description, a.model))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def create_assistant(self):
        name = simpledialog.askstring("Name", "Assistant name:")
        model = simpledialog.askstring("Model", "Model (e.g. gpt-4o-mini):", initialvalue="gpt-4o-mini")
        desc = simpledialog.askstring("Description", "Description:")
        try:
            a = self.client.beta.assistants.create(name=name, model=model, description=desc)
            messagebox.showinfo("Created", f"Assistant {a.id}")
            self.list_assistants()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def update_assistant(self):
        selected = self.assistant_tree.selection()
        if not selected: return
        item = self.assistant_tree.item(selected[0])["values"]
        new_name = simpledialog.askstring("Update", "New name:", initialvalue=item[1])
        new_desc = simpledialog.askstring("Update", "New description:", initialvalue=item[2])
        try:
            self.client.beta.assistants.update(item[0], name=new_name, description=new_desc)
            messagebox.showinfo("Updated", f"Assistant {item[0]} updated.")
            self.list_assistants()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def delete_assistant(self):
        selected = self.assistant_tree.selection()
        if not selected: return
        item = self.assistant_tree.item(selected[0])["values"]
        if not messagebox.askyesno("Confirm", f"Delete assistant {item[1]}?"):
            return
        try:
            self.client.beta.assistants.delete(item[0])
            self.list_assistants()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def fetch_assistant_by_id(self):
        id_ = self.assistant_id_entry.get().strip()
        if not id_:
            return messagebox.showerror("Error", "Enter an ID")
        try:
            a = self.client.beta.assistants.retrieve(id_)
            self.assistant_output.delete("1.0", tk.END)
            self.assistant_output.insert(tk.END, f"{a}\n")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ============================== FILES ==============================
    def make_file_tab(self):
        frame = tk.Frame(self.tabs)
        self.file_tree = ttk.Treeview(frame, columns=("id", "filename", "purpose", "bytes"), show="headings")
        for c in ("id", "filename", "purpose", "bytes"):
            self.file_tree.heading(c, text=c.title())
            self.file_tree.column(c, width=200)
        self.file_tree.pack(fill=tk.BOTH, expand=True, pady=10)

        btn_frame = tk.Frame(frame)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="List Files", command=self.list_files).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Upload File", command=self.upload_file).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Delete File", command=self.delete_file).pack(side=tk.LEFT, padx=5)
        return frame

    def list_files(self):
        self.file_tree.delete(*self.file_tree.get_children())
        if not self.client: return
        try:
            files = self.client.files.list()
            for f in files.data:
                self.file_tree.insert("", tk.END, values=(f.id, f.filename, f.purpose, f.bytes))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def upload_file(self):
        path = filedialog.askopenfilename()
        if not path: return
        try:
            with open(path, "rb") as f:
                uploaded = self.client.files.create(file=f, purpose="assistants")
            messagebox.showinfo("Uploaded", f"File ID: {uploaded.id}")
            self.list_files()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def delete_file(self):
        selected = self.file_tree.selection()
        if not selected: return
        item = self.file_tree.item(selected[0])["values"]
        try:
            self.client.files.delete(item[0])
            self.list_files()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ============================== THREADS ==============================
    def make_thread_tab(self):
        frame = tk.Frame(self.tabs)
        self.thread_box = tk.Text(frame)
        self.thread_box.pack(fill=tk.BOTH, expand=True, pady=10)
        btn_frame = tk.Frame(frame)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="Create Thread", command=self.create_thread).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="List Threads (Recent)", command=self.list_threads_placeholder).pack(side=tk.LEFT, padx=5)
        return frame

    def create_thread(self):
        try:
            th = self.client.beta.threads.create()
            messagebox.showinfo("Created", f"Thread ID: {th.id}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def list_threads_placeholder(self):
        self.thread_box.delete("1.0", tk.END)
        self.thread_box.insert(tk.END, "OpenAI API currently does not expose full thread listing.\n")

    # ============================== MESSAGES ==============================
    def make_message_tab(self):
        frame = tk.Frame(self.tabs)
        tk.Label(frame, text="Thread ID:").pack()
        self.msg_thread_id = tk.Entry(frame, width=70)
        self.msg_thread_id.pack(pady=5)
        self.msg_box = tk.Text(frame, height=10)
        self.msg_box.pack(fill=tk.BOTH, expand=True, pady=10)
        btn_frame = tk.Frame(frame)
        btn_frame.pack()
        tk.Button(btn_frame, text="Send Message", command=self.send_message).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="List Messages", command=self.list_messages).pack(side=tk.LEFT, padx=5)
        return frame

    def send_message(self):
        thread_id = self.msg_thread_id.get().strip()
        content = self.msg_box.get("1.0", tk.END).strip()
        if not thread_id or not content:
            return messagebox.showerror("Error", "Thread ID and message required.")
        try:
            self.client.beta.threads.messages.create(thread_id=thread_id, role="user", content=content)
            messagebox.showinfo("Sent", "Message sent.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def list_messages(self):
        thread_id = self.msg_thread_id.get().strip()
        if not thread_id: return messagebox.showerror("Error", "Thread ID required.")
        try:
            msgs = self.client.beta.threads.messages.list(thread_id=thread_id)
            text = "\n".join([f"{m.role}: {m.content[0].text.value}" for m in msgs.data])
            self.msg_box.delete("1.0", tk.END)
            self.msg_box.insert(tk.END, text)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ============================== RUNS ==============================
    def make_run_tab(self):
        frame = tk.Frame(self.tabs)
        tk.Label(frame, text="Thread ID:").pack()
        self.run_thread_id = tk.Entry(frame, width=70)
        self.run_thread_id.pack(pady=5)
        tk.Label(frame, text="Assistant ID:").pack()
        self.run_assistant_id = tk.Entry(frame, width=70)
        self.run_assistant_id.pack(pady=5)
        tk.Button(frame, text="Create Run", command=self.create_run).pack(pady=5)
        self.run_output = tk.Text(frame, height=10)
        self.run_output.pack(fill=tk.BOTH, expand=True, pady=10)
        return frame

    def create_run(self):
        th = self.run_thread_id.get().strip()
        aid = self.run_assistant_id.get().strip()
        if not th or not aid: return messagebox.showerror("Error", "Both IDs required.")
        try:
            r = self.client.beta.threads.runs.create(thread_id=th, assistant_id=aid)
            self.run_output.insert(tk.END, f"Run created: {r.id}\n")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ============================== MODELS ==============================
    def make_model_tab(self):
        frame = tk.Frame(self.tabs)
        self.model_box = tk.Text(frame)
        self.model_box.pack(fill=tk.BOTH, expand=True, pady=10)
        tk.Button(frame, text="List Models", command=self.list_models).pack()
        return frame

    def list_models(self):
        try:
            models = self.client.models.list()
            out = "\n".join([m.id for m in models.data])
            self.model_box.delete("1.0", tk.END)
            self.model_box.insert(tk.END, out)
        except Exception as e:
            messagebox.showerror("Error", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    app = OpenAIGUI(root)
    root.mainloop()

