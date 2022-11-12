import os
import gdal
import rasterio
import numpy as np
from glob import glob
import rioxarray as rxr
from rio_toa import reflectance


def reformat_array(path):
    """Преобразовать массив значений DN в удобную
    форму двумерного массива для машинного обучения"""
    multispecral_image = rxr.open_rasterio(path, masked=True).squeeze().values
    shape = list(multispecral_image.shape)
    array_reshape = multispecral_image.reshape(shape[0], shape[1] * shape[2])
    reformed_array = np.transpose(array_reshape)
    return reformed_array


def cut_polygone(path_to_image, pixel_coordinates):
    """" Вырезать полигон из GeoTiff по координатам пикселей """
    geo_coordinates = []
    for i in pixel_coordinates[0]:
        x, y = i[0], i[1]
        ds = gdal.Open(path_to_image)
        param1, param2, param3, param4, param5, param6 = ds.GetGeoTransform()
        posX = param1 + x * param2 + y * param3
        posY = param4 + x * param5 + y * param6
        geo_coordinates.append((posX, posY))

    geoms = [{'type': 'Polygon', 'coordinates': [geo_coordinates]}]
    with rasterio.open(path_to_image) as src:
        out_image, out_transform = mask(src, geoms, crop=True)
    out_meta = src.meta.copy()
    out_meta.update({"driver": "GTiff",
                     "height": out_image.shape[1],
                     "width": out_image.shape[2],
                     "transform": out_transform})

    with rasterio.open("masked.tif", "w", **out_meta) as dest:
        dest.write(out_image)


def DN_to_TOA_main_image(self):
    """" Преобразовать массив значений DN в TOA главного изображения"""
    dn_image_7 = self.landsat_multispectral_7.values  # значения DN массива 7 спектрального изображения
    MR = 2.0000E-05
    AR = -0.100000

    MTL_file = glob(os.path.normpath(os.path.join(temp_path, "*MTL*.txt")))
    with open(MTL_file[0], 'r', encoding='utf-8') as file:
        for i in file:
            if 'SUN_ELEVATION' in i:
                E = float(i.split('= ')[1])
    self.toa_image = reflectance.reflectance(dn_image_7, MR, AR, E, src_nodata=0)


def DN_to_TOA_learning_image(self, path_to_image):
    """" Преобразовать массив значений DN в TOA изображений для обучения и структурировать их"""
    learning_image = rasterio.open(path_to_image)

    dn_image_7 = learning_image.values  # значения DN массива 7 спектрального изображения
    MR = 2.0000E-05
    AR = -0.100000

    MTL_file = glob(os.path.normpath(os.path.join(temp_path, "*MTL*.txt")))
    with open(MTL_file[0], 'r', encoding='utf-8') as file:
        for i in file:
            if 'SUN_ELEVATION' in i:
                E = float(i.split('= ')[1])
    self.toa_image = reflectance.reflectance(dn_image_7, MR, AR, E, src_nodata=0)
