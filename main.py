import os
from typing import Dict, List
import telebot
from telebot import types
from parser import Parser, MusicParser
from config import TOKEN_API


# создаем экземпляр бота, используя токен
bot = telebot.TeleBot(token=TOKEN_API)

# URL для поиска песен
link: str = "https://ru.hitmotop.com/search?q="


# обработчик команды /start
@bot.message_handler(commands=["start"])
def start_cmd(message: types.Message):
    # Отправляем пользователю сообщение с запросом названия песни
    bot.send_message(chat_id=message.chat.id, text="Введите название песни, которую хотите найти...")


# обработчик входящих сообщений с текстом
@bot.message_handler(content_types=["text"])
def message_decorator(message: types.Message):
    # Создаем объект класса MusicParser для извлечения информации со страницы по указанному названию песни
    music_parser: MusicParser = MusicParser(link=link, title=message.text)

    def search_cmd(parser: MusicParser) -> telebot.TeleBot:
        # Инициализируем новую клавиатуру, которая будет отображаться пользователю
        markup: types.ReplyKeyboardMarkup = types.ReplyKeyboardMarkup(resize_keyboard=True)

        # Если на странице нет результатов, отправляем сообщение и завершаем функцию
        if parser.get_all_title() is None:
            return bot.send_message(chat_id=message.chat.id, text="По вашему запросу ничего не найдено...")

        # Создаем кнопку для каждой песни в результате поиска
        for keys, values in parser.create_dict().items():
            markup.add(types.KeyboardButton(text=f"{keys} - {values}"))

        # Отправляем клавиатуру пользователю
        bot.send_message(chat_id=message.chat.id, text="Выберите ту, что вам нужна...", reply_markup=markup)

        # Регистрируем обработчик следующего входящего сообщения со списком найденных песен и выбранной пользователем песней
        # Он будет вызван после выбора пользователем конкретной песни.
        return bot.register_next_step_handler(message=message, callback=main_worker, parser=parser)

    def main_worker(msg: types.Message, parser: MusicParser):
        # Скачиваем выбранную песню на жесткий диск
        parser.download_audio()

        # Получаем полный путь к загруженному музыкальному файлу
        audio_file_path = os.path.join(os.getcwd(), f"{parser.get_title()}.mp3")

        # Отправляем загруженную песню пользователю в виде аудио-файла
        try:
            with open(file=audio_file_path, mode="rb") as audio:
                audio.seek(0)
                bot.send_audio(chat_id=msg.chat.id, audio=audio, reply_markup=types.ReplyKeyboardRemove())
        except Exception as e:
            # Если при отправке файла возникла ошибка, отправляем сообщение об ошибке пользователю
            bot.send_message(chat_id=msg.chat.id, text=f"Произошла ошибка: {str(e)}")

        # Удаляем загруженный файл c жесткого диска
        try:
            parser.delete_audio()
        except Exception as e:
            # Если при удалении файла возникла ошибка, выводим ее в консоль для дальнейшей диагностики
            print(f"Error deleting file: {e}")

    # Вызываем функцию search_cmd для начала поиска и отображения списка найденных песен
    return search_cmd(music_parser)


if __name__ == "__main__":
    # Запускаем бота в бесконечном цикле
    bot.polling(none_stop=True)
