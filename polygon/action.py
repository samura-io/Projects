import os
from glob import glob
from rio_toa import reflectance
from PIL import Image
import numpy as np
import pandas as pd
from .ml_models import MLModels
import rioxarray as rxr


class Action():
    """ Самостоятельный класс. Использует заранее поготовленные данные
     Данный класс переобразует изображения в два датасета:
     первый - для предсказания класса типа поверхности;
     второй - для обучения на основе выбранных участках типов поверхности. """

    def __init__(self, path):
        # Путь к текущему изображению:
        self.path_to_main_image =  os.path.join(os.path.dirname(__file__).replace('polygon', ''), 'temp\\mergened.tif')
        self.temp_path = os.path.join(os.path.dirname(__file__).replace('polygon', ''), 'temp\\landsat')
        self.shape = ()  # Размер массива (необходим для сборки изображения)
        self.path_to_polygons_file = os.path.join(os.path.dirname(__file__).replace('polygon', ''),
                                                  'temp\\polygons.xlsx')

        self.reformed_array = None
        self.learning_array = None
        self.learning = None

    def DN_to_TOA_main_image(self, array):
        """" Преобразовать массив значений DN в TOA главного изображения"""
        MR = 2.0000E-05
        AR = -0.100000

        MTL_file = glob(os.path.normpath(os.path.join(self.temp_path, "*MTL*.txt")))
        with open(MTL_file[0], 'r', encoding='utf-8') as file:
            for i in file:
                if 'SUN_ELEVATION' in i:
                    E = float(i.split('= ')[1])
        toa_image = reflectance.reflectance(array, MR, AR, E, src_nodata=0)
        return toa_image

    def reformat_array(self):
        """Преобразовать массив значений DN в удобную
        форму двумерного массива для машинного обучения"""
        multispecral_image = rxr.open_rasterio(self.path_to_main_image, masked=True).squeeze().values
        self.shape = multispecral_image.shape
        list_shape = list(self.shape)
        array_reshape = multispecral_image.reshape(list_shape[0], list_shape[1] * list_shape[2])
        reformed = np.transpose(array_reshape)
        self.reformed_array = self.DN_to_TOA_main_image(reformed)

    # def img_to_dataset(self):
    #     """" Переобразует текущее изображение в набор данных для предсказания """
    #
    #     image_open = Image.open(self.path_to_main_image)  # self.path_to_main_image
    #     array = np.asarray(image_open, dtype='uint8')
    #     self.shape = list(array.shape)
    #
    #     self.line_list = []
    #     for lines in array:
    #         for line in lines:
    #             line = line.tolist()
    #             self.line_list.append(line)

    def reformat_array_learning_dataset(self, classname, R, G, B):
        """Преобразовать массив значений DN в удобную
        форму двумерного массива для машинного обучения С МЕТКАМИ"""
        marker = classname, R, G, B
        multispecral_image = rxr.open_rasterio(path, masked=True).squeeze().values #
        list_shape = list(multispecral_image.shape)
        array_reshape = multispecral_image.reshape(list_shape[0], list_shape[1] * list_shape[2])
        reformed_array = np.transpose(array_reshape)
        x = reformed_array[~np.isnan(reformed_array).any(axis=1), :]  # удалить NAN строки
        x1 = np.delete(x, list(range(0, x.shape[0], 2)), axis=0)  # сократить матрицу в 2 раза
        x2 = self.DN_to_TOA_main_image(x1)
        markered_array = np.full((x2.shape[0], 4), marker, dtype='int16')
        print(markered_array)
        x3 = np.concatenate((x2, markered_array), axis=1, dtype='float16')
        if self.learning_array is None:
            self.learning_array = x3
        else:
            self.learning_array = np.concatenate((self.learning_array, x3), axis=0, dtype='float16')
        print('Ok')

    def collect_image(self, array):
        arr = np.array(array.iloc[:, 7].values)
        new_list = []

        polygons_file = pd.read_excel(self.path_to_polygons_file, header=None)
        classname_color = dict(polygons_file.iloc[:, 1:4:2].to_dict('split')['data'][1:])

        for line in arr:
            line = list(eval(classname_color[line]))
            new_list.append(line)

        new_arr = np.array(new_list).reshape(self.shape[1], self.shape[2], 3)  # [783, 831, 3]
        new_img = Image.fromarray(new_arr.astype(np.uint8))
        new_img.save('result.tif')
        new_img.show()



    def execute(self):
        """"Выполнить все функции класса"""
        print("Загружаем основное изображение")
        self.reformat_array()  # Получили данные из большого изображения и преобразовали
        print("Подготавливаем изображения для обучения")
        path_to_images = os.path.join(os.path.dirname(__file__).replace('polygon', ''), 'temp\\polygons_for_learning')
        count = 0
        all = len(os.listdir(path_to_images))
        for i in os.listdir(path_to_images):
            path_to_image = os.path.join(path_to_images, i)
            parts = i.rsplit('_', 4)  # ['classmane', 'R', 'G', 'B']
            classname, R, G, B = int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])
            self.reformat_array_learning_dataset(classname, R, G, B)
            count += 1
            print(count, 'из', all)
        print("Машинное обучение")
        ml = MLModels(dataset=self.reformed_array, dataset_for_learning=self.learning_array)
        result = ml.random_forest()
        print(f'Shape: {self.shape}')
        self.collect_image(result)










    # def img_to_learning_dataset(self, classname, path):
    #     """ Создает датасеты для обучения из вырезанных изображений """
    #     l_image_open = Image.open(path)
    #     l_array = np.asarray(l_image_open, dtype='uint8')
    #
    #     for lines in l_array:
    #         for line in lines:
    #             line = line.tolist()
    #             line.pop(-1)
    #             if line != [0, 0, 0]:
    #                 line.append(classname)
    #                 self.line_list_learning.append(line)
    #             else:
    #                 pass

    # def dataset_to_image(self, data):
    #     arr = np.array(data)
    #     new_list = []
    #
    #     polygons_file = pd.read_excel(self.path_to_polygons_file, header=None)
    #     classname_color = dict(polygons_file.iloc[:, 1:4:2].to_dict('split')['data'][1:])
    #
    #     for line in arr:
    #         line = list(eval(classname_color[line[3]]))
    #         new_list.append(line)
    #
    #     new_arr = np.array(new_list).reshape(self.shape)  # [783, 831, 3]
    #     new_img = Image.fromarray(new_arr.astype(np.uint8))
    #     new_img.show()
    #
    # def clear_dataset(self):
    #     pass
    #
    #
    # def execute(self):
    #     """"Выполнить все функции класса"""
    #     self.img_to_dataset()
    #     path_to_images = os.path.join(os.path.dirname(__file__).replace('polygon', ''), 'temp\\polygons_for_learning')
    #     for i in os.listdir(path_to_images):
    #         path_to_image = os.path.join(path_to_images, i)
    #         classname = re.sub(r'\_+\w+\.png', '', i)
    #         self.img_to_learning_dataset(classname=classname, path=path_to_image)
    #     ml = MLModels(dataset=self.line_list, dataset_for_learning=self.line_list_learning)
    #     result = ml.random_forest()
    #     self.dataset_to_image(result)



if __name__ == '__main__':

    path = os.path.join(os.path.dirname(__file__).replace('polygon', ''), 'temp\\main.tif')

    action = Action(path)
    action.execute()

