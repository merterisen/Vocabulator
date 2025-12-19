import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import config

class VocabulatorUI:
    """
    Responsible for:
        - Displaying widgets
        - Getting user input
        - Calling the Controller, when buttons are clicked
    """
    def __init__(self, root):
        self.root = root
        self.controller = None # Will be set by app.py
        
        self.root.title(config.WINDOW_TITLE)
        self.root.geometry(config.WINDOW_SIZE)
        
        # --- State Variables ---
        self.status = tk.StringVar(value="Ready")
        self.language = tk.StringVar(value="German")
        self.include_articles = tk.BooleanVar(value=False)
        self.pdf_file_path = tk.StringVar()
        self.known_words_file_path = tk.StringVar()
        
        self._build_ui() # Run _build_ui() at start


    def set_controller(self, controller):
        """Connection to the VocabulatorController"""
        self.controller = controller


    def _build_ui(self):
        """
        Creates all the visual elements (widgets) on the screen.
        """

        # SECTION 1: SELECT PDF
        select_pdf_frame = tk.LabelFrame(self.root, text="1. Select PDF", padx=10, pady=10)
        select_pdf_frame.pack(fill="x", padx=10, pady=5)

        self.select_pdf_entry = tk.Entry(select_pdf_frame, textvariable=self.pdf_file_path, state='readonly')
        self.select_pdf_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        select_pdf_button = tk.Button(select_pdf_frame, text="Browse", command=lambda: self.controller.browse_pdf())
        select_pdf_button.pack(side="left")


        # CONTAINER for Language and Known Words
        container_frame = tk.Frame(self.root)
        container_frame.pack(fill="x", padx=10, pady=5)

        
        # SECTION 2: LANGUAGE SELECTION
        select_language_frame = tk.LabelFrame(container_frame, text="2. Select Language", padx=10, pady=10)
        select_language_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        select_language_combobox = ttk.Combobox(select_language_frame, textvariable=self.language, values=list(config.LANGUAGES.keys()), state="readonly")
        select_language_combobox.pack(fill="x")

        include_articles_checkbutton = tk.Checkbutton(select_language_frame, text="Include Articles", variable=self.include_articles)
        include_articles_checkbutton.pack(anchor="w")


        # SECTION 3: KNOWN WORDS FILE
        known_words_frame = tk.LabelFrame(container_frame, text="3. Select Known Words (Optional)", padx=10, pady=10)
        known_words_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))

        self.known_words_entry = tk.Entry(known_words_frame, textvariable=self.known_words_file_path, state='readonly')
        self.known_words_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        # Command routes to Controller
        known_words_button = tk.Button(known_words_frame, text="Browse", command=lambda: self.controller.browse_known_words())
        known_words_button.pack(side="left")


        # SECTION 4: RUN BUTTON AND STATUS
        self.run_button = tk.Button(self.root, text="RUN ANALYSIS", command=lambda: self.controller.run_analysis(), height=2, bg="#e1e1e1") 
        self.run_button.pack(fill="x", padx=20, pady=10)

        self.progress_bar = ttk.Progressbar(self.root, mode='indeterminate')
        self.progress_bar.pack(fill="x", padx=10)
        
        status_label = tk.Label(self.root, textvariable=self.status, fg="blue")
        status_label.pack(pady=5)


        # SECTION 5: RESULTS TABLE
        results_frame = tk.LabelFrame(self.root, text="Preview (Top 50)", padx=10, pady=10)
        results_frame.pack(fill="both", expand=True, padx=10, pady=5)

        results_scrollbar = ttk.Scrollbar(results_frame, orient="vertical")
        results_scrollbar.pack(side="right", fill="y")

        self.results_table = ttk.Treeview(results_frame, columns=("Word", "Count"), show="headings", 
                                        yscrollcommand=results_scrollbar.set)
        self.results_table.heading("Word", text="Word")
        self.results_table.heading("Count", text="Frequency")
        self.results_table.column("Word", anchor="w")
        self.results_table.column("Count", anchor="center", width=100)
        self.results_table.pack(side="left", fill="both", expand=True)
        
        results_scrollbar.config(command=self.results_table.yview)


        # SECTION 6: EXPORT BUTTONS
        export_frame = tk.Frame(self.root, pady=10)
        export_frame.pack(fill="x")
        
        export_csv_button = tk.Button(export_frame, text="Export CSV", command=lambda: self.controller.export_data("csv"))
        export_csv_button.pack(side="left", padx=20, expand=True)
        
        export_excel_button = tk.Button(export_frame, text="Export Excel", command=lambda: self.controller.export_data("excel"))
        export_excel_button.pack(side="right", padx=20, expand=True)



    # =================================================================
    # Methods called by Controller
    # =================================================================

    def update_status(self, message):
        self.status.set(message)


    def set_pdf_path(self, path):
        self.pdf_file_path.set(path)


    def set_known_words_path(self, path):
        self.known_words_file_path.set(path)


    def update_table(self, dataframe):
        """Clears and repopulates the treeview"""
        
        for item in self.results_table.get_children():
            self.results_table.delete(item)
            
        if dataframe is None or dataframe.empty:
            return

        for _, row in dataframe.head(50).iterrows():
            self.results_table.insert("", "end", values=(row['word'], row['count']))


    def show_error(self, title, message):
        messagebox.showerror(title, message)


    def show_info(self, title, message):
        messagebox.showinfo(title, message)


    def show_warning(self, title, message):
        messagebox.showwarning(title, message)


    def lock_ui(self):
        self.run_button.config(state="disabled")
        self.progress_bar.start(10)


    def unlock_ui(self):
        self.progress_bar.stop()
        self.run_button.config(state="normal")