# -*- coding: utf-8 -*-
import os
import configparser

class Config:
    """ Этот класс отвечает за различные операции с конфигурационным INI файлом.
        Модуль ConfigParser является частью стандартной библиотеки Python. """
    def __init__(self, path='temp'):
        """ Инициализировать параметры конфигурации для файла INI """
        self.config_dir = path  # должен быть общедоступным для основного графического интерфейса
        self.__config_name = 'config.ini'  # имя файла конфигурации
        self.__config_path = os.path.join(self.config_dir, self.__config_name)
        #
        # Value -- первое место. Options -- второе место.
        self.__window = 'Window'  # информация о главном окне
        self.__geometry = 'Geometry'  # размер и положение главного окна "ШxВ±X±Y"
        self.default_geometry = '800x600+0+0'  # геометрия окна по умолчанию 'WxH±X±Y'
        self.__state = 'State'  # состояние окна: нормальное, увеличенное и т.д.
        self.default_state = 'normal'  # нормальное состояние окна
        self.__opened_path = 'OpenedPath'  # последний открытый путь к задаче или изображению
        self.__default_opened_path = 'None'
        #
        self.__rolling = 'RollingWindow'  # информация о скользящем окне
        self.__roll_w = 'Width'  # ширина скользящего окна
        self.__roll_h = 'Height'  # высота скользящего окна
        self.__default_roll_w, self.__default_roll_h = 320, 240  # ширина/высота скользящего окна по умолчанию
        self.__roll_dx = 'Horizontal step'  # горизонтальный шаг скользящего окна
        self.__roll_dy = 'Vertical step'  # вертикальный шаг скользящего окна
        # Шаг по горизонтали по умолчанию составляет 1/2 ширины скользящего окна.
        self.__default_roll_dx = int(self.__default_roll_w / 2)  # должно быть целым числом
        # Шаг по вертикали по умолчанию равен 1/2 высоты скользящего окна.
        self.__default_roll_dy = int(self.__default_roll_h / 2)  # должно быть целым числом
        #
        self.__recent = 'LastOpened'  # список последних открытых путей
        self.__recent_number = 10  # количество последних путей
        #
        self.__config = configparser.ConfigParser()  # создать парсер конфигурации
        self.__config.optionxform = lambda option: option  # сохранить футляр для писем
        # Создать каталог конфигурации, если он не существует
        if not os.path.isdir(self.config_dir):
            os.makedirs(self.config_dir)
        # Создайте новый файл конфигурации, если он не существует, или прочитайте существующий
        if not os.path.isfile(self.__config_path):
            self.__new_config()  # создать новую конфигурацию
        else:
            self.__config.read(self.__config_path)  # прочитать существующий файл конфигурации

    def __check_section(self, section):
        """ Проверьте, существует ли раздел, и создайте его, если нет. """
        if not self.__config.has_section(section):
            self.__config.add_section(section)

    def get_win_geometry(self):
        """ Получить размер и положение главного окна """
        try:
            return self.__config[self.__window][self.__geometry]
        except KeyError:  # если ключа нет в словаре конфига
            return self.default_geometry

    def set_win_geometry(self, geometry):
        """ Установить размер главного окна """
        self.__check_section(self.__window)
        self.__config[self.__window][self.__geometry] = geometry

    def get_win_state(self):
        """ Получить состояние главного окна: нормальное, увеличенное и т. д. """
        try:
            return self.__config[self.__window][self.__state]
        except KeyError:  # если ключа нет в словаре конфига
            return self.default_state

    def set_win_state(self, state):
        """ Установить состояние главного окна: обычное, увеличенное и т. д. """
        self.__check_section(self.__window)
        self.__config[self.__window][self.__state] = state

    def get_opened_path(self):
        """ Получить открытый путь, если он не был закрыт ранее, или вернуть пустую строку """
        try:
            path = self.__config[self.__window][self.__opened_path]
            if path == self.__default_opened_path or not os.path.exists(path):
                return ''
            else:
                return path
        except KeyError:  # если ключа нет в словаре конфига
            return ''

    def set_opened_path(self, path=None):
        """ Запомнить открытый путь к INI файлу конфигурации """
        self.__check_section(self.__window)
        if path:
            self.__config[self.__window][self.__opened_path] = path
        else:
            self.__config[self.__window][self.__opened_path] = self.__default_opened_path

    def get_roll_size(self):
        """ Получить кортеж (ширину, высоту) скользящего окна """
        try:
            w = self.__config[self.__rolling][self.__roll_w]
            h = self.__config[self.__rolling][self.__roll_h]
            return int(w), int(h)
        except KeyError:  # если ключа нет в словаре конфига
            return self.__default_roll_w, self.__default_roll_h

    def set_roll_size(self, width=None, height=None):
        """ Установить кортеж (ширину, высоту) скользящего окна """
        self.__check_section(self.__rolling)
        if width:
            self.__config[self.__rolling][self.__roll_w] = str(width)
        else:
            self.__config[self.__rolling][self.__roll_w] = str(self.__default_roll_w)
        if height:
            self.__config[self.__rolling][self.__roll_h] = str(height)
        else:
            self.__config[self.__rolling][self.__roll_h] = str(self.__default_roll_h)

    def get_step_size(self):
        """ Получить кортеж (dx, dy) шагов скользящего окна """
        try:
            dx = self.__config[self.__rolling][self.__roll_dx]
            dy = self.__config[self.__rolling][self.__roll_dy]
            return int(dx), int(dy)
        except KeyError:  # если ключа нет в словаре конфига
            return self.__default_roll_dx, self.__default_roll_dy

    def set_step_size(self, dx=None, dy=None):
        """ Установите кортеж (dx, dy) шагов скользящего окна """
        self.__check_section(self.__rolling)
        if dx:
            self.__config[self.__rolling][self.__roll_dx] = str(dx)
        else:
            self.__config[self.__rolling][self.__roll_dx] = str(self.__default_roll_dx)
        if dy:
            self.__config[self.__rolling][self.__roll_dy] = str(dy)
        else:
            self.__config[self.__rolling][self.__roll_dy] = str(self.__default_roll_dy)

    def get_recent_list(self):
        """ Получить список недавно открытых путей к изображениям """
        try:
            lst = self.__config.items(self.__recent)  # список пар (ключ, значение)
            lst = [path for key, path in lst]  # оставить только путь
            for n, path in enumerate(lst):
                if not os.path.isfile(path):
                    del lst[n]  # удалить путь к несуществующему файлу из списка
            return lst
        except configparser.NoSectionError:  # нет раздела со списком последних открытых путей
            return ''

    def get_recent_path(self):
        """ Получить последний открытый путь из файла конфигурации INI """
        try:
            path = self.__config[self.__recent]['1']
            path = os.path.abspath(os.path.join(path, os.pardir))  # получить родительский каталог
            if not os.path.exists(path):
                return os.getcwd()  # вернуть текущий каталог
            return path
        except KeyError:  # если ключа нет в словаре конфига
            return os.getcwd()  # получить текущий каталог

    def set_recent_path(self, path):
        """ Установить последний открытый путь к INI-файлу конфигурации """
        try:
            lst = self.__config.items(self.__recent)  # список пар (ключ, значение)
        except configparser.NoSectionError:  # нет раздела со списком последних открытых путей
            lst = []  # нет такого раздела
        lst = [value for key, value in lst]  # оставить только путь
        if path in lst: lst.remove(path)  # удалить путь из списка
        lst.insert(0, path)  # добавить путь в начало списка
        self.__config.remove_section(self.__recent)  # удалить раздел
        self.__config.add_section(self.__recent)  # создать пустой раздел
        key = 1
        for name in lst:
            if os.path.exists(name):
                self.__config[self.__recent][str(key)] = name
                key += 1
            if key > self.__recent_number:
                break  # выход из цикла

    def save(self):
        """ Сохранить файл конфигурации """
        with open(self.__config_path, 'w') as configfile:
            self.__config.write(configfile)

    def __new_config(self):
        """ Создайте новый INI-файл конфигурации и поместите в него значения по умолчанию. """
        self.set_win_geometry(self.default_geometry)
        self.set_win_state(self.default_state)
        self.set_roll_size()
        self.set_step_size()

    def destroy(self):
        """ Деструктор конфигурации """
        self.save()
