# -*- coding: utf-8 -*-
import tkinter as tk

class Menu:
    """ Виджет меню для главного окна GUI """
    def __init__(self, master, config, shortcuts, functions):
        """ Инициализировать меню """
        self.__config = config  # получить ссылку на файл конфигурации
        self.__shortcuts = shortcuts  # получить ссылку на сочетания клавиш
        self.__functs = functions  # получить ссылку на словарь функций
        self.menubar = tk.Menu(master)  # создать строку главного меню, общедоступную для основного графического интерфейса
        self.empty_menu = tk.Menu(master)  # пустое меню, чтобы скрыть настоящую строку меню в полноэкранном режиме
        # Включить / отключить эти метки меню
        self.__label_recent = 'Открыть предыдущее'
        self.__label_close = 'Закрыть файл'
        self.__label_tools = 'Инструменты'
        self.__labal_cut_polygons = 'Вырезать полигоны'
        self.__label_open = 'Открыть полигоны'
        self.__label_save = 'Сохранить полигоны'
        self.__label_clear = 'Очистить лист с полигонами'
        self.__label_open_table = 'Открыть лист с полигонами'
        self.__label_train = 'Обучить модель'
        # Создать меню для изображения
        self.__file = tk.Menu(self.menubar, tearoff=False, postcommand=self.__list_recent)
        self.__file.add_command(label='Открыть файл',
                              command=self.__shortcuts[0][2],
                              accelerator=self.__shortcuts[0][0])
        self.__recent_images = tk.Menu(self.__file, tearoff=False)
        self.__file.add_cascade(label=self.__label_recent, menu=self.__recent_images)
        self.__file.add_command(label=self.__label_close,
                              command=self.__shortcuts[1][2],
                              accelerator=self.__shortcuts[1][0],
                              state='disabled')
        self.__file.add_separator()
        self.__file.add_command(label='Выход',
                              command=self.__functs['destroy'],
                              accelerator=u'Alt+F4')
        self.menubar.add_cascade(label='Файл', menu=self.__file)
        # Создать меню для инструментов: вырезать прямоугольные изображения с прокручивающимся окном и т.д.
        self.__tools = tk.Menu(self.menubar, tearoff=False, postcommand=self.__check_polygons)
        self.__tools.add_command(label=self.__labal_cut_polygons,
                                 command=self.__shortcuts[2][2],
                                 accelerator=self.__shortcuts[2][0],
                                 state='disabled')
        self.__tools.add_separator()
        self.__tools.add_command(label=self.__label_open,
                                 command=self.__shortcuts[4][2],
                                 accelerator=self.__shortcuts[4][0])
        self.__tools.add_command(label=self.__label_save,
                                 command=self.__shortcuts[5][2],
                                 accelerator=self.__shortcuts[5][0])
        self.__tools.add_command(label=self.__label_clear,
                                 command=self.__shortcuts[3][2],
                                 accelerator=self.__shortcuts[3][0])
        self.menubar.add_cascade(label=self.__label_tools, menu=self.__tools)
        # Создать меню для просмотра: полноэкранный режим, размер по умолчанию и т. д.
        self.__view = tk.Menu(self.menubar, tearoff=False)
        self.__view.add_command(label='Полноэкранный режим',
                                command=self.__functs["toggle_fullscreen"],
                                accelerator='F11')
        self.__view.add_command(label='Сбросить размер окна',
                                command=self.__functs["default_geometry"],
                                accelerator='F5')
        self.__view.add_command(label=self.__label_open_table,
                                command=self.__shortcuts[6][2],
                                accelerator=self.__shortcuts[6][0])
        self.menubar.add_cascade(label='Просмотр', menu=self.__view)
        # Создать меню для сегментации
        self.__segmentation = tk.Menu(self.menubar, tearoff=False)
        self.__segmentation.add_command(label=self.__label_train,
                                command=self.__shortcuts[7][2],
                                accelerator=self.__shortcuts[7][0])
        self.menubar.add_cascade(label='Сегментация', menu=self.__segmentation)

    def __list_recent(self):
        """ List of the recent images """
        self.__recent_images.delete(0, 'end')  # пустой предыдущий список
        lst = self.__config.get_recent_list()  # получить список недавно открытых изображений
        for path in lst:  # получить список последних путей к изображениям
            self.__recent_images.add_command(label=path,
                                             command=lambda x=path: self.__functs["set_image"](x))
        # Отключить недавнее меню списка, если оно пусто.
        if self.__recent_images.index('end') is None:
            self.__file.entryconfigure(self.__label_recent, state='disabled')
        else:
            self.__file.entryconfigure(self.__label_recent, state='normal')

    def __check_polygons(self):
        """ Проверить, есть ли на изображении полигоны и включить/отключить меню «Вырезать полигоны, Сохранить
        полигоны» """
        if self.__functs["check_polygons"]():  # на изображении есть полигоны
            self.__tools.entryconfigure(self.__labal_cut_polygons, state='normal')  # включить меню
        else:  # если нет полигонов
            self.__tools.entryconfigure(self.__labal_cut_polygons, state='disabled')  # отключить меню
        if self.__functs["check_roi"]():  # на изображении есть полигоны
            self.__tools.entryconfigure(self.__label_save, state='normal')  # включить меню
        else:  # если нет полигонов
            self.__tools.entryconfigure(self.__label_save, state='disabled')  # отключить меню


    def set_state(self, state, roi=False, rect=None):
        """ Включить/отключить некоторые меню """
        self.menubar.entryconfigure(self.__label_tools, state=state)
        self.__file.entryconfigure(self.__label_close, state=state)

