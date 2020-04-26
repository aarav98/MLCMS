import tkinter as tk
import system as model


class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack()
        self.create_widgets()

    def create_widgets(self):
        w = tk.Canvas(self.master, width=1000, height=1000)
        w.pack()

root = tk.Tk()
app = Application(master=root)
app.mainloop()