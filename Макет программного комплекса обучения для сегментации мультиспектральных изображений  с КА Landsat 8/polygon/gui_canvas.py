# -*- coding: utf-8 -*-
# Canvas widget to zoom image.
import os
import math
import hashlib
import warnings
import tkinter as tk

from tkinter import ttk
from PIL import Image, ImageTk
from .gui_autoscrollbar import AutoScrollbar

MAX_IMAGE_PIXELS = 1500000000  # максимальное количество пикселей на изображении, используйте его осторожно

class CanvasImage:
    """ Показать и увеличить изображение """
    def __init__(self, placeholder, path):
        """ Инициализировать ImageFrame """
        self.imscale = 1.0  # масштаб для масштабирования изображения холста, общедоступный для внешних классов
        self.__delta = 1.3  # величина масштабирования
        self.__filter = Image.ANTIALIAS  # может быть: NEAREST, BILINEAR, BICUBIC and ANTIALIAS
        self.__previous_state = 0  # предыдущее состояние клавиатуры
        self.path = path  # путь к изображению должен быть общедоступным для внешних классов
        # Создаем ImageFrame в виджете-заполнителе
        self.__imframe = ttk.Frame(placeholder)  # заполнитель объекта ImageFrame
        # Вертикальные и горизонтальные полосы прокрутки для холста
        hbar = AutoScrollbar(self.__imframe, orient='horizontal')
        vbar = AutoScrollbar(self.__imframe, orient='vertical')
        hbar.grid(row=1, column=0, sticky='we')
        vbar.grid(row=0, column=1, sticky='ns')
        # Создайте холст и привяжите его полосами прокрутки. Public для внешних классов
        self.canvas = tk.Canvas(self.__imframe, highlightthickness=0,
                                xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        self.canvas.grid(row=0, column=0, sticky='nswe')
        self.canvas.update()  # дождитесь создания холста
        hbar.configure(command=self.__scroll_x)  # привязать полосы прокрутки к холсту
        vbar.configure(command=self.__scroll_y)
        # Bind events to the Canvas
        self.canvas.bind('<Configure>', lambda event: self.__show_image())  # размер холста изменен
        self.canvas.bind('<ButtonPress-3>', self.__move_from)  # запомнить положение холста
        self.canvas.bind('<B3-Motion>',     self.__move_to)  # переместить холст в новое положение
        self.canvas.bind('<MouseWheel>', self.__wheel)  # zoom для Windows и MacOS, но не для Linux
        self.canvas.bind('<Button-5>',   self.__wheel)  # масштабирование для Linux, прокрутка колеса вниз
        self.canvas.bind('<Button-4>',   self.__wheel)  # масштабирование для Linux, прокрутка колеса вверх
        # Обрабатывать нажатия клавиш в режиме ожидания, т.к. программа тормозит на слабых компьютерах,
        # когда слишком много событий нажатия клавиш одновременно
        self.canvas.bind('<Key>', lambda event: self.canvas.after_idle(self.__keystroke, event))

        # Решите, большое это изображение или нет
        self.__huge = False  # огромный или нет
        self.__huge_size = 14000  # определить размер огромного изображения
        self.__band_width = 1024  # ширина полосы плитки
        Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS  # подавить DecompressionBombError для большого изображения
        with warnings.catch_warnings():  # подавить DecompressionBombWarning для большого изображения
            warnings.simplefilter('ignore')
            self.__image = Image.open(self.path)  # открыть изображение, но не загружать его в оперативную память
        self.imwidth, self.imheight = self.__image.size  # public для внешних классов
        if self.imwidth * self.imheight > self.__huge_size * self.__huge_size and \
                        self.__image.tile[0][0] == 'raw':  # только необработанные изображения могут быть мозаичными
            self.__huge = True  # изображение огромное
            self.__offset = self.__image.tile[0][2]  # начальное смещение плитки
            self.__tile = [self.__image.tile[0][0],  # он должен быть "сырым"
                           [0, 0, self.imwidth, 0],  # экстент плитки (прямоугольник)
                           self.__offset,
                           self.__image.tile[0][3]]  # список аргументов декодера
        self.__min_side = min(self.imwidth, self.imheight)  # получить меньшую сторону изображения
        # Создаем пирамиду изображений
        self.__pyramid = [self.smaller()] if self.__huge else [Image.open(self.path)]
        # Установите коэффициент отношения для пирамиды изображения
        self.__ratio = max(self.imwidth, self.imheight) / self.__huge_size if self.__huge else 1.0
        self.__curr_img = 0  # текущее изображение с пирамиды
        self.__scale = self.imscale * self.__ratio  # масштаб пирамиды изображения
        self.__reduction = 2  # степень уменьшения пирамиды изображения
        (w, h), m, j = self.__pyramid[-1].size, 512, 0
        n = math.ceil(math.log(min(w, h) / m, self.__reduction)) + 1  # длина пирамиды изображения
        while w > m and h > m:  # изображение верхней пирамиды имеет размер около 512 пикселей
            j += 1
            print('\rCreating image pyramid: {j} from {n}'.format(j=j, n=n), end='')
            w /= self.__reduction  # разделить на степень редукции
            h /= self.__reduction  # разделить на степень редукции
            self.__pyramid.append(self.__pyramid[-1].resize((int(w), int(h)), self.__filter))
        print('\r' + (40 * ' ') + '\r', end='')  # скрыть напечатанную строку
        # Поместите изображение в прямоугольник контейнера и используйте его для установки правильных координат изображения.
        self.container = self.canvas.create_rectangle((0, 0, self.imwidth, self.imheight), width=0)
        # Создайте хеш-сумму MD5 из изображения. Public для внешних классов
        self.md5 = hashlib.md5(self.__pyramid[0].tobytes()).hexdigest()
        self.__show_image()  # показать изображение на холсте
        self.canvas.focus_set()  # установить фокус на холсте

    def smaller(self):
        """ Пропорционально изменить размер изображения и вернуть меньшее изображение """
        w1, h1 = float(self.imwidth), float(self.imheight)
        w2, h2 = float(self.__huge_size), float(self.__huge_size)
        aspect_ratio1 = w1 / h1
        aspect_ratio2 = w2 / h2  # он равен 1,0
        if aspect_ratio1 == aspect_ratio2:
            image = Image.new('RGB', (int(w2), int(h2)))
            k = h2 / h1  # степень сжатия
            w = int(w2)  # длина полосы
        elif aspect_ratio1 > aspect_ratio2:
            image = Image.new('RGB', (int(w2), int(w2 / aspect_ratio1)))
            k = h2 / w1  # степень сжатия
            w = int(w2)  # длина полосы
        else:  # aspect_ratio1 < aspect_ration2
            image = Image.new('RGB', (int(h2 * aspect_ratio1), int(h2)))
            k = h2 / h1  # тепень сжатия
            w = int(h2 * aspect_ratio1)  # длина полосы
        i, j, n = 0, 0, math.ceil(self.imheight / self.__band_width)
        while i < self.imheight:
            j += 1
            print('\rOpening image: {j} from {n}'.format(j=j, n=n), end='')
            band = min(self.__band_width, self.imheight - i)  # ширина полосы плитки
            self.__tile[1][3] = band  # установить ширину полосы
            self.__tile[2] = self.__offset + self.imwidth * i * 3  # смещение тайла (3 байта на пиксель)
            self.__image.close()
            self.__image = Image.open(self.path)  # заново открыть/сбросить изображение
            self.__image.size = (self.imwidth, band)  # задать размер полосы тайла
            self.__image.tile = [self.__tile]  # установить плитку
            cropped = self.__image.crop((0, 0, self.imwidth, band))  # лента для обрезки плитки
            image.paste(cropped.resize((w, int(band * k)+1), self.__filter), (0, int(i * k)))
            i += band
        print('\r' + (40 * ' ') + '\r', end='')  # скрыть напечатанную строку
        return image

    @staticmethod
    def check_image(path):
        """ Проверьте, является ли это изображением. Статический метод """
        # noinspection PyBroadException
        try:  # попробуйте открыть и закрыть изображение с помощью PIL
            Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS  # подавить DecompressionBombError для большого изображения
            with warnings.catch_warnings():  # подавить DecompressionBombWarning для большого изображения
                warnings.simplefilter(u'ignore')
                img = Image.open(path)
            img.close()
        except:
            return False  # не изображение
        return True  # изображение

    def redraw_figures(self):
        """ Фиктивная функция для перерисовки фигур в дочерних классах """
        pass

    def grid(self, **kw):
        """ Поместите виджет CanvasImage на родительский виджет """
        self.__imframe.grid(**kw)  # поместите виджет CanvasImage в сетку
        self.__imframe.grid(sticky='nswe')  # сделать контейнер рамы липким
        self.__imframe.rowconfigure(0, weight=1)  # сделать холст расширяемым
        self.__imframe.columnconfigure(0, weight=1)

    def pack(self, **kw):
        """ Исключение: нельзя использовать пакет с этим виджетом """
        raise Exception('Нельзя использовать пакет с этим виджетом ' + self.__class__.__name__)

    def place(self, **kw):
        """ Исключение: нельзя использовать место с этим виджетом """
        raise Exception('Нельзя использовать пакет с этим виджетом  ' + self.__class__.__name__)

    # noinspection PyUnusedLocal
    def __scroll_x(self, *args, **kwargs):
        """ Прокрутите холст по горизонтали и перерисуйте изображение """
        self.canvas.xview(*args)  # прокручивать горизонтально
        self.__show_image()  # перерисовать изображение

    # noinspection PyUnusedLocal
    def __scroll_y(self, *args, **kwargs):
        """ Прокрутите холст по вертикали и перерисуйте изображение """
        self.canvas.yview(*args)  # прокрутить вертикально
        self.__show_image()  # перерисовать изображение

    def __show_image(self):
        """ Показать изображение на холсте. Реализует правильное масштабирование изображения почти как в Google Maps. """
        box_image = self.canvas.coords(self.container)  # получить область изображения
        box_canvas = (self.canvas.canvasx(0),  # получить видимую область холста
                      self.canvas.canvasy(0),
                      self.canvas.canvasx(self.canvas.winfo_width()),
                      self.canvas.canvasy(self.canvas.winfo_height()))
        box_img_int = tuple(map(int, box_image))  # преобразовать в целое число, иначе оно не будет работать должным образом
        # Получить область прокрутки
        box_scroll = [min(box_img_int[0], box_canvas[0]), min(box_img_int[1], box_canvas[1]),
                      max(box_img_int[2], box_canvas[2]), max(box_img_int[3], box_canvas[3])]
        # Горизонтальная часть изображения находится в видимой области
        if  box_scroll[0] == box_canvas[0] and box_scroll[2] == box_canvas[2]:
            box_scroll[0]  = box_img_int[0]
            box_scroll[2]  = box_img_int[2]
        # Вертикальная часть изображения находится в видимой области
        if  box_scroll[1] == box_canvas[1] and box_scroll[3] == box_canvas[3]:
            box_scroll[1]  = box_img_int[1]
            box_scroll[3]  = box_img_int[3]
        # Преобразование области прокрутки в кортеж и в целое число
        self.canvas.configure(scrollregion=tuple(map(int, box_scroll)))  # установить область прокрутки
        x1 = max(box_canvas[0] - box_image[0], 0)  # получить координаты (x1,y1,x2,y2) фрагмента изображения
        y1 = max(box_canvas[1] - box_image[1], 0)
        x2 = min(box_canvas[2], box_image[2]) - box_image[0]
        y2 = min(box_canvas[3], box_image[3]) - box_image[1]
        if int(x2 - x1) > 0 and int(y2 - y1) > 0:  # показать изображение, если оно находится в видимой области
            if self.__huge and self.__curr_img < 0:  # показать огромное изображение, которое не помещается в оперативную память
                h = int((y2 - y1) / self.imscale)  # высота полосы плитки
                self.__tile[1][3] = h  # установить высоту полосы тайла
                self.__tile[2] = self.__offset + self.imwidth * int(y1 / self.imscale) * 3
                self.__image.close()
                self.__image = Image.open(self.path)  # заново открыть/сбросить изображение
                self.__image.size = (self.imwidth, h)  # задать размер полосы тайла
                self.__image.tile = [self.__tile]
                image = self.__image.crop((int(x1 / self.imscale), 0, int(x2 / self.imscale), h))
            else:  # показать нормальное изображение
                image = self.__pyramid[max(0, self.__curr_img)].crop(  # обрезать текущее изображение из пирамиды
                                    (int(x1 / self.__scale), int(y1 / self.__scale),
                                     int(x2 / self.__scale), int(y2 / self.__scale)))
            #
            imagetk = ImageTk.PhotoImage(image.resize((int(x2 - x1), int(y2 - y1)), self.__filter))
            imageid = self.canvas.create_image(max(box_canvas[0], box_img_int[0]),
                                               max(box_canvas[1], box_img_int[1]),
                                               anchor='nw', image=imagetk)
            self.canvas.lower(imageid)  # установить изображение в фон
            self.canvas.imagetk = imagetk  # сохранить дополнительную ссылку, чтобы предотвратить сборку мусора

    def __move_from(self, event):
        """ Запоминать предыдущие координаты для прокрутки мышкой """
        self.canvas.scan_mark(event.x, event.y)

    def __move_to(self, event):
        """ Перетащите (переместите) холст в новое положение """
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        self.__show_image()  # увеличить плитку и показать ее на холсте

    def outside(self, x, y):
        """ Проверяет, находится ли точка (x, y) за пределами области изображения """
        bbox = self.canvas.coords(self.container)  # получить область изображения
        if bbox[0] < x < bbox[2] and bbox[1] < y < bbox[3]:
            return False  # точка (x,y) находится внутри области изображения
        else:
            return True  # точка (x,y) находится за пределами области изображения

    def __wheel(self, event):
        """ Масштабировать колесиком мыши """
        x = self.canvas.canvasx(event.x)  # получить координаты события на холсте
        y = self.canvas.canvasy(event.y)
        if self.outside(x, y): return  # масштабировать только внутри области изображения
        scale = 1.0
        # Реагировать на событие колеса Linux (event.num) или Windows (event.delta)
        if event.num == 5 or event.delta == -120:  # прокрутить вниз, уменьшить, уменьшить
            if round(self.__min_side * self.imscale) < 30: return  # изображение меньше 30 пикселей
            self.imscale /= self.__delta
            scale        /= self.__delta
        if event.num == 4 or event.delta == 120:  # прокрутить вверх, увеличить, увеличить
            i = float(min(self.canvas.winfo_width(), self.canvas.winfo_height()) >> 1)
            if i < self.imscale: return  # 1 пиксель больше, чем видимая область
            self.imscale *= self.__delta
            scale        *= self.__delta
        # Возьмите соответствующее изображение из пирамиды
        k = self.imscale * self.__ratio  # временной коэффициент
        self.__curr_img = min((-1) * int(math.log(k, self.__reduction)), len(self.__pyramid) - 1)
        self.__scale = k * math.pow(self.__reduction, max(0, self.__curr_img))
        #
        self.canvas.scale('all', x, y, scale, scale)  # изменить масштаб всех объектов
        # Перерисовать некоторые фигуры перед показом изображения на экране
        self.redraw_figures()  # метод для дочерних классов
        self.__show_image()

    def __keystroke(self, event):
        """ Прокрутка с помощью клавиатуры.
            Независимо от языка клавиатуры, CapsLock, <Ctrl>+<клавиша> и т. д. """
        if event.state - self.__previous_state == 4:  # означает, что клавиша Control нажата
            pass  # ничего не делать, если нажата клавиша Control
        else:
            self.__previous_state = event.state  # запомнить последнее состояние нажатия клавиши
            # Вверх, вниз, влево, вправо нажатия клавиш
            self.keycodes = {}  # коды клавиш инициализации
            if os.name == 'nt':  # Windows OS
                self.keycodes = {
                    'd': [68, 39, 102],
                    'a': [65, 37, 100],
                    'w': [87, 38, 104],
                    's': [83, 40,  98],
                }
            else:  # Linux OS
                self.keycodes = {
                    'd': [40, 114, 85],
                    'a': [38, 113, 83],
                    'w': [25, 111, 80],
                    's': [39, 116, 88],
                }
            if event.keycode in self.keycodes['d']:  # прокрутите вправо, клавиши «d» или «вправо»
                self.__scroll_x('scroll',  1, 'unit', event=event)
            elif event.keycode in self.keycodes['a']:  # прокрутите влево, клавиши «а» или «влево»
                self.__scroll_x('scroll', -1, 'unit', event=event)
            elif event.keycode in self.keycodes['w']:  # прокрутите вверх, клавиши «w» или «вверх»
                self.__scroll_y('scroll', -1, 'unit', event=event)
            elif event.keycode in self.keycodes['s']:  # прокрутите вниз, клавиши «s» или «вниз»
                self.__scroll_y('scroll',  1, 'unit', event=event)

    def crop(self, bbox):
        """ Обрезать прямоугольник с изображения и вернуть его """
        if self.__huge:  # изображение огромное и не полностью в оперативной памяти
            band = bbox[3] - bbox[1]  # ширина полосы плитки
            self.__tile[1][3] = band  # установить высоту плитки
            self.__tile[2] = self.__offset + self.imwidth * bbox[1] * 3  # установить смещение полосы
            self.__image.close()
            self.__image = Image.open(self.path)  # заново открыть/сбросить изображение
            self.__image.size = (self.imwidth, band)  # задать размер полосы тайла
            self.__image.tile = [self.__tile]
            return self.__image.crop((bbox[0], 0, bbox[2], band))
        else:  # изображение полностью в оперативной памяти
            return self.__pyramid[0].crop(bbox)

    def destroy(self):
        """ Деструктор ImageFrame """
        self.__image.close()
        map(lambda i: i.close, self.__pyramid)  # закрыть все изображения пирамид
        del self.__pyramid[:]  # удалить список пирамид
        del self.__pyramid  # удалить переменную пирамиды
        self.canvas.destroy()
        self.__imframe.destroy()
