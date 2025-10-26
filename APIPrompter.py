import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from openai import OpenAI
import threading
import os
import json
import base64
import subprocess
from datetime import datetime

class OpenAIGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("OpenAI Control Center - The XSS Rat Edition")
        self.root.geometry("1000x700")

        self.api_key = tk.StringVar()
        self.client = None
        self.request_history = []
        self.pending_logs = []
        self.log_text = None

        self.build_ui()

    def ensure_client(self):
        if not self.client:
            messagebox.showerror("Error", "Connect first.")
            return False
        return True

    def run_in_thread(self, func, callback=None):
        def runner():
            try:
                result = func()
                if callback:
                    self.root.after(0, lambda: callback(result))
            except Exception as e:
                def handle_error():
                    messagebox.showerror("Error", str(e))
                    self.append_log(f"Error: {e}")
                self.root.after(0, handle_error)

        threading.Thread(target=runner, daemon=True).start()

    def format_json(self, payload):
        try:
            return json.dumps(payload, indent=2, ensure_ascii=False)
        except Exception:
            return str(payload)

    def append_log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] {message}\n"
        if self.log_text:
            self.log_text.configure(state=tk.NORMAL)
            self.log_text.insert(tk.END, entry)
            self.log_text.see(tk.END)
            self.log_text.configure(state=tk.DISABLED)
        else:
            self.pending_logs.append(entry)

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
        self.tab_model_capabilities = self.make_model_capabilities_tab()
        self.tab_evals = self.make_evals_tab()
        self.tab_finetune = self.make_finetune_tab()
        self.tab_responses = self.make_responses_tab()
        self.tab_videogen = self.make_videogen_tab()
        self.tab_raw_curl = self.make_raw_curl_tab()
        self.tab_logging = self.make_logging_tab()

        self.tabs.add(self.tab_assistants, text="Assistants")
        self.tabs.add(self.tab_files, text="Files")
        self.tabs.add(self.tab_threads, text="Threads")
        self.tabs.add(self.tab_messages, text="Messages")
        self.tabs.add(self.tab_runs, text="Runs")
        self.tabs.add(self.tab_models, text="Models")
        self.tabs.add(self.tab_model_capabilities, text="Model Capabilities")
        self.tabs.add(self.tab_evals, text="Evals")
        self.tabs.add(self.tab_finetune, text="Finetuning & Workflows")
        self.tabs.add(self.tab_responses, text="Responses API")
        self.tabs.add(self.tab_videogen, text="VideoGen")
        self.tabs.add(self.tab_raw_curl, text="Raw CURL")
        self.tabs.add(self.tab_logging, text="Logging & Errors")

    # ============================== RAW CURL ==============================
    def make_raw_curl_tab(self):
        frame = tk.Frame(self.tabs)

        command_frame = tk.Frame(frame)
        command_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        tk.Label(command_frame, text="CURL Command:").pack(anchor=tk.W)
        self.curl_command_text = tk.Text(command_frame, height=12, wrap=tk.WORD)
        self.curl_command_text.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        btn_frame = tk.Frame(command_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        tk.Button(btn_frame, text="Send Request", command=self.run_curl_command).pack(side=tk.LEFT)
        tk.Button(btn_frame, text="Clear", command=lambda: self.curl_command_text.delete("1.0", tk.END)).pack(side=tk.LEFT, padx=5)

        display_frame = tk.Frame(frame)
        display_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        response_frame = tk.Frame(display_frame)
        response_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tk.Label(response_frame, text="Response:").pack(anchor=tk.W)
        self.curl_response_text = tk.Text(response_frame, height=15, wrap=tk.WORD, state=tk.DISABLED)
        self.curl_response_text.pack(fill=tk.BOTH, expand=True)

        history_frame = tk.Frame(display_frame, width=220)
        history_frame.pack(side=tk.RIGHT, fill=tk.Y)
        tk.Label(history_frame, text="History:").pack(anchor=tk.W)
        self.curl_history_list = tk.Listbox(history_frame, height=15)
        self.curl_history_list.pack(fill=tk.BOTH, expand=True)
        self.curl_history_list.bind("<<ListboxSelect>>", self.load_selected_history)

        return frame

    def run_curl_command(self):
        command = self.curl_command_text.get("1.0", tk.END).strip()
        if not command:
            return messagebox.showerror("Error", "Enter a CURL command to execute.")
        key = self.api_key.get().strip()
        if not key:
            return messagebox.showerror("Error", "Please enter your API key first.")

        self.append_log(f"Sending CURL command:\n{command}")

        def task():
            env = os.environ.copy()
            env["OPENAI_API_KEY"] = key
            completed = subprocess.run(command, shell=True, capture_output=True, text=True, env=env)
            return {
                "command": command,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
                "returncode": completed.returncode,
            }

        def done(result):
            self.request_history.append(result)
            summary = result["command"].splitlines()[0]
            if len(summary) > 80:
                summary = summary[:77] + "..."
            display_text = self.format_curl_output(result)
            self.update_curl_response(display_text)
            index_label = f"{len(self.request_history)}. {summary}"
            self.curl_history_list.insert(tk.END, index_label)
            self.curl_history_list.selection_clear(0, tk.END)
            self.curl_history_list.selection_set(tk.END)
            self.curl_history_list.see(tk.END)

            log_message = (
                f"CURL command completed with return code {result['returncode']}.\n"
                f"STDOUT:\n{result['stdout']}\nSTDERR:\n{result['stderr']}"
            )
            self.append_log(log_message)

        self.run_in_thread(task, done)

    def format_curl_output(self, result):
        parts = [f"Return code: {result['returncode']}"]
        stdout = result.get("stdout", "")
        stderr = result.get("stderr", "")
        if stdout:
            parts.append(f"STDOUT:\n{stdout}")
        if stderr:
            parts.append(f"STDERR:\n{stderr}")
        return "\n\n".join(parts)

    def update_curl_response(self, text):
        self.curl_response_text.configure(state=tk.NORMAL)
        self.curl_response_text.delete("1.0", tk.END)
        self.curl_response_text.insert(tk.END, text or "No output returned.")
        self.curl_response_text.configure(state=tk.DISABLED)

    def load_selected_history(self, event):
        selection = event.widget.curselection()
        if not selection:
            return
        idx = selection[0]
        if idx >= len(self.request_history):
            return
        entry = self.request_history[idx]
        self.curl_command_text.delete("1.0", tk.END)
        self.curl_command_text.insert(tk.END, entry["command"])
        self.update_curl_response(self.format_curl_output(entry))

    # ============================== LOGGING ==============================
    def make_logging_tab(self):
        frame = tk.Frame(self.tabs)
        self.log_text = tk.Text(frame, state=tk.DISABLED, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        if self.pending_logs:
            self.log_text.configure(state=tk.NORMAL)
            for entry in self.pending_logs:
                self.log_text.insert(tk.END, entry)
            self.log_text.configure(state=tk.DISABLED)
            self.log_text.see(tk.END)
            self.pending_logs.clear()

        return frame


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
        if not self.ensure_client():
            return
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
        if not self.ensure_client():
            return
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
        if not self.ensure_client():
            return
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
        if not self.ensure_client():
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
        if not self.ensure_client():
            return
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
        if not self.ensure_client():
            return
        try:
            files = self.client.files.list()
            for f in files.data:
                self.file_tree.insert("", tk.END, values=(f.id, f.filename, f.purpose, f.bytes))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def upload_file(self):
        path = filedialog.askopenfilename()
        if not path: return
        if not self.ensure_client():
            return
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
        if not self.ensure_client():
            return
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
        if not self.ensure_client():
            return

        def task():
            return self.client.beta.threads.create()

        def done(th):
            messagebox.showinfo("Created", f"Thread ID: {th.id}")

        self.run_in_thread(task, done)

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
        if not self.ensure_client():
            return

        def task():
            self.client.beta.threads.messages.create(thread_id=thread_id, role="user", content=content)

        def done(_):
            messagebox.showinfo("Sent", "Message sent.")

        self.run_in_thread(task, done)

    def list_messages(self):
        thread_id = self.msg_thread_id.get().strip()
        if not thread_id: return messagebox.showerror("Error", "Thread ID required.")
        if not self.ensure_client():
            return

        def task():
            return self.client.beta.threads.messages.list(thread_id=thread_id)

        def done(msgs):
            lines = []
            for m in msgs.data:
                content = ""
                if getattr(m, "content", None):
                    parts = []
                    for part in m.content:
                        if hasattr(part, "text") and part.text:
                            parts.append(part.text.value)
                        elif hasattr(part, "type"):
                            parts.append(str(part))
                    content = " ".join(parts)
                lines.append(f"{m.role}: {content}")
            text = "\n".join(lines)
            self.msg_box.delete("1.0", tk.END)
            self.msg_box.insert(tk.END, text)

        self.run_in_thread(task, done)

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

        btn_frame = tk.Frame(frame)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="Run Status", command=self.fetch_run_status).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Run Steps", command=self.fetch_run_steps).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Cancel Run", command=self.cancel_run).pack(side=tk.LEFT, padx=5)

        self.run_output = tk.Text(frame, height=10)
        self.run_output.pack(fill=tk.BOTH, expand=True, pady=10)
        return frame

    def create_run(self):
        th = self.run_thread_id.get().strip()
        aid = self.run_assistant_id.get().strip()
        if not th or not aid: return messagebox.showerror("Error", "Both IDs required.")
        if not self.ensure_client():
            return

        def task():
            return self.client.beta.threads.runs.create(thread_id=th, assistant_id=aid)

        def done(r):
            self.run_output.insert(tk.END, f"Run created: {r.id}\n")

        self.run_in_thread(task, done)

    def fetch_run_status(self):
        th = self.run_thread_id.get().strip()
        run_id = simpledialog.askstring("Run Status", "Enter run ID:")
        if not th or not run_id:
            return messagebox.showerror("Error", "Thread and Run IDs required.")
        if not self.ensure_client():
            return

        def task():
            return self.client.beta.threads.runs.retrieve(thread_id=th, run_id=run_id)

        def done(run):
            self.run_output.insert(tk.END, f"Run {run.id} status: {run.status}\n")

        self.run_in_thread(task, done)

    def fetch_run_steps(self):
        th = self.run_thread_id.get().strip()
        run_id = simpledialog.askstring("Run Steps", "Enter run ID:")
        if not th or not run_id:
            return messagebox.showerror("Error", "Thread and Run IDs required.")
        if not self.ensure_client():
            return

        def task():
            return self.client.beta.threads.runs.steps.list(thread_id=th, run_id=run_id)

        def done(steps):
            formatted = []
            for s in steps.data:
                formatted.append(f"{s.id} - {s.type} - {s.status}")
            self.run_output.insert(tk.END, "\n".join(formatted) + "\n")

        self.run_in_thread(task, done)

    def cancel_run(self):
        th = self.run_thread_id.get().strip()
        run_id = simpledialog.askstring("Cancel Run", "Enter run ID to cancel:")
        if not th or not run_id:
            return messagebox.showerror("Error", "Thread and Run IDs required.")
        if not self.ensure_client():
            return

        def task():
            return self.client.beta.threads.runs.cancel(thread_id=th, run_id=run_id)

        def done(run):
            self.run_output.insert(tk.END, f"Run {run.id} canceled.\n")

        self.run_in_thread(task, done)

    # ============================== MODELS ==============================
    def make_model_tab(self):
        frame = tk.Frame(self.tabs)
        self.model_box = tk.Text(frame)
        self.model_box.pack(fill=tk.BOTH, expand=True, pady=10)
        tk.Button(frame, text="List Models", command=self.list_models).pack()
        return frame

    def list_models(self):
        if not self.ensure_client():
            return

        def task():
            return self.client.models.list()

        def done(models):
            out = "\n".join([m.id for m in models.data])
            self.model_box.delete("1.0", tk.END)
            self.model_box.insert(tk.END, out)

        self.run_in_thread(task, done)

    # ============================== MODEL CAPABILITIES ==============================
    def make_model_capabilities_tab(self):
        frame = tk.Frame(self.tabs)
        top = tk.Frame(frame)
        top.pack(fill=tk.X, pady=5)
        tk.Label(top, text="Model ID:").pack(side=tk.LEFT)
        self.capabilities_model_entry = tk.Entry(top, width=50)
        self.capabilities_model_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(top, text="Retrieve", command=self.retrieve_model_capabilities).pack(side=tk.LEFT)
        tk.Button(top, text="Refresh Models", command=self.populate_capabilities_models).pack(side=tk.LEFT, padx=5)

        self.capabilities_list = tk.Listbox(frame, height=8)
        self.capabilities_list.pack(fill=tk.X, padx=10, pady=5)
        self.capabilities_list.bind("<<ListboxSelect>>", self.on_capability_select)

        self.capabilities_output = tk.Text(frame)
        self.capabilities_output.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        return frame

    def populate_capabilities_models(self):
        if not self.ensure_client():
            return

        def task():
            return self.client.models.list()

        def done(models):
            self.capabilities_list.delete(0, tk.END)
            for m in models.data:
                self.capabilities_list.insert(tk.END, m.id)

        self.run_in_thread(task, done)

    def on_capability_select(self, event):
        selection = event.widget.curselection()
        if not selection:
            return
        model_id = event.widget.get(selection[0])
        self.capabilities_model_entry.delete(0, tk.END)
        self.capabilities_model_entry.insert(0, model_id)
        self.retrieve_model_capabilities()

    def retrieve_model_capabilities(self):
        model_id = self.capabilities_model_entry.get().strip()
        if not model_id:
            return messagebox.showerror("Error", "Enter a model ID.")
        if not self.ensure_client():
            return

        def task():
            return self.client.models.retrieve(model_id)

        def done(model):
            data = {
                "id": model.id,
                "created": getattr(model, "created", ""),
                "owned_by": getattr(model, "owned_by", ""),
                "capabilities": getattr(model, "capabilities", {}),
                "default_experience": getattr(model, "default_experience", {}),
            }
            self.capabilities_output.delete("1.0", tk.END)
            self.capabilities_output.insert(tk.END, self.format_json(data))

        self.run_in_thread(task, done)

    # ============================== EVALS ==============================
    def make_evals_tab(self):
        frame = tk.Frame(self.tabs)
        controls = tk.Frame(frame)
        controls.pack(fill=tk.X, pady=5)
        tk.Button(controls, text="List Evals", command=self.list_evals).pack(side=tk.LEFT, padx=5)
        tk.Button(controls, text="Create Eval", command=self.create_eval).pack(side=tk.LEFT, padx=5)
        tk.Button(controls, text="Retrieve Eval", command=self.retrieve_eval).pack(side=tk.LEFT, padx=5)

        id_frame = tk.Frame(frame)
        id_frame.pack(fill=tk.X, pady=5)
        tk.Label(id_frame, text="Eval ID:").pack(side=tk.LEFT)
        self.eval_id_entry = tk.Entry(id_frame, width=50)
        self.eval_id_entry.pack(side=tk.LEFT, padx=5)

        self.eval_output = tk.Text(frame)
        self.eval_output.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        return frame

    def list_evals(self):
        if not self.ensure_client():
            return

        def task():
            return self.client.beta.evals.list()

        def done(result):
            lines = []
            for ev in result.data:
                lines.append(f"{ev.id} - {ev.status}")
            self.eval_output.delete("1.0", tk.END)
            self.eval_output.insert(tk.END, "\n".join(lines))

        self.run_in_thread(task, done)

    def create_eval(self):
        if not self.ensure_client():
            return

        model = simpledialog.askstring("Eval Model", "Model to evaluate:", initialvalue="gpt-4.1-mini")
        if not model:
            return
        spec_path = filedialog.askopenfilename(title="Select evaluation spec (JSON)")
        if not spec_path:
            return
        with open(spec_path, "r", encoding="utf-8") as f:
            spec = json.load(f)

        def task():
            return self.client.beta.evals.create(model=model, evaluation_spec=spec)

        def done(eval_obj):
            self.eval_output.delete("1.0", tk.END)
            self.eval_output.insert(tk.END, self.format_json(eval_obj.to_dict() if hasattr(eval_obj, "to_dict") else eval_obj))

        self.run_in_thread(task, done)

    def retrieve_eval(self):
        eval_id = self.eval_id_entry.get().strip()
        if not eval_id:
            return messagebox.showerror("Error", "Enter an eval ID.")
        if not self.ensure_client():
            return

        def task():
            return self.client.beta.evals.retrieve(eval_id)

        def done(eval_obj):
            payload = eval_obj.to_dict() if hasattr(eval_obj, "to_dict") else eval_obj
            self.eval_output.delete("1.0", tk.END)
            self.eval_output.insert(tk.END, self.format_json(payload))

        self.run_in_thread(task, done)

    # ============================== FINETUNING & WORKFLOWS ==============================
    def make_finetune_tab(self):
        frame = tk.Frame(self.tabs)

        ft_frame = tk.LabelFrame(frame, text="Fine-tuning Jobs")
        ft_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        controls = tk.Frame(ft_frame)
        controls.pack(fill=tk.X, pady=5)
        tk.Button(controls, text="List Jobs", command=self.list_fine_tunes).pack(side=tk.LEFT, padx=5)
        tk.Button(controls, text="Create Job", command=self.create_fine_tune).pack(side=tk.LEFT, padx=5)
        tk.Button(controls, text="Retrieve Job", command=self.retrieve_fine_tune).pack(side=tk.LEFT, padx=5)
        tk.Button(controls, text="Cancel Job", command=self.cancel_fine_tune).pack(side=tk.LEFT, padx=5)
        tk.Button(controls, text="Job Events", command=self.list_fine_tune_events).pack(side=tk.LEFT, padx=5)

        id_frame = tk.Frame(ft_frame)
        id_frame.pack(fill=tk.X, pady=5)
        tk.Label(id_frame, text="Job ID:").pack(side=tk.LEFT)
        self.fine_tune_id_entry = tk.Entry(id_frame, width=40)
        self.fine_tune_id_entry.pack(side=tk.LEFT, padx=5)

        self.fine_tune_tree = ttk.Treeview(ft_frame, columns=("id", "model", "status"), show="headings")
        for col in ("id", "model", "status"):
            self.fine_tune_tree.heading(col, text=col.title())
            self.fine_tune_tree.column(col, width=200)
        self.fine_tune_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.fine_tune_output = tk.Text(ft_frame, height=8)
        self.fine_tune_output.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        workflow_frame = tk.LabelFrame(frame, text="Workflows")
        workflow_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        wf_controls = tk.Frame(workflow_frame)
        wf_controls.pack(fill=tk.X, pady=5)
        tk.Button(wf_controls, text="List Workflows", command=self.list_workflows).pack(side=tk.LEFT, padx=5)
        tk.Button(wf_controls, text="Run Workflow", command=self.run_workflow).pack(side=tk.LEFT, padx=5)
        tk.Button(wf_controls, text="Retrieve Run", command=self.retrieve_workflow_run).pack(side=tk.LEFT, padx=5)

        wf_id_frame = tk.Frame(workflow_frame)
        wf_id_frame.pack(fill=tk.X, pady=5)
        tk.Label(wf_id_frame, text="Workflow ID:").pack(side=tk.LEFT)
        self.workflow_id_entry = tk.Entry(wf_id_frame, width=40)
        self.workflow_id_entry.pack(side=tk.LEFT, padx=5)
        tk.Label(wf_id_frame, text="Run ID:").pack(side=tk.LEFT)
        self.workflow_run_entry = tk.Entry(wf_id_frame, width=30)
        self.workflow_run_entry.pack(side=tk.LEFT, padx=5)

        self.workflow_input = tk.Text(workflow_frame, height=6)
        self.workflow_input.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.workflow_input.insert(tk.END, "{\n  \"input\": \"\"\n}")

        self.workflow_output = tk.Text(workflow_frame, height=6)
        self.workflow_output.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        return frame

    def list_fine_tunes(self):
        if not self.ensure_client():
            return

        def task():
            return self.client.fine_tuning.jobs.list()

        def done(result):
            self.fine_tune_tree.delete(*self.fine_tune_tree.get_children())
            for job in result.data:
                self.fine_tune_tree.insert("", tk.END, values=(job.id, job.model, job.status))

        self.run_in_thread(task, done)

    def create_fine_tune(self):
        if not self.ensure_client():
            return

        training_file = simpledialog.askstring("Training File", "Training file ID:")
        model = simpledialog.askstring("Base Model", "Base model:", initialvalue="gpt-4o-mini")
        if not training_file or not model:
            return

        def task():
            return self.client.fine_tuning.jobs.create(training_file=training_file, model=model)

        def done(job):
            self.fine_tune_id_entry.delete(0, tk.END)
            self.fine_tune_id_entry.insert(0, job.id)
            self.fine_tune_output.delete("1.0", tk.END)
            self.fine_tune_output.insert(tk.END, self.format_json(job.to_dict() if hasattr(job, "to_dict") else job))
            self.list_fine_tunes()

        self.run_in_thread(task, done)

    def retrieve_fine_tune(self):
        job_id = self.fine_tune_id_entry.get().strip()
        if not job_id:
            return messagebox.showerror("Error", "Enter a job ID.")
        if not self.ensure_client():
            return

        def task():
            return self.client.fine_tuning.jobs.retrieve(job_id)

        def done(job):
            self.fine_tune_output.delete("1.0", tk.END)
            self.fine_tune_output.insert(tk.END, self.format_json(job.to_dict() if hasattr(job, "to_dict") else job))

        self.run_in_thread(task, done)

    def cancel_fine_tune(self):
        job_id = self.fine_tune_id_entry.get().strip()
        if not job_id:
            return messagebox.showerror("Error", "Enter a job ID.")
        if not self.ensure_client():
            return

        def task():
            return self.client.fine_tuning.jobs.cancel(job_id)

        def done(job):
            self.fine_tune_output.insert(tk.END, f"\nCanceled job {job.id}\n")
            self.list_fine_tunes()

        self.run_in_thread(task, done)

    def list_fine_tune_events(self):
        job_id = self.fine_tune_id_entry.get().strip()
        if not job_id:
            return messagebox.showerror("Error", "Enter a job ID.")
        if not self.ensure_client():
            return

        def task():
            return self.client.fine_tuning.jobs.list_events(job_id)

        def done(events):
            lines = [f"{ev.created_at}: {ev.message}" for ev in events.data]
            self.fine_tune_output.delete("1.0", tk.END)
            self.fine_tune_output.insert(tk.END, "\n".join(lines))

        self.run_in_thread(task, done)

    def list_workflows(self):
        if not self.ensure_client():
            return

        def task():
            return self.client.beta.workflows.list()

        def done(result):
            lines = []
            for wf in result.data:
                lines.append(f"{wf.id} - {wf.name if hasattr(wf, 'name') else ''}")
            self.workflow_output.delete("1.0", tk.END)
            self.workflow_output.insert(tk.END, "\n".join(lines))

        self.run_in_thread(task, done)

    def run_workflow(self):
        workflow_id = self.workflow_id_entry.get().strip()
        if not workflow_id:
            return messagebox.showerror("Error", "Enter a workflow ID.")
        if not self.ensure_client():
            return
        raw_input = self.workflow_input.get("1.0", tk.END).strip() or "{}"
        try:
            payload = json.loads(raw_input)
        except json.JSONDecodeError as exc:
            return messagebox.showerror("Error", f"Invalid JSON: {exc}")

        def task():
            return self.client.beta.workflows.runs.create(workflow_id=workflow_id, input=payload)

        def done(run):
            self.workflow_run_entry.delete(0, tk.END)
            self.workflow_run_entry.insert(0, run.id)
            self.workflow_output.delete("1.0", tk.END)
            self.workflow_output.insert(tk.END, self.format_json(run.to_dict() if hasattr(run, "to_dict") else run))

        self.run_in_thread(task, done)

    def retrieve_workflow_run(self):
        workflow_id = self.workflow_id_entry.get().strip()
        run_id = self.workflow_run_entry.get().strip()
        if not workflow_id or not run_id:
            return messagebox.showerror("Error", "Enter workflow and run IDs.")
        if not self.ensure_client():
            return

        def task():
            return self.client.beta.workflows.runs.retrieve(workflow_id=workflow_id, run_id=run_id)

        def done(run):
            self.workflow_output.delete("1.0", tk.END)
            self.workflow_output.insert(tk.END, self.format_json(run.to_dict() if hasattr(run, "to_dict") else run))

        self.run_in_thread(task, done)

    # ============================== RESPONSES API ==============================
    def make_responses_tab(self):
        frame = tk.Frame(self.tabs)

        top = tk.Frame(frame)
        top.pack(fill=tk.X, pady=5)
        tk.Label(top, text="Model:").pack(side=tk.LEFT)
        self.responses_model = tk.Entry(top, width=40)
        self.responses_model.insert(0, "gpt-4.1-mini")
        self.responses_model.pack(side=tk.LEFT, padx=5)
        tk.Button(top, text="Send", command=self.send_response_request).pack(side=tk.LEFT, padx=5)

        tk.Label(frame, text="System Prompt (optional):").pack(anchor=tk.W, padx=10)
        self.responses_system = tk.Text(frame, height=4)
        self.responses_system.pack(fill=tk.X, padx=10)

        tk.Label(frame, text="User Prompt:").pack(anchor=tk.W, padx=10, pady=(10, 0))
        self.responses_user = tk.Text(frame, height=8)
        self.responses_user.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        tk.Label(frame, text="Response:").pack(anchor=tk.W, padx=10)
        self.responses_output = tk.Text(frame, height=10)
        self.responses_output.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        return frame

    def send_response_request(self):
        if not self.ensure_client():
            return
        model = self.responses_model.get().strip()
        user_prompt = self.responses_user.get("1.0", tk.END).strip()
        system_prompt = self.responses_system.get("1.0", tk.END).strip()
        if not user_prompt:
            return messagebox.showerror("Error", "Enter a user prompt.")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        def task():
            return self.client.responses.create(model=model, input=messages)

        def done(response):
            text = getattr(response, "output_text", None)
            if not text and hasattr(response, "output"):
                text = self.format_json(response.output)
            self.responses_output.delete("1.0", tk.END)
            self.responses_output.insert(tk.END, text or str(response))

        self.run_in_thread(task, done)

    # ============================== VIDEOGEN ==============================
    def make_videogen_tab(self):
        frame = tk.Frame(self.tabs)

        controls = tk.Frame(frame)
        controls.pack(fill=tk.X, pady=5)
        tk.Label(controls, text="Model:").pack(side=tk.LEFT)
        self.videogen_model = tk.Entry(controls, width=30)
        self.videogen_model.insert(0, "gpt-4.1")
        self.videogen_model.pack(side=tk.LEFT, padx=5)
        tk.Label(controls, text="Aspect Ratio:").pack(side=tk.LEFT)
        self.videogen_ratio = tk.Entry(controls, width=15)
        self.videogen_ratio.insert(0, "16:9")
        self.videogen_ratio.pack(side=tk.LEFT, padx=5)
        tk.Button(controls, text="Generate Video", command=self.generate_video).pack(side=tk.LEFT, padx=5)

        tk.Label(frame, text="Prompt:").pack(anchor=tk.W, padx=10)
        self.videogen_prompt = tk.Text(frame, height=6)
        self.videogen_prompt.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.videogen_status = tk.Text(frame, height=8)
        self.videogen_status.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        return frame

    def generate_video(self):
        if not self.ensure_client():
            return
        prompt = self.videogen_prompt.get("1.0", tk.END).strip()
        if not prompt:
            return messagebox.showerror("Error", "Enter a prompt.")
        model = self.videogen_model.get().strip() or "gpt-4.1"
        ratio = self.videogen_ratio.get().strip() or "16:9"
        save_path = filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=[("MP4", "*.mp4")])
        if not save_path:
            return

        def task():
            video = self.client.videos.generate(model=model, prompt=prompt, aspect_ratio=ratio)
            if hasattr(video, "data"):
                clip = video.data[0]
                if hasattr(clip, "b64_json"):
                    data = base64.b64decode(clip.b64_json)
                else:
                    data = clip
            else:
                data = video
            with open(save_path, "wb") as fh:
                if isinstance(data, bytes):
                    fh.write(data)
                elif isinstance(data, str):
                    fh.write(base64.b64decode(data))
                else:
                    raise ValueError("Unknown video payload format")
            return save_path

        def done(path):
            self.videogen_status.delete("1.0", tk.END)
            self.videogen_status.insert(tk.END, f"Video saved to {path}\n")

        self.run_in_thread(task, done)


if __name__ == "__main__":
    root = tk.Tk()
    app = OpenAIGUI(root)
    root.mainloop()

