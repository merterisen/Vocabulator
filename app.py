import tkinter as tk
from ui.main_window import Vocabulator

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = Vocabulator(root)
        root.mainloop()
    except Exception as e:
        print(f"Critical Error: {e}")
        input("Press Enter to close...")