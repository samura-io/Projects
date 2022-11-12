import os
import pandas as pd
import numpy as np
from tkinter import *
from tkinter import ttk
import tkinter.messagebox as mb
import tkinter.colorchooser as color

from polygon.logic_tools import save_polygons_for_learning


class Table(Toplevel):
    count = 0

    def __init__(self, data):
        super().__init__()
        self.name = None
        self.polygons = None
        self.classname = None
        self.data = data

        self.title('Лист с полигонима')
        self.geometry('500x350')

        self.table = ttk.Treeview(self)
        self.table.pack(pady=10)
        self.table['columns'] = ('PolygonCoordinates', 'Name', 'ClassName')
        self.table.column("#0", width=0, stretch=NO)
        self.table.column("PolygonCoordinates", anchor=CENTER, width=125)
        self.table.column("Name", anchor=CENTER, width=115)
        self.table.column("ClassName", anchor=CENTER, width=115)
        self.table.heading("#0", text="", anchor=CENTER)
        self.table.heading("PolygonCoordinates", text="PolygonCoordinates", anchor=CENTER)
        self.table.heading("Name", text="Name", anchor=CENTER)
        self.table.heading("ClassName", text="ClassName", anchor=CENTER)

        for record in data:
            self.table.insert(parent='', index='end', iid=Table.count, text='',
                              values=(record[0], record[1], record[2]))
            Table.count += 1

        Delete_button = Button(self, text="Удалить", command=lambda: self.delete_record())
        frame = Frame()
        frame.grid()
        Delete_button.pack(pady=20)

    def delete_record(self):
        item = self.table.selection()[0]
        self.table.delete(item)




class ImputWindow(Tk):
    def __init__(self):
        super().__init__()
        self.attributes('-topmost', True)
        self.after_idle(self.attributes, '-topmost', False)

        self.name = None
        self.classname = None
        self.name_entry = None
        self.classname_entry = None
        self.rgb = None

        self.title('Добавить полигоны')
        self.geometry('300x300')

        Input_frame = Frame(self)
        Input_frame.pack()
        name = Label(Input_frame, text="Имя")
        name.grid(row=0, column=0)
        classname = Label(Input_frame, text="Класс")
        classname.grid(row=0, column=1)

        self.name_entry = Entry(Input_frame)
        self.name_entry.grid(row=1, column=0)
        self.classname_entry = Entry(Input_frame)
        self.classname_entry.grid(row=1, column=1)

        self.btn = Button(self, text="Выберите цвет", command=self.onChoose)
        self.btn.pack(fill=Y, pady=20)
        self.frame = Frame(self, border=1, relief=SUNKEN, width=100, height=100)
        self.frame.pack()

        add_button = Button(self, text="Добавить", command=self.add)
        add_button.pack(pady=20)

    def onChoose(self):
        (self.rgb, hx) = color.askcolor()
        self.frame.config(bg=hx)
        self.lift()

    def add(self):
        self.name = self.name_entry.get()
        self.classname = self.classname_entry.get()
        if self.name == "" or self.classname == "" or self.rgb is None:
            mb.showinfo('Ошибка', 'Пустое значение. \nЗаполните все поля.')
            self.lift()
        else:
            save_polygons_for_learning(self.name, self.classname, self.rgb)
            self.lift()
            self.destroy()





if __name__ == '__main__':
    imput_window = ImputWindow()
    imput_window.mainloop()

