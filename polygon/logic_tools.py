# -*- coding: utf-8 -*-
import os
import codecs
import pickle

import gdal
import numpy as np
import configparser
import pandas as pd
import tkinter.ttk as ttk

from datetime import datetime

import rasterio
from PIL import Image, ImageDraw
from rasterio.mask import mask

from .action import Action

from polygon import gui_main, logic_config

str_image = 'Image'
str_name = 'Name'
str_md5 = 'MD5'
str_polygons = 'Polygons'
str_roi = 'ROI'
roi = None

path_to_polygonfile = os.path.join(os.path.dirname(__file__).replace('polygon', ''), 'temp\\polygons.xlsx')
save_path = os.path.join(os.path.dirname(__file__).replace('polygon', ''), 'temp\\polygons_for_learning')
mergened_image = os.path.join(os.path.dirname(__file__).replace('polygon', ''), 'temp\\mergened.tif')


def roll(mask,  # массив изображений
         rwin,  # массив скользящих окон
         dx,  # шаг по горизонтали - количество столбцов
         dy):  # шаг по вертикали - количество рядов
    """ Прокручивающееся окно для двумерного массива. Возвращает массив скользящих окон """
    shape = (int((mask.shape[0] - rwin.shape[0]) / dy) + 1,) + \
            (int((mask.shape[1] - rwin.shape[1]) / dx) + 1,) + rwin.shape
    strides = (mask.strides[0] * dy, mask.strides[1] * dx,) + mask.strides
    return np.lib.stride_tricks.as_strided(mask, shape=shape, strides=strides)


def get_images(imframe, config):
    """ Получите набор небольших изображений для машинного обучения """
    mask = Image.new('1', (imframe.imwidth, imframe.imheight), False)  # создать побитовый массив False
    for roi in imframe.roi_dict.values():  # для всех полигонов ROI изображения
        ImageDraw.Draw(mask).polygon(roi, outline=True, fill=True)  # заполнить маску
    mask = np.array(mask, dtype=np.bool)  # преобразовать маску в массив Numpy
    w, h = config.get_roll_size()  # получить кортеж (ширину, высоту) скользящего окна
    dx, dy = config.get_step_size()  # получить кортеж (dx, dy) шагов скользящего окна
    rwin = np.full((h, w), True, dtype=np.bool)  # создать скользящее окно
    found = np.all(np.all(roll(mask, rwin, dx, dy) == rwin, axis=2), axis=2)  # найти все совпадения
    # Получить все найденные координаты верхнего левого угла прямоугольника
    found = np.transpose(found.nonzero()) * [dy, dx]
    name = os.path.basename(imframe.path)[:-4]  # получить имя файла изображения без расширения
    name += '_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S')  # добавить дату_время
    n = str(len(str(len(found))))  # нулевое число заполнения
    m = str(len(str(max(imframe.imwidth, imframe.imheight))))  # нулевое число заполнения
    for i, c in enumerate(found):  # для каждой координаты верхнего левого угла прямоугольника
        im = imframe.crop((c[1], c[0], c[1] + w, c[0] + h))  # вырезать подпрямоугольник из изображения
        imname = ('{name}_{i:0' + n +
                  '}_{c1:0' + m +
                  '}-{c0:0' + m +
                  '}.png').format(name=name, i=i, c0=c[0], c1=c[1])  # создать имя файла
        im.save(os.path.join(config.config_dir, imname))  # сохранить изображение в папку config dir


def open_polygons(imframe, path):
    """ Открывайте полигоны (ROI и отверстия) и показывайте их на холсте """
    parser = configparser.ConfigParser()  # создать парсер конфигурации
    parser.optionxform = lambda option: option  # сохранить футляр для писем
    parser.read(path)  # прочитать файл с полигонами
    """
    if parser[str_image][str_md5] != imframe.md5:  # check md5 sum
        raise Exception('Wrong polygons. MD5 sum of image and from selected file should be equal.')
    """
    roi = parser[str_polygons][str_roi]  # получить информацию о рои
    roi = pickle.loads(codecs.decode(roi.encode(), 'base64'))  # развернуть информацию о ROI
    imframe.reset(roi)  # очистить старые и нарисовать новые полигоны


def save_polygons(imframe, config):
    """ Сохранение полигонов (ROI и отверстий) в файл """
    parser = configparser.ConfigParser()  # создать парсер конфигурации
    parser.optionxform = lambda option: option  # preserve case for letters
    parser.add_section(str_image)
    parser[str_image][str_name] = imframe.path
    parser[str_image][str_md5] = imframe.md5
    parser.add_section(str_polygons)
    global roi
    roi = list(imframe.roi_dict.values())  # получить список роев
    parser[str_polygons][str_roi] = codecs.encode(pickle.dumps(roi), 'base64').decode()  # обернуть информацию
    uid = datetime.now().strftime('%Y-%m-%d_%H-%M-%S.%f')  # уникальный идентификатор
    name = os.path.basename(imframe.path)[:-4]  # получить имя файла изображения без расширения
    name += '_' + uid + '.txt'  # уникальное имя
    path = os.path.join(config.config_dir, name)
    with open(path, 'w') as file:
        parser.write(file)  # сохранить информацию
    imframe.delete_all()
    imframe.polygons_list.append(roi)


def save_polygons_for_learning(name, classname, color):
    """Записывает в файл polygons.xlsx сохраненные координаты полигонов, метки классов и сами классы"""
    path = os.path.join(os.path.dirname(__file__).replace('polygon', ''), 'temp\\polygons.xlsx')
    roi_list = roi
    df = pd.DataFrame(pd.read_excel(path))
    df.loc[len(df.index)] = [f'{roi_list}', int(name), classname, color]
    df.to_excel(path, index=None)


def clear_save_polygons(config):
    """Очищает файл polygons.xlsx путем его пересоздания"""
    path = os.path.join(config.config_dir, 'polygons.xlsx')
    df = pd.DataFrame(columns=(['PolygonCoordinates', 'Name', 'ClassName', 'Color']))
    df.to_excel(path, index=None)


def cut_polygons():
    df = np.array(pd.read_excel(path_to_polygonfile))
    df_new = df.tolist()
    for line in df_new:
        classname = line[1]
        color = str(line[3])
        color_list = color.translate({ord(i): None for i in ['(', ')', ' ']})
        parts = color_list.rsplit(',', 3)
        R, G, B = parts[0], parts[1], parts[2]
        count = 1
        for polygon_coordinate in eval(line[0]):
            geo_coordinates = []
            for i in polygon_coordinate:
                x, y = i[0], i[1]
                ds = gdal.Open(mergened_image)
                param1, param2, param3, param4, param5, param6 = ds.GetGeoTransform()
                posX = param1 + x * param2 + y * param3
                posY = param4 + x * param5 + y * param6
                geo_coordinates.append((posX, posY))

            geoms = [{'type': 'Polygon', 'coordinates': [geo_coordinates]}]
            with rasterio.open(mergened_image) as src:
                out_image, out_transform = mask(src, geoms, crop=True)
            out_meta = src.meta.copy()
            out_meta.update({"driver": "GTiff",
                             "height": out_image.shape[1],
                             "width": out_image.shape[2],
                             "transform": out_transform})
            name = os.path.join(save_path, f'{classname}_{R}_{G}_{B}_{count}.tif')
            with rasterio.open(name, "w", **out_meta) as dest:
                dest.write(out_image)
                count += 1


def train():
    config = logic_config.Config()  # Экземпляр класса logic_config
    oppened_im_path = config.get_opened_path()  # Путь к открытому изображению
    segmentation = Action(oppened_im_path)
    segmentation.execute()
