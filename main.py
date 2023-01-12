import os
import time

import requests
import telebot

from bs4 import BeautifulSoup
from telebot import types

from config import TOKEN_API

bot = telebot.TeleBot(TOKEN_API)


link = "https://ru.hitmotop.com/search?q="


def get_all_title(title):
    response = requests.get(link + title)
    soup = BeautifulSoup(response.text, "html.parser")

    song_title = [title.text.strip() for title in soup.find_all("div", class_="track__title")]
    song_auther = [auther.text.strip() for auther in soup.find_all("div", class_="track__desc")]

    song_music = {}

    for i in range(0, len(song_title)):
        song_music[song_title[i]] = song_auther[i]

    return None if song_music == {} else song_music


def get_title(song_name: str) -> str:
    response = requests.get(link + song_name)
    soup = BeautifulSoup(response.text, "html.parser")

    song_title = soup.find("div", class_="track__title").text.strip()

    song_title_auther = soup.find("div", class_="track__desc").text.strip()

    return f"{song_title} - {song_title_auther}"


def download_music(song_name: str):
    page = requests.get(link + song_name)
    soup = BeautifulSoup(page.text, "html.parser")

    song_link = soup.find("a", class_="track__download-btn").get("href")
    response = requests.get(song_link, stream=True)

    with open(get_title(song_name) + ".mp3", "wb") as file:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            file.write(chunk) if chunk else ValueError("NOT UPLOADED")


def delete_music(song_name: str):
    path = os.path.join(os.path.abspath(os.path.dirname(__file__)), f"{get_title(song_name)}.mp3")
    os.remove(path)


@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "Введите название песни, куторую хотите найти...")


@bot.message_handler(content_types=["text"])
def text_song(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    if get_all_title(message.text) is None:
        return bot.send_message(message.chat.id, "По вашему запросу ничего не найдено...")

    for key, value in get_all_title(message.text).items():
        markup.add(types.KeyboardButton(text=f"{key} - {value}"))

    bot.send_message(message.chat.id, "Выберите ту, что вам нужна...", reply_markup=markup)
    return bot.register_next_step_handler(message, halo)


def halo(message):
    bot.send_message(message.chat.id, "Подождите, идет загрузка...")
    download_music(message.text)
    audio = open(os.path.join(os.path.abspath(os.path.dirname(__file__)), f"{get_title(message.text)}.mp3"), "rb")
    bot.send_audio(message.chat.id, audio, reply_markup=types.ReplyKeyboardRemove())
    bot.delete_message(message.chat.id, message.message_id + 1)
    audio.close()
    delete_music(message.text)


while True:
    try:
        bot.polling(none_stop=True)

    except Exception as e:
        print(e.args[0])
        time.sleep(15)
