import customtkinter as ctk
import os

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme(
    os.path.join(os.path.dirname(__file__), "mesa_sismica_theme.json")
)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Mesa Sísmica")
        self.geometry("1800x1080")


if __name__ == "__main__":
    app = App()
    app.mainloop()
