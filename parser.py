import os
from typing import Optional, List, Dict
import requests
from bs4 import BeautifulSoup
from requests import Response


class Parser:
    # URL для поиска песен
    link: str = "https://ru.hitmotop.com/search?q="

    # Конструктор класса. Принимает два параметра:
    # `link` - URL страницы, с которой надо извлечь информацию.
    # `title` - заголовок страницы.
    def __init__(self, title: str):
        # Выполянем запрос на указанный `link` и сохраняем ответ `response`.
        self.response: Response = requests.get(self.link + title)

    # Метод `soup` возвращает объект `BeautifulSoup`, который используется для парсинга HTML-кода.
    def soup(self) -> BeautifulSoup:
        return BeautifulSoup(self.response.text, "lxml")

    # Метод `get_all_title` возвращает список из двух списков:
    # - список заголовков композиций.
    # - список имен и фамилий авторов композиций.
    def get_all_title(self) -> Optional[tuple[List[str], List[str]]]:
        # Извлекаем из HTML-кода все заголовки композиций.
        title = [title.text.strip() for title in self.soup().find_all("div", class_="track__title")]
        # Извлекаем из HTML-кода все имена и фамилии авторов композиций.
        author = [author.text.strip() for author in self.soup().find_all("div", class_="track__desc")]

        # Если список заголовков не пустой, возвращаем кортеж со списками заголовков и имен авторов.
        # Если список заголовков пустой, возвращаем None.
        return (title, author) if title else None

    # Метод `get_title` возвращает заголовок и имя автора первой композиции.
    def get_title(self) -> str:
        # Извлекаем заголовок первой композиции.
        title: str = self.soup().find("div", class_="track__title").text.strip()
        # Извлекаем имя автора первой композиции.
        author: str = self.soup().find("div", class_="track__desc").text.strip()

        # Возвращаем строку с заголовком и именем автора первой композиции.
        return f"{title} - {author}"

    # Метод `get_link` возвращает ответ типа `requests.Response`, содержащий скачиваемый файл.
    def get_link(self) -> Response:
        # Извлекаем URL для скачивания файла.
        link: str = self.soup().find("a", class_="track__download-btn").get("href")
        # Выполянем запрос на URL для скачивания файла и сохраняем ответ `response`.
        response: Response = requests.get(link, stream=True)

        # Возвращаем ответ `response`, содержащий скачиваемый файл.
        return response


class MusicParser(Parser):
    # Метод `create_dict` возвращает словарь, ключами которого явлются заголовки композиций,
    # а значениями - имена авторов.
    def create_dict(self) -> Dict[str, str]:
        title, author = self.get_all_title()
        return dict(zip(title, author))

    # Метод `download_audio` загружает музыкальный файл и записывает его в файл на жестком диске.
    # Имя файла состоит из заголовка и имени автора первой композиции, а расширение - ".mp3".
    def download_audio(self) -> None:
        with open(file=self.get_title() + ".mp3", mode="wb") as file:
            # Читаем контент файла порциями размером 1МБ и записываем их в файл.
            for chunk in self.get_link().iter_content(chunk_size=1024 * 1024):
                file.write(chunk) if chunk else ValueError("NOT UPLOADED.")

    # Метод `delete_audio` удаляет загруженный музыкальный файл.
    def delete_audio(self) -> None:
        # Удаление файла происходит с помощью метода `os.remove`.
        os.remove(path=os.path.join(os.path.abspath(os.path.dirname(__file__)), f"{self.get_title()}.mp3"))