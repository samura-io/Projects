# -*- coding: utf-8 -*-
import uuid
import tkinter as tk

from .gui_canvas import CanvasImage

class Polygons(CanvasImage):
    """ Класс полигонов. Наследовать класс CanvasImage """
    def __init__(self, placeholder, path, roll_size):
        """ Инициализировать полигоны """
        CanvasImage.__init__(self, placeholder, path)  # вызов __init__ класса CanvasImage
        self.canvas.bind('<ButtonPress-1>', self.set_edge)  # установить новый край
        self.canvas.bind('<ButtonRelease-3>', self.popup)  # вызов всплывающего меню
        self.canvas.bind('<Motion>', self.motion)  # управлять движением мыши
        self.canvas.bind('<Delete>', lambda event: self.delete_poly())  # удалить выбранный полигон
        # Создайте всплывающее меню для полигонов
        self.hold_menu1 = False  # всплывающее меню закрыто
        self.hold_menu2 = False
        self.menu = tk.Menu(self.canvas, tearoff=0)
        self.menu.add_command(label='Удалить полигон', command=self.delete_poly)
        # Параметры полигона
        self.roi = True  # это ROI или дыра
        self.table = True  # показать окно таблицы
        self.roll_size = roll_size  # размер скользящего окна
        self.width_line = 2  # ширина линий
        self.roll_rect = self.canvas.create_rectangle((0, 0, 0, 0), width=self.width_line,
                                                      state=u'hidden')
        self.dash = (1, 1)  # штриховой узор
        self.color_back_roi = 'yellow'  # нарисовать цвет Рои
        self.color_roi =  {'draw'   : 'red',      # нарисовать цвет Рои
                           'point'  : 'blue',     # цвет точки РОИ
                           'back'   : self.color_back_roi,  # цвет фона РОИ
                           'stipple': 'gray12'}   # пунктирное значение для roi
        self.tag_curr_edge_start = '1st_edge'  # начальный край текущего полигона
        self.tag_curr_edge = 'edge'  # ребра полигона
        self.tag_curr_edge_id = 'edge_id'  # часть ID текущего ребра
        self.tag_roi = 'roi'  # ROI тэг
        self.tag_const = 'poly'  # постоянный тег для полигона
        self.tag_poly_line = 'poly_line'  # край полигона
        self.tag_curr_circle = 'circle'  # Тег залипания круга для текущей полилинии
        self.radius_stick = 10  # расстояние, на котором линия прилегает к начальной точке многоугольника
        self.radius_circle = 2  # радиус липкого круга
        self.edge = None  # текущий край нового полигона
        self.polygon = []  # вершины текущего (чертежного, красного) многоугольника
        self.selected_poly = []  # выбранные полигоны
        self.roi_dict = {}
        self.polygons_list = []  # словарь всех полигонов roi и их координат на изображении холста

    def set_edge(self, event):
        """ Установить край полигона """
        if self.hold_menu2:  # всплывающее меню было открыто
            self.hold_menu2 = False
            self.motion(event)  # событие движения для всплывающего меню
            return
        self.motion(event)  # генерировать событие движения. Это необходимо для строки меню, иначе ошибка!
        x = self.canvas.canvasx(event.x)  # получить координаты события на холсте
        y = self.canvas.canvasy(event.y)
        if self.edge and ' '.join(map(str, self.dash)) == self.canvas.itemcget(self.edge, 'dash'):
            return  # ребро выходит за рамки или самопересекается с другими ребрами
        elif not self.edge and self.outside(x, y):
            return  # отправная точка выходит за рамки
        color = self.color_roi
        if not self.edge:  # начать рисовать многоугольник
            self.draw_edge(color, x, y, self.tag_curr_edge_start)
            # Нарисуйте липкий круг
            self.canvas.create_oval(x - self.radius_circle, y - self.radius_circle,
                                    x + self.radius_circle, y + self.radius_circle,
                                    width=0, fill=color['draw'],
                                    tags=(self.tag_curr_edge, self.tag_curr_circle))
        else:  # продолжить рисование многоугольника
            x1, y1, x2, y2 = self.canvas.coords(self.tag_curr_edge_start)  # получить координаты 1-го края
            x3, y3, x4, y4 = self.canvas.coords(self.edge)  # получить координаты текущего ребра
            if x4 == x1 and y4 == y1:  # закончить рисование многоугольника
                if len(self.polygon) > 2:  # нарисовать многоугольник на увеличенном холсте изображения
                    d = self.roi_dict
                    tag = self.tag_roi
                    self.draw_polygon(self.polygon, color, tag, d)
                self.delete_edges()  # удалить ребра нарисованного многоугольника
            else:
                self.draw_edge(color, x, y)  # продолжить рисование многоугольника, установить новое ребро

    def draw_polygon(self, polygon, color, tag, dictionary):
        """ Нарисовать многоугольник на холсте """
        # Вычислить координаты вершин на увеличенном изображении
        bbox = self.canvas.coords(self.container)  # получить область изображения
        vertices = list(map((lambda i: (i[0] * self.imscale + bbox[0],
                                        i[1] * self.imscale + bbox[1])), polygon))
        # Создать идентификационный тег
        tag_uid = uuid.uuid4().hex  # уникальный идентификатор
        # Создать полигон. 2-й тег ВСЕГДА представляет собой уникальный идентификатор тега + постоянную строку.
        self.canvas.create_polygon(vertices, fill=color['point'],
                                   stipple=color['stipple'], width=0, state='hidden',
                                   tags=(tag, tag_uid + self.tag_const))
        # Создать полилинию. 2-й тег ВСЕГДА является уникальным идентификатором тега.
        for j in range(-1, len(vertices) - 1):
            self.canvas.create_line(vertices[j], vertices[j + 1], width=self.width_line,
                                    fill=color['back'], tags=(self.tag_poly_line, tag_uid))
        # Запомните ROI/отверстие в словаре всех ROI/отверстий
        dictionary[tag_uid] = polygon.copy()

    def draw_edge(self, color, x, y, tags=None):
        """ Нарисовать ребро многоугольника """
        if len(self.polygon) > 1:
            x1, y1, x2, y2 = self.canvas.coords(self.edge)
            if x1 == x2 and y1 == y2:
                return  # не проводите ребро в одной и той же точке, иначе будет самопересечение
        curr_edge_id = self.tag_curr_edge_id + str(len(self.polygon))  # ID ребра в полигоне
        self.edge = self.canvas.create_line(x, y, x, y, fill=color['draw'], width=self.width_line,
                                            tags=(tags, self.tag_curr_edge, curr_edge_id,))
        bbox = self.canvas.coords(self.container)  # получить область изображения
        x1 = round((x - bbox[0]) / self.imscale)  # получить реальный (x, y) на изображении без увеличения
        y1 = round((y - bbox[1]) / self.imscale)
        self.polygon.append((x1, y1))  # добавить новую вершину в список вершин многоугольника

    def popup(self, event):
        """ Всплывающее меню """
        self.motion(event)  # выберите многоугольник во всплывающем меню явно, чтобы убедиться, что он выбран
        if self.selected_poly:  # показывать всплывающее меню только для выбранного полигона
            self.hold_menu1 = True  # всплывающее меню открыто
            self.hold_menu2 = True
            self.menu.post(event.x_root, event.y_root)  # показать всплывающее меню
            self.hold_menu1 = False  # всплывающее меню закрыто

    def motion(self, event):
        """ Отслеживание положения мыши на холсте """
        if self.hold_menu1: return  # всплывающее меню открыто
        x = self.canvas.canvasx(event.x)  # получить координаты события на холсте
        y = self.canvas.canvasy(event.y)
        if self.edge:  # переместить край нарисованного многоугольника
            x1, y1, x2, y2 = self.canvas.coords(self.tag_curr_edge_start)  # получить координаты 1-го ребра
            x3, y3, x4, y4 = self.canvas.coords(self.edge)  # получить координаты текущего ребра
            dx = x - x1
            dy = y - y1
            # Установить новые координаты края
            if self.radius_stick * self.radius_stick > dx * dx + dy * dy:  # радиус прилипания
                self.canvas.coords(self.edge, x3, y3, x1, y1)  # придерживаться начала
                self.set_dash(x1, y1)  # установить тире для краевого сегмента
            else:  # следуй за мышью
                self.canvas.coords(self.edge, x3, y3, x, y)  # следить за движениями мыши
                self.set_dash(x, y)  # установить тире для краевого сегмента
        # Обработка полигонов на холсте
        self.deselect_poly()  # изменить цвет и обнулить выбранный полигон
        self.select_poly()  # изменить цвет и выбрать полигон

    def set_dash(self, x, y):
        """ Установить штрих для краевого сегмента """
        # Если за пределами изображения или полигона произошло самопересечение
        if self.outside(x, y) or self.polygon_selfintersection():
            self.canvas.itemconfigure(self.edge, dash=self.dash)  # установить пунктирную линию
        else:
            self.canvas.itemconfigure(self.edge, dash='')  # установить сплошную линию

    def deselect_poly(self):
        """ Отменить выбор текущего объекта ROI """
        if not self.selected_poly: return  # список выбранных полигонов пуст
        for i in self.selected_poly:
            j = i + self.tag_const  # уникальный тег полигона
            color = self.color_roi # получить цветовую палитру
            self.canvas.itemconfigure(i, fill=color['back'])  # отменить выбор строк
            self.canvas.itemconfigure(j, state='hidden')  # скрыть фигуру
        self.selected_poly.clear()  # очистить список

    def select_poly(self):
        """ Выберите и измените цвет текущего объекта области интереса """
        if self.edge: return  # новый полигон создается (рисуется) прямо сейчас
        i = self.canvas.find_withtag('current')  # идентификатор текущего объекта
        tags = self.canvas.gettags(i)  # получить теги текущего объекта
        if self.tag_poly_line in tags:  # Если это полилиния. 2-й тег ВСЕГДА является уникальным идентификатором тега
            j = tags[1] + self.tag_const  # уникальный тег полигона
            color = self.color_roi # получить цветовую палитру
            self.canvas.itemconfigure(tags[1], fill=color['point'])  # выбрать строки через 2-й тег
            self.canvas.itemconfigure(j, state='normal')  # показать многоугольник
            self.selected_poly.append(tags[1])  # запомнить 2-й уникальный tag_id

    def is_roi(self, tag):
        """ Возвратите True, если полигон является ROI. Возвращает False, если многоугольник является дырой """
        tags = self.canvas.gettags(tag)
        if self.tag_roi in tags:
            return True
        return False

    def redraw_figures(self):
        """ Перезаписанный метод. Перерисовать липкий круг для события колеса """
        bbox = self.canvas.coords(self.tag_curr_circle)
        if bbox:  # радиус липкого круга не меняется при масштабировании
            cx = (bbox[0] + bbox[2]) / 2  # центр круга
            cy = (bbox[1] + bbox[3]) / 2
            self.canvas.coords(self.tag_curr_circle,
                               cx - self.radius_circle, cy - self.radius_circle,
                               cx + self.radius_circle, cy + self.radius_circle)

    def delete_edges(self):
        """ Удалить ребра нарисованного многоугольника """
        if self.edge:  # если полигон рисуется, удалите его
            self.edge = None  # удалить все ребра и установить текущее ребро на None
            self.canvas.delete(self.tag_curr_edge)  # удалить все ребра
            self.polygon.clear()  # удалить все элементы из списка вершин

    def delete_poly(self):
        """ Удалить выбранный полигон """
        self.delete_edges()  # удалить ребра нарисованного многоугольника
        if self.selected_poly:  # удалить выбранный полигон
            for i in self.selected_poly:
                j = i + self.tag_const  # уникальный тег полигона
                if self.is_roi(j):
                    del(self.roi_dict[i])  # удалить ROI из словаря всех ROI
                self.canvas.delete(i)  # удалить строки
                self.canvas.delete(j)  # удалить полигон
            self.selected_poly.clear()  # Очистить выбранный лист
            self.hold_menu2 = False  # закрыть всплывающееся меню

    def delete_all(self):
        """ Удалите все полигоны с холста и очистите переменные. """
        self.delete_edges()  # удалить ребра нарисованного многоугольника
        self.canvas.delete(self.tag_roi)  # удалить все РОИ
        self.canvas.delete(self.tag_poly_line)  # удалить все линии многоугольника
        self.selected_poly.clear()  # очистить список выбора
        self.hold_menu2 = False  # всплывающее меню закрыто
        self.roi_dict.clear()  # очистить словарь ROI

    def reset(self, roi):
        """ Сбросить область интереса и отверстия на изображении """
        self.delete_all()  # удалить старые полигоны
        for polygon in roi:  # рисовать рои-полигоны
            self.draw_polygon(polygon, self.color_roi, self.tag_roi, self.roi_dict)

    @staticmethod
    def orientation(p1, p2, p3):
        """ Найдите ориентацию упорядоченной тройки (p1, p2, p3). Возвращает следующие значения:
             0 --> p1, p2 и p3 коллинеарны
            -1 --> по часовой стрелке
Найдите ориентацию упорядоченной тройки (p1, p2, p3). Возвращает следующие значения:
             0 --> p1, p2 и p3 коллинеарны
            -1 --> по часовой стрелке
             1 --> против часовой стрелки """
        val = (p2[0] - p1[0]) * (p3[1] - p2[1]) - (p2[1] - p1[1]) * (p3[0] - p2[0])
        if   val < 0: return -1  # по часовой стрелке
        elif val > 0: return  1  # против часовой стрелки
        else:         return  0  # коллинеарный

    @staticmethod
    def on_segment(p1, p2, p3):
        """ Для трех коллинеарных точек p1, p2, p3 функция проверяет
            если точка p2 лежит на отрезке p1-p3 """
        # noinspection PyChainedComparisons
        if p2[0] <= max(p1[0], p3[0]) and p2[0] >= min(p1[0], p3[0]) and \
           p2[1] <= max(p1[1], p3[1]) and p2[1] >= min(p1[1], p3[1]):
            return True
        return False

    def intersect(self, p1, p2, p3, p4):
        """ Возвращает True, если отрезки p1-p2 и p3-p4 пересекаются, в противном случае возвращает False """
        # Найдите 4 направления
        o1 = self.orientation(p1, p2, p3)
        o2 = self.orientation(p1, p2, p4)
        o3 = self.orientation(p3, p4, p1)
        o4 = self.orientation(p3, p4, p2)
        # Общий случай
        if o1 != o2 and o3 != o4: return True  # сегменты пересекаются
        # Отрезки p1-p2 и p3-p4 лежат на одной прямой.
        if o1 == o2 == 0:
            # p3 лежит на отрезке p1-p2
            if self.on_segment(p1, p3, p2): return True
            # p4 лежит на отрезке p1-p2
            if self.on_segment(p1, p4, p2): return True
            # p1 лежит на отрезке p3-p4
            if self.on_segment(p3, p1, p4): return True
        return False  # не пересекается

    def penultimate_intersect(self, p1, p2, p3):
        """ Проверяем предпоследнее (последнее) ребро,
            где p1 и p4 совпадают с текущим ребром """
        if self.orientation(p1, p2, p3) == 0 and not self.on_segment(p3, p1, p2):
            return True
        else:
            return False

    def first_intersect(self, p1, p2, p3, p4):
        """ Проверяем 1-е ребро, где точки p2 и p3 МОГУТ совпадать """
        if p2[0] == p3[0] and p2[1] == p3[1]: return False  # p2 и p3 совпадают - это нормально
        if p1[0] == p3[0] and p1[1] == p3[1]: return False  # есть только 1 ребро
        # Есть только 2 ребра
        if p1[0] == p4[0] and p1[1] == p4[1]: return self.penultimate_intersect(p1, p2, p3)
        return self.intersect(p1, p2, p3, p4)  # Общий случай

    def polygon_selfintersection(self):
        """ Проверить, есть ли у многоугольника самопересечения """
        x1, y1, x2, y2 = self.canvas.coords(self.edge)  # получить координаты текущего края
        for i in range(1, len(self.polygon)-2):  # не включать 1-й и последние 2 ребра
            x3, y3, x4, y4 = self.canvas.coords(self.tag_curr_edge_id + str(i))
            if self.intersect((x1, y1), (x2, y2), (x3, y3), (x4, y4)): return True
        # Проверяем предпоследнее (предпоследнее) ребро, где точки p1 и p4 совпадают
        j = len(self.polygon) - 2
        if j > 0:  # 2 или более ребер
            x3, y3, x4, y4 = self.canvas.coords(self.tag_curr_edge_id + str(j))
            if self.penultimate_intersect((x1, y1), (x2, y2), (x3, y3)): return True
        # Проверяем 1-е ребро, где точки p2 и p3 МОГУТ совпадать
        x3, y3, x4, y4 = self.canvas.coords(self.tag_curr_edge_start)
        if self.first_intersect((x1, y1), (x2, y2), (x3, y3), (x4, y4)): return True
        return False  # в многоугольнике нет самопересечений
