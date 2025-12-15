import tkinter as tk
from tkinter import filedialog, ttk

class FileSelector(tk.LabelFrame):
    """
    A reusable component for selecting a file.
    """
    
    def __init__(self, parent, title, allowed_file_types, width=50):
        super().__init__(parent, text=title, padx=10, pady=10)
        
        self.file_path = tk.StringVar()
        self.allowed_file_types = allowed_file_types
        
        # UI Elements
        self.entry = tk.Entry(self, textvariable=self.file_path, width=width)
        self.entry.pack(side="left", padx=5, fill="x", expand=True)
        
        self.button = tk.Button(self, text="Browse", command=self._browse)
        self.button.pack(side="left")

    def _browse(self):
        filename = filedialog.askopenfilename(filetypes=self.allowed_file_types)
        if filename:
            self.file_path.set(filename)

    def get_path(self):
        return self.file_path.get()


class ResultTable(tk.LabelFrame):
    """
    A reusable component for displaying tabular data.
    """
    def __init__(self, parent, title):
        super().__init__(parent, text=title, padx=10, pady=10)
        
        # Scrollbar
        self.scrollbar = ttk.Scrollbar(self, orient="vertical")
        self.scrollbar.pack(side="right", fill="y")
        
        # Treeview
        self.tree = ttk.Treeview(self, columns=("Word", "Count"), show="headings", yscrollcommand=self.scrollbar.set)
        self.tree.heading("Word", text="Word (Lemma)")
        self.tree.heading("Count", text="Frequency")
        self.tree.column("Count", anchor="center", width=100)
        self.tree.column("Word", anchor="w")
        
        self.tree.pack(side="left", fill="both", expand=True)
        self.scrollbar.config(command=self.tree.yview)

    def update_data(self, dataframe, limit=50):
        # Clear existing
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        if dataframe is None or dataframe.empty:
            return

        # Insert new data
        for _, row in dataframe.head(limit).iterrows():
            self.tree.insert("", "end", values=(row['word'], row['count']))