# -*- coding: utf-8 -*-
import os
import tkinter as tk
from polygon.gui_main import MainGUI

if __name__ == '__main__':
    this_dir = os.path.dirname(os.path.realpath(__file__))  # путь к этой дирркетории
    os.chdir(this_dir)  # сделать путь к этому каталогу текущим путем
    app = MainGUI(tk.Tk())  # инициализация программы
    app.mainloop()  # запустить приложение

