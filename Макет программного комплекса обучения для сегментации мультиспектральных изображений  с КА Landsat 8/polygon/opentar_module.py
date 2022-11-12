import os
import re
from glob import glob
import numpy as np
import pandas as pd
import xarray as xr
import rioxarray as rxr
from rio_toa import reflectance
import pathlib
from rio_toa import toa_utils

import os
import tarfile
from glob import glob
from tkinter.ttk import Progressbar
import tkinter as tk
from tkinter import messagebox as mb
import earthpy.plot as ep
from PIL import Image
import rasterio

temp_path = os.path.dirname(__file__).replace('polygon', r'temp\landsat')


class OpenFile:

    def __init__(self, archive):
        self.archive = archive
        self.files_paths_list = [] # отсортированный список путей к изображениям с 1 по 7 канал
        self.landsat_multispectral_7 = []  # массив значений DN 7-канальноего изображения
        self.toa_image = None # массив мультиспектральных данных

        if tarfile.is_tarfile(self.archive):  # не открывает прогрессбар если закрыть окно выбора файла
            self.root = tk.Tk()
            self.root.title('Загрузка')
            self.root.geometry('300x80')
            self.root.config(bg='#345')
            self.pb = Progressbar(self.root, orient='horizontal', mode='determinate', length=250)
            self.pb.pack(expand=True)
            self.pb.configure(maximum=100)
            self.i = 0


    def unzip(self):
        if tarfile.is_tarfile(self.archive):
            with tarfile.open(self.archive, mode='r') as tar_archive:
                for file_name in tar_archive.getnames():
                    tar_archive.extract(file_name, path=temp_path)
        else:
            mb.showinfo('Нет изображения', 'Загрузите файл с расширением .tar')


    def file_parsere(self):
        self.files_paths_list = glob(os.path.join(temp_path, "*B*.tif"))  # Создать список с файлами каналами
        self.files_paths_list.sort()  # Отсортировать список
        self.files_paths_list.pop()
        return self.files_paths_list

    def open_clean_bands(self, band_path):
        """Открыть GEOTIFF файл"""
        self.ras_meta = rxr.open_rasterio(band_path, masked=True).squeeze()
        return self.ras_meta

    def get_rgb_image(self):
        all_bands = []
        for i, aband in enumerate(self.files_paths_list):
            all_bands.append(self.open_clean_bands(aband))
            all_bands[i]["band"] = i + 1

        self.landsat_multispectral_7 = xr.concat(all_bands, dim="band")

        ax, image = ep.plot_rgb(self.landsat_multispectral_7.values,
                                rgb=[3, 2, 1],
                                title="RGB Composite Image\n Post Fire Landsat Data",
                                stretch=True,
                                str_clip=2)

        img = Image.fromarray(image.astype(np.uint8))
        path_result_im = (os.path.join(temp_path.replace('landsat', ''), 'res.tif'))
        if os.path.isfile(path_result_im):
            os.remove(path_result_im)
        img.save(path_result_im)
        return path_result_im


    def clear_temp(self):
        for file in os.listdir(temp_path):
            os.remove(os.path.join(temp_path, file))

    def act_rgb(self):
        self.progress_bar_point(20)
        self.clear_temp()
        self.progress_bar_point(20)
        self.unzip()
        self.progress_bar_point(20)
        self.file_parsere()
        self.progress_bar_point(20)
        rgb = self.get_rgb_image()
        self.progress_bar_point(20)
        self.deli()

        return rgb

    def progress_bar_point(self, i):
        self.i += i
        self.pb.configure(value=self.i)
        self.pb.update()
        if self.i >= 100:
            self.root.destroy()
            self.i = 0

    def deli(self):
        path = os.path.join(os.path.dirname(__file__).replace('polygon', ''), 'temp\\mergened.tif')
        with rasterio.open(self.files_paths_list[0]) as src:
            ras_meta = src.profile
            ras_meta['count'] = 7

        with rasterio.open(path, 'w', **ras_meta) as dst:
            dst.write(self.landsat_multispectral_7)



if __name__ == '__main__':
        path_to_archive = os.path.dirname(__file__).replace('polygon',
                                                            r'data\LC08_L2SP_176029_20210825_20210901_02_T1.tar')
        imload = OpenFile(path_to_archive)

