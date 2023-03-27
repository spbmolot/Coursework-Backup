import requests
import time
import json
from alive_progress import alive_bar


class VkGetPhotos:
    """
    Создает словарь для загрузки.

    Запрашивает в VK по API количество лайков каждой фотографии профиля и ссылку на фотографию максимального размера.
    Формирует из полученных данных словарь где ключами является количество лайков с расширением (.jpg),
    если количество лайков одинаковое, то к ним добавляется дата в "unix" формате.
    Эти ключи в последующим будут именами файлов. Значениями ключей являются ссылки.

    """
    URL = 'https://api.vk.com/method/'

    def __init__(self, token_vk, version, user_id):
        """
        Создает основные параметры доступа к API VK.

        Для доступа к API VK требуется версия :v: и токен :access_token:.

        """
        self.user_id = user_id
        self.params = {
            'access_token': token_vk,
            'v': version
        }

    def get_photos_profile(self):
        """
        Получает из VK josn файл.

        Подключается по API VK с введенными пользователем параметрами :user_id: и
        возвращает josn файл со ссылками на первые фотографий (по умолчанию установлено 5).
        :return: req:

        """
        group_url_method = self.URL + 'photos.get'
        r_params = {
            'user_id': self.user_id,
            'album_id': 'profile',
            'extended': 1,
            'count': 5
        }
        req = requests.get(group_url_method, params={**self.params, **r_params}).json()
        req = req['response']['items']
        return req

    def creates_dict(self):
        """
        Создает словарь :name_image:.

        В словаре ключами являются наименование сформированное из количества лайков фото, а
        значения ссылки на фотографию профиля в максимальном разрешении.
        Дополнительно создаёт json-файл "photo information" с информацией по файлам.
        :return: name_image

        """
        req = self.get_photos_profile()
        name_image = {}
        list_info = []
        for i in range(len(req)):
            href_image = req[i]['sizes'][-1]['url']  # УРЛ для загрузки фото из ВК
            like_name = f"{req[i]['likes']['count']}.jpg"
            if like_name not in name_image:
                name_image[like_name] = href_image
                list_info.append({
                    "file_name": like_name,
                    "size": req[i]['sizes'][-1]['type']
                })
            else:
                like_name = f"{req[i]['likes']['count']}_{req[i]['date']}.jpg"
                name_image[like_name] = href_image
                list_info.append({
                    "file_name": like_name,
                    "size": req[i]['sizes'][-1]['type']
                })
        with open('photo information.json', 'w') as f:
            json.dump(list_info, f, indent=4)
        return name_image


class YandexDisk:
    """
    Загружает фото на яндекс диск

    Получает список в виде словаря из класса :VkGetPhotos: и загружает
    фотографии на яндекс диск в указанную папку.

    """
    url = 'https://cloud-api.yandex.net/v1/disk/'

    def __init__(self, token_ya):
        self.token = token_ya
        self.folder = 'Backup photos VK'
        self.headers = self.__get_headers()

    def __get_headers(self):
        """
        Создает основные параметры доступа к API яндекс диска.

        Для доступа к API требуется :Authorization: токен для яндекс диска.

        """
        return {'Authorization': 'OAuth {}'.format(self.token)}

    def creating_folder(self, folder):
        """
        Создает папку на яндекс диске.

        Получает на вход название папки и создает её на яндекс диске,
        если папка уже есть, то информирует об этом.
        :return: folder: Название папки.

        """
        group_url_method = self.url + 'resources'
        params = {'path': folder}
        response = requests.put(group_url_method, headers=self.headers, params=params)
        if response.status_code == 201:
            print(f'Папка "{folder}" создана на Я.Диске')
        else:
            print(response.json()['message'])

    def upload_file_to_disk(self, dict_name_image):
        """
        Загружает фото по ссылке на яндекс диск.

        Получает на вход словарь с именами файлов в виде ключей и значениями в виде ссылки
        на файл который требуется загрузить.
        :param dict_name_image: словарь в формате {Наименование файла: ссылка на фото}

        """
        group_url_method = self.url + 'resources/upload'
        self.creating_folder(self.folder)

        with alive_bar(len(dict_name_image), bar='bubbles') as bar:
            for file, upload_file in dict_name_image.items():
                time.sleep(0.33)
                params = {
                    'url': upload_file,
                    'path': f'{self.folder}/{file}',
                    'disable_redirects': 'true'
                }
                response = requests.post(group_url_method, headers=self.headers, params=params)
                bar()
                if response.status_code == 202:
                    print(f'Файл "{file}" загружен на Я.Диск')
                else:
                    print(response.json()['message'])


if __name__ == "__main__":
    with open('token.txt', 'r') as file_object:
        TOKEN_VK = file_object.readline().strip()
        TOKEN_YA = file_object.readline().strip()

    # TOKEN_VK = input("Введите VK token: ")
    # TOKEN_YA = input("Введите YA token: ")

    user = int(input("Введите id пользователя: "))
    vk_client = VkGetPhotos(TOKEN_VK, '5.131', user)
    ya = YandexDisk(TOKEN_YA)
    ya.upload_file_to_disk(vk_client.creates_dict())
