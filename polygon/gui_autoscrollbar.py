# -*- coding: utf-8 -*-
import tkinter as tk

from tkinter import ttk

class AutoScrollbar(ttk.Scrollbar):
    """ Полоса прокрутки, которая прячется, если она не нужна. Работает только для менеджера геометрии сетки """
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            self.grid_remove()
        else:
            self.grid()
            ttk.Scrollbar.set(self, lo, hi)

    def pack(self, **kw):
        raise tk.TclError('Нельзя использовать пакет с этим виджетом ' + self.__class__.__name__)

    def place(self, **kw):
        raise tk.TclError('Нельзя использовать пакет с этим виджетом ' + self.__class__.__name__)
