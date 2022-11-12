# -*- coding: utf-8 -*-
import os
import tkinter as tk

from tkinter import ttk
from tkinter import messagebox
from tkinter.filedialog import askopenfilename

import numpy as np
import pandas as pd

from .gui_menu import Menu
from .gui_polygons import Polygons
from .logic_config import Config
from .logic_tools import train, save_polygons, open_polygons, cut_polygons, clear_save_polygons
from .opentar_module import OpenFile

from .gui_toplevels import Table, ImputWindow


class MainGUI(ttk.Frame):
    """ Главное окно графического интерфейса """
    def __init__(self, mainframe):
        """ Инициализация фрейма """
        ttk.Frame.__init__(self, master=mainframe)
        self.__create_instances()
        self.__create_main_window()
        self.__create_widgets()


    def __create_instances(self):
        """ Экземпляры для графического интерфейса создаются здесь """
        self.__config = Config()  # открыть конфигурационный файл главного окна
        self.__imframe = None  # пустой экземпляр фрейма изображения (canvas)

    def __create_main_window(self):
        """ Создать графический интерфейс главного окна """
        self.__default_title = 'Сегментатор изображения'
        self.master.title(self.__default_title)
        self.master.geometry(self.__config.get_win_geometry())  # получить размер/положение окна из конфигурации
        self.master.wm_state(self.__config.get_win_state())  # получить состояние окна
        # self.destructor срабатывает, когда окно уничтожается
        self.master.protocol('WM_DELETE_WINDOW', self.destroy)
        #
        self.__fullscreen = False  # включить/отключить полноэкранный режим
        self.__bugfix = False  # ОШИБКА! при изменении: полноэкранный --> увеличенный --> обычный
        self.__previous_state = 0  # предыдущее состояние события
        # Список сочетаний клавиш в следующем формате: [имя, код клавиши, функция]
        self.keycode = {}  # коды клавиш инициализации
        if os.name == 'nt':  # Windows OS
            self.keycode = {
                'o': 79,
                'w': 87,
                'r': 82,
                'q': 81,
                'h': 72,
                's': 83,
                'a': 65,
                'c': 67,
                'f': 70
            }
        else:  # Linux OS
            self.keycode = {
                'o': 32,
                'w': 25,
                'r': 27,
                'q': 24,
                'h': 43,
                's': 39,
                'a': 38,
                'c': 54,
                'f': 41
            }
        self.__shortcuts = [['Ctrl+O', self.keycode['o'], self.__open_image],   # 0 Открыть изображение
                            ['Ctrl+W', self.keycode['w'], self.__close_image],  # 1 Загрыть изображение
                            ['Ctrl+R', self.keycode['r'], self.__cut_polygons],         # 2 Скользящее окно
                            ['Ctrl+C', self.keycode['c'], self.__clear_poly],  # 3 очистить список полигонов
                            ['Ctrl+H', self.keycode['h'], self.__open_poly],    # 4 открытые полигоны для изображения
                            ['Ctrl+S', self.keycode['s'], self.__save_poly],    # 5 сохранить полигоны изображения
                            ['Ctrl+A', self.keycode['a'], self.__open_table],   # 6 показать прямоугольник скользящего окна
                            ['Ctrl+F', self.keycode['f'], self.__train]]        # 7 сегментация

        # Привязать события к главному окну
        self.master.bind('<Motion>', lambda event: self.__motion())  # отслеживать и обрабатывать положение указателя мыши
        self.master.bind('<F11>', lambda event: self.__toggle_fullscreen())  # переключить полноэкранный режим
        self.master.bind('<Escape>', lambda event, s=False: self.__toggle_fullscreen(s))
        self.master.bind('<F5>', lambda event: self.__default_geometry())  # сбросить геометрию окна по умолчанию
        # Обработка изменения размера главного окна в режиме ожидания, потому что последовательные нажатия клавиш <F11> - <F5>
        # не устанавливайте геометрию по умолчанию из полноэкранного режима, если изменение размера не отложено.
        self.master.bind('<Configure>', lambda event: self.master.after_idle(self.__resize_master))
        # Обрабатывать нажатия клавиш в режиме ожидания, т.к. программа тормозит на слабых компьютерах,
        # когда слишком много событий нажатия клавиш одновременно.
        self.master.bind('<Key>', lambda event: self.master.after_idle(self.__keystroke, event))

    def __toggle_fullscreen(self, state=None):
        """ Включить/отключить полноэкранный режим """
        if state is not None:
            self.__fullscreen = state  # установить состояние на полноэкранный режим
        else:
            self.__fullscreen = not self.__fullscreen  # переключение логического значения
        # Скрыть строку меню в полноэкранном режиме или показать ее в противном случае
        if self.__fullscreen:
            self.__menubar_hide()
        else:  # показать строку меню
            self.__menubar_show()
        self.master.wm_attributes('-fullscreen', self.__fullscreen)  # полноэкранный режим вкл/выкл

    def __menubar_show(self):
        """ Показать строку меню """
        self.master.configure(menu=self.__menu.menubar)

    def __menubar_hide(self):
        """ Скрыть строку меню """
        self.master.configure(menu=self.__menu.empty_menu)

    def __motion(self):
        """ Отслеживание указателя мыши и управление его положением """
        if self.__fullscreen:
            y = self.master.winfo_pointery()
            if 0 <= y < 20:  # если близко к верхней части главного окна
                self.__menubar_show()
            else:
                self.__menubar_hide()

    def __keystroke(self, event):
        """ Независимая от языка обработка событий с клавиатуры"""
        #print(event.keycode, event.keysym, event.state)  # раскомментируйте его для целей отладки
        if event.state - self.__previous_state == 4:  # проверьте, нажата ли клавиша <Control>
            for shortcut in self.__shortcuts:
                if event.keycode == shortcut[1]:
                    shortcut[2]()
        else:  # запомнить предыдущее состояние события
            self.__previous_state = event.state

    def __default_geometry(self):
        """ Сбросить геометрию по умолчанию для главного окна графического интерфейса """
        self.__toggle_fullscreen(state=False)  # выход из полноэкранного режима
        self.master.wm_state(self.__config.default_state)  # выйти из увеличенного
        self.__config.set_win_geometry(self.__config.default_geometry)  # сохранить по умолчанию в конфиг
        self.master.geometry(self.__config.default_geometry)  # установить геометрию по умолчанию

    def __resize_master(self):
        """ Сохранить размер и положение главного окна в конфигурационном файле.
            ОШИБКА! Существует ОШИБКА при переходе окна из полноэкранного режима в увеличенный, а затем в обычный режим.
            Главное окно каким-то образом запоминает увеличенный режим как обычно, поэтому я должен явно установить
            предыдущая геометрия из INI-файла конфигурации в главное окно. """
        if self.master.wm_attributes('-fullscreen'):  # не помню полноэкранную геометрию
            self.__bugfix = True  # исправление ошибки
            return
        if self.master.state() == 'normal':
            if self.__bugfix is True:  # исправление ошибки для: полноэкранный --> увеличенный --> обычный
                self.__bugfix = False
                # Явно установите предыдущую геометрию, чтобы исправить ошибку
                self.master.geometry(self.__config.get_win_geometry())
                return
            self.__config.set_win_geometry(self.master.winfo_geometry())
        self.__config.set_win_state(self.master.wm_state())

    def __create_widgets(self):
        """ Виджеты для графического интерфейса создаются здесь """
        # CСоздать виджет меню
        self.functions = {  # словарь функций для виджета меню
            "destroy": self.destroy,
            "toggle_fullscreen": self.__toggle_fullscreen,
            "default_geometry": self.__default_geometry,
            "set_image": self.__set_image,
            "check_polygons": self.__check_polygons,
            "check_roi": self.__check_roi}
        self.__menu = Menu(self.master, self.__config, self.__shortcuts, self.functions)
        self.master.configure(menu=self.__menu.menubar)  # меню должно быть ДО iconbitmap, это ошибка
        # ОШИБКА! Добавьте строку меню в главное окно ПЕРЕД командой iconbitmap. В противном случае это будет
        # уменьшать высоту на 20 пикселей после каждого открытия-закрытия главного окна.
        this_dir = os.path.dirname(os.path.realpath(__file__))  # каталог этого файла
        if os.name == 'nt':  # Windows OS
            self.master.iconbitmap(os.path.join(this_dir, 'logo.ico'))  # установить значок логотипа
        else:  # Linux OS
            # Формат ICO не работает для Linux. Вместо этого используйте формат GIF или черно-белый формат XBM
            img = tk.PhotoImage(file=os.path.join(this_dir, 'logo.gif'))
            self.master.tk.call('wm', 'iconphoto', self.master._w, img)  # установить значок логотипа
        # Создайте рамку-заполнитель для изображения
        self.master.rowconfigure(0, weight=1)  # сделать ячейку сетки расширяемой
        self.master.columnconfigure(0, weight=1)
        self.__placeholder = ttk.Frame(self.master)
        self.__placeholder.grid(row=0, column=0, sticky='nswe')
        self.__placeholder.rowconfigure(0, weight=1)  # сделать ячейку сетки расширяемой
        self.__placeholder.columnconfigure(0, weight=1)
        # Если изображение не было закрыто ранее, откройте это изображение еще раз
        path = self.__config.get_opened_path()
        if path:
            self.__set_image(path)  # открыть предыдущее изображение

    def __set_image(self, path):
        """ Закрыть предыдущее изображение и установить новое """
        self.__imframe = Polygons(placeholder=self.__placeholder, path=path,
                                  roll_size=self.__config.get_roll_size())  # создать рамку изображения
        self.__imframe.grid()  # покажи это
        self.master.title(self.__default_title + ': {}'.format(path))  # изменить заголовок окна
        self.__config.set_recent_path(path)  # сохранить путь к изображению в конфиге
        # Включить некоторые меню
        self.__menu.set_state(state='normal', roi=self.__imframe.roi, rect=self.__imframe.table)

    def __open_image(self):
        """ Открыть изображение в графическом интерфейсе """
        path = askopenfilename(title='Выберите архив Landsat',
                               initialdir=self.__config.get_recent_path())
        geotiff = OpenFile(archive=path)
        self.__close_image()   # закрыть предыдущее изображение
        image = geotiff.act_rgb()
        if image == '': return
        # Проверьте, является ли это изображением
        if not Polygons.check_image(image):
            messagebox.showinfo('Ошибка! \n Выберите другой файл Ladsat')
            self.__open_image()  # попробуйте снова открыть новое изображение
            return
        self.__set_image(image)

    def __close_image(self):
        """ Закрыть изображение """
        if self.__imframe:
            if len(self.__imframe.roi_dict):
                pass  # self.__save_poly()  # если есть полигоны, сохранить их
            self.__imframe.destroy()
            self.__imframe = None
            self.master.title(self.__default_title)  # установить заголовок окна по умолчанию
            self.__menu.set_state(state='disabled')  # отключить некоторые меню

    def __check_roi(self):
        if self.__imframe and len(self.__imframe.roi_dict):  # есть сохраненные полигоны
            return True
        return False

    def __check_polygons(self):
        """ Проверить, есть ли полигоны """
        if self.__imframe and len(self.__imframe.polygons_list):  # есть сохраненные полигоны
            return True
        return False  # если нет полигонов

    def __cut_polygons(self):
        """ Применение вырезки к изображению """
        if self.__check_polygons():  # есть полигоны
            cut_polygons()


    def __open_poly(self):
        """ Открыть полигоны ROI и отверстия для текущего изображения из файла """
        if self.__imframe:
            path = askopenfilename(title='Открыть полигоны для текущего изображения',
                                   initialdir=self.__config.config_dir)
            if path == '': return
            # отсутствие инспекции PyBroadException
            try:  # проверьте, правильный ли это файл с полигонами
                open_polygons(self.__imframe, path)
                self.__imframe.roi = True  # сбросить рисунок области интереса
            except:
                messagebox.showinfo('Неверный файл',
                                    'Неверные полигоны для изображения: "{}"\n'.format(self.__imframe.path) +
                                    'Пожалуйста, выберите полигоня для текущего изображения.')
                self.__open_poly()  # попробуй снова открыть полигоны
                return

    def __save_poly(self):
        """ Сохранение полигонов ROI и отверстий текущего изображения в файл """
        if self.__imframe:
            save_polygons(self.__imframe, self.__config)
            self.__open_inputwindow()


    def __clear_poly(self):
        if self.__imframe:
            clear_save_polygons(self.__config)
        else:
            clear_save_polygons(self.__config)

    def __open_inputwindow(self):
        """"Открыть окно с полями ввода"""
        inputwindow = ImputWindow()
        inputwindow.grab_set()
        # save_polygons_for_learning(self.__imframe, self.__config, name=name, classname=classname)


    def __clear_tempdata(self):
        """Удаляет все temp файлы после закрытия программы"""
        path = os.path.join(os.path.dirname(__file__).replace('polygon', ''), 'temp')
        path2 = os.path.join(os.path.dirname(__file__).replace('polygon', ''), 'temp\\polygons_for_learning')
        for i in os.listdir(path):
            if '.txt' in i:
                os.remove(os.path.join(path, i))
        for i in os.listdir(path2):
            os.remove(os.path.join(path2, i))


    def __open_table(self):
        """Открывает таблицу с данными полигонов, меток и имен"""
        self.path = os.path.join(os.path.dirname(__file__).replace('polygon', ''), 'temp\\polygons.xlsx')
        self.data = np.array(pd.read_excel(self.path))
        table = Table(self.data)
        table.grab_set()

    def __train(self):
        train()



    def destroy(self):
        """ Уничтожить объект основного кадра и освободить все ресурсы """
        if self.__imframe:  # изображение не закрыто
            self.__config.set_opened_path(self.__imframe.path)  # запомнить открытое изображение
        else:  # изображение закрыто
            self.__config.set_opened_path()  # нет пути
        self.__close_image()
        self.__config.destroy()
        self.__clear_tempdata()
        self.__clear_poly()
        self.quit()

