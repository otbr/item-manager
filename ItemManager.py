import customtkinter as ctk
import os
import sys
import tkinter as tk
from PIL import Image, ImageTk

if getattr(sys, 'frozen', False):
    base_path = os.path.dirname(sys.executable)
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

data_path = os.path.join(base_path, "data")
if data_path not in sys.path:
    sys.path.append(data_path)

from ImageUpscale import ImageUpscaleTab
from datspr import DatSprTab
from otbreload import OtbReloadTab

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.withdraw() 
        self.title("Item Manager")
        self.geometry("900x1000")
        
        # Define ícone
        icon_path = os.path.join(base_path, "ItemManagerIco.ico")
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)

        self.show_splash()

    def show_splash(self):
        splash_path = os.path.join(base_path, "ItemManagersplash.png")
        
        self.splash_window = ctk.CTkToplevel(self)
        self.splash_window.overrideredirect(True) 
        self.splash_window.attributes("-topmost", True)
        
        try:
            pil_img = Image.open(splash_path)
            width, height = pil_img.size
            self.splash_image = ImageTk.PhotoImage(pil_img) 
        except Exception as e:
            print(f"Erro ao carregar splash: {e}")
            self.end_splash()
            return

        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w // 2) - (width // 2)
        y = (screen_h // 2) - (height // 2)
        self.splash_window.geometry(f"{width}x{height}+{x}+{y}")

        label = tk.Label(self.splash_window, image=self.splash_image, border=0)
        label.pack()
        
        self.after(3000, self.end_splash)

    def end_splash(self):
        if hasattr(self, 'splash_window') and self.splash_window.winfo_exists():
            self.splash_window.destroy()
        
        self.build_main_interface()
        self.deiconify()
        self.state('zoomed')

    def build_main_interface(self):

        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_manager = self.tab_view.add("Sprite Editor")
        self.tab_sprdat = self.tab_view.add("Spr/Dat Editor")
        self.tab_otbreload = self.tab_view.add("Otb Reload")

        self.upscale_module = ImageUpscaleTab(self.tab_manager, base_path)
        self.upscale_module.pack(fill="both", expand=True)

        self.datspr_module = DatSprTab(self.tab_sprdat)
        self.datspr_module.pack(fill="both", expand=True)

        self.otb_module = OtbReloadTab(self.tab_otbreload)
        self.otb_module.pack(fill="both", expand=True)

if __name__ == "__main__":
    app = App()
    app.mainloop()
