import tkinter as tk
from ui.ui import VocabulatorUI
from controller import VocabulatorController

if __name__ == "__main__":
    try:
        root = tk.Tk()
        view = VocabulatorUI(root)
        controller = VocabulatorController(view)
        view.set_controller(controller)
        root.mainloop()
        
    except Exception as e:
        print(f"Critical Error: {e}")
        input("Press Enter to close...")