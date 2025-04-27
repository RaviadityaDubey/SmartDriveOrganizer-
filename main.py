import os
import shutil
import sqlite3
import uuid
from datetime import datetime
from tkinterdnd2 import DND_FILES, TkinterDnD
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from collections import defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
import joblib

# Categories
CATEGORIES = {
    "Documents": [".pdf", ".docx", ".doc", ".txt", ".xlsx"],
    "Images": [".jpg", ".jpeg", ".png", ".svg", ".gif"],
    "Videos": [".mp4", ".mkv", ".avi", ".mov"],
    "Audio": [".mp3", ".wav", ".aac"],
    "Applications": [".exe", ".msi", ".apk"],
    "Archives": [".zip", ".rar", ".7z", ".tar"],
    "Code": [".py", ".js", ".html", ".css", ".java", ".cpp"]
}

LOG_DB = "sort_log.db"
category_states = {}
MODEL_PATH = "ai_sort_model.pkl"

# DB setup
def init_db():
    conn = sqlite3.connect(LOG_DB)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS file_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT,
                        filename TEXT,
                        original_path TEXT,
                        new_path TEXT,
                        date_moved TEXT)''')
    conn.commit()
    conn.close()

# AI-Based Classifier Setup
def load_or_train_ai_model():
    if os.path.exists(MODEL_PATH):
        return joblib.load(MODEL_PATH)
    documents = ["report.pdf", "image.jpg", "video.mp4", "script.py", "presentation.ppt"]
    labels = ["Documents", "Images", "Videos", "Code", "Documents"]
    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(documents)
    clf = MultinomialNB()
    clf.fit(X, labels)
    joblib.dump((vectorizer, clf), MODEL_PATH)
    return vectorizer, clf

vectorizer, clf = load_or_train_ai_model()

# Utility functions
def get_category(extension, filename=""):
    for category, extensions in CATEGORIES.items():
        if extension.lower() in extensions and category_states.get(category, tk.BooleanVar()).get():
            return category
    try:
        X = vectorizer.transform([filename])
        return clf.predict(X)[0]
    except:
        return "Others"

def log_file_movement(session_id, filename, original_path, new_path):
    conn = sqlite3.connect(LOG_DB)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO file_logs (session_id, filename, original_path, new_path, date_moved) VALUES (?, ?, ?, ?, ?)",
                   (session_id, filename, original_path, new_path, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def organize_folder(folder_path, sort_by_date=False):
    if not folder_path:
        messagebox.showerror("Error", "Please select a folder.")
        return

    session_id = str(uuid.uuid4())
    moved_files = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            ext = os.path.splitext(file)[1]
            category = get_category(ext, file)

            if sort_by_date:
                try:
                    stat = os.stat(file_path)
                    date_folder = datetime.fromtimestamp(stat.st_mtime).strftime("%Y/%m")
                    category_folder = os.path.join(folder_path, date_folder)
                except:
                    category_folder = os.path.join(folder_path, category)
            else:
                category_folder = os.path.join(folder_path, category)

            os.makedirs(category_folder, exist_ok=True)
            new_path = os.path.join(category_folder, file)
            if file_path != new_path:
                shutil.move(file_path, new_path)
                log_file_movement(session_id, file, file_path, new_path)
                moved_files.append((file, file_path, new_path))

    if moved_files:
        messagebox.showinfo("Done", f"Moved {len(moved_files)} files. See 'View Logs' for details.")
    else:
        messagebox.showinfo("Done", "No files were moved.")

# def undo_last_sort():
#     conn = sqlite3.connect(LOG_DB)
#     cursor = conn.cursor()
#     cursor.execute("SELECT session_id FROM file_logs ORDER BY id DESC LIMIT 1")
#     result = cursor.fetchone()
#     if not result:
#         messagebox.showinfo("Info", "No sort session to undo.")
#         return
#     session_id = result[0]
#     cursor.execute("SELECT filename, original_path, new_path FROM file_logs WHERE session_id = ?", (session_id,))
#     entries = cursor.fetchall()
#     moved_folders = set()
#     for filename, original_path, new_path in reversed(entries):
#         if os.path.exists(new_path):
#             os.makedirs(os.path.dirname(original_path), exist_ok=True)
#             shutil.move(new_path, original_path)
#             moved_folders.add(os.path.dirname(new_path))
#     for folder in moved_folders:
#         if os.path.isdir(folder) and not os.listdir(folder):
#             os.rmdir(folder)
#     cursor.execute("DELETE FROM file_logs WHERE session_id = ?", (session_id,))
#     conn.commit()
#     conn.close()
#     messagebox.showinfo("Undo", "Undo of last session completed.")

def undo_last_sort():
    conn = sqlite3.connect(LOG_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT session_id FROM file_logs ORDER BY id DESC LIMIT 1")
    result = cursor.fetchone()
    if not result:
        messagebox.showinfo("Info", "No sort session to undo.")
        return

    session_id = result[0]
    cursor.execute("SELECT filename, original_path, new_path FROM file_logs WHERE session_id = ?", (session_id,))
    entries = cursor.fetchall()
    moved_folders = set()

    for filename, original_path, new_path in reversed(entries):
        if os.path.exists(new_path):
            os.makedirs(os.path.dirname(original_path), exist_ok=True)
            shutil.move(new_path, original_path)
            moved_folders.add(os.path.dirname(new_path))

    # Remove empty folders: including nested date folders (e.g., /2024/04)
    for folder in sorted(moved_folders, key=lambda x: -len(x)):  # Sort deeper paths first
        try:
            while folder != os.path.dirname(folder):  # Avoid deleting root drive
                if os.path.isdir(folder) and not os.listdir(folder):
                    os.rmdir(folder)
                    folder = os.path.dirname(folder)
                else:
                    break
        except Exception as e:
            print(f"Failed to remove {folder}: {e}")

    cursor.execute("DELETE FROM file_logs WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()
    messagebox.showinfo("Undo", "Undo of last session completed and folders cleaned up.")


def show_logs():
    log_window = tk.Toplevel()
    log_window.title("Action Logs")
    tree = ttk.Treeview(log_window, columns=("Filename", "From", "To", "Date"), show='headings')
    tree.pack(fill="both", expand=True)
    for col in tree["columns"]:
        tree.heading(col, text=col)
        tree.column(col, width=150)
    conn = sqlite3.connect(LOG_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT filename, original_path, new_path, date_moved FROM file_logs ORDER BY id DESC LIMIT 100")
    for row in cursor.fetchall():
        tree.insert("", "end", values=row)
    conn.close()

def preview_sort(folder_path):
    if not folder_path:
        messagebox.showerror("Error", "Please select a folder.")
        return
    preview_window = tk.Toplevel()
    preview_window.title("Sort Preview")
    tree = ttk.Treeview(preview_window, columns=("File", "New Location"), show='headings')
    tree.pack(fill="both", expand=True)
    tree.heading("File", text="File")
    tree.heading("New Location", text="New Location")
    for root, _, files in os.walk(folder_path):
        for file in files:
            ext = os.path.splitext(file)[1]
            category = get_category(ext, file)
            new_path = os.path.join(folder_path, category, file)
            tree.insert("", "end", values=(file, new_path))

# GUI
class SmartDriveApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SmartDrive Organizer")
        self.folder_path = tk.StringVar()
        self.sort_by_date = tk.BooleanVar(value=False)

        init_db()
        self.build_ui()

    def build_ui(self):
        frm = tk.Frame(self.root, padx=20, pady=20)
        frm.pack()

        tk.Label(frm, text="📁 Select Folder:").grid(row=0, column=0, sticky="w")
        entry = tk.Entry(frm, textvariable=self.folder_path, width=50)
        entry.grid(row=0, column=1)

        # Drag and Drop Binding
        entry.drop_target_register(DND_FILES)
        entry.dnd_bind('<<Drop>>', self.handle_drag_drop)

        tk.Button(frm, text="Browse", command=self.browse_folder).grid(row=0, column=2)

        tk.Label(frm, text="Select Categories to Sort:").grid(row=1, column=0, columnspan=3, pady=(10, 0), sticky="w")

        cat_frame = tk.Frame(frm)
        cat_frame.grid(row=2, column=0, columnspan=3, sticky="w")
        for i, category in enumerate(CATEGORIES.keys()):
            var = tk.BooleanVar(value=True)
            category_states[category] = var
            tk.Checkbutton(cat_frame, text=category, variable=var).grid(row=i//3, column=i%3, sticky="w")

        tk.Checkbutton(frm, text="📆 Sort by modification date (Year/Month)", variable=self.sort_by_date).grid(
            row=3, column=0, columnspan=3, pady=(10, 0), sticky="w")

        btn_frame = tk.Frame(frm, pady=10)
        btn_frame.grid(row=4, column=0, columnspan=3)

        tk.Button(btn_frame, text="Run Sort", width=15, command=self.run_sort).grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Preview Sort", width=15, command=self.preview_sort).grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text="Undo Last Sort", width=15, command=undo_last_sort).grid(row=0, column=2, padx=5)
        tk.Button(btn_frame, text="View Logs", width=15, command=show_logs).grid(row=0, column=3, padx=5)
        tk.Button(btn_frame, text="Exit", width=10, command=self.root.quit).grid(row=0, column=4, padx=5)

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path.set(folder)

    def handle_drag_drop(self, event):
        dropped_data = event.data.strip("{}")
        if os.path.isdir(dropped_data):
            self.folder_path.set(dropped_data)

    def run_sort(self):
        organize_folder(self.folder_path.get(), self.sort_by_date.get())

    def preview_sort(self):
        preview_sort(self.folder_path.get())

# Run the app
if __name__ == '__main__':
    root = TkinterDnD.Tk()
    app = SmartDriveApp(root)
    root.mainloop()


