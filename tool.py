import json
import telebot
import models
from datetime import datetime




file = open("RU.json", encoding="utf-8")
ru_bot_text = json.load(file)




def language_check():
    """Подгружаем файл с текстами ответов бота"""
    return ru_bot_text



def create_inlineKeyboard(key, row=0):
    keyboard = telebot.types.InlineKeyboardMarkup()
    key_list = []
    count = 0
    for i in key:
        key_list.append(telebot.types.InlineKeyboardButton(
            text=i, callback_data=key.get(i)))
        count += 1

        if count >= row:
            keyboard.add(*[i for i in key_list])
            key_list = []
            count = 0
        if list(key.keys())[-1] == i:
            keyboard.add(*[i for i in key_list])
    return keyboard


def log(func):
    """Декоратор для красивых логов в консоли"""
    def wrapper(*args, **kwargs):
        message = args[0]
        print("\n ---------")
        print(datetime.now())
        if str(type(message)) == "<class 'telebot.types.Message'>":
            print("From: %s %s. (id: %s)\nText: %s" % (message.from_user.first_name,
                                                       message.from_user.last_name, message.from_user.id, message.text))
        elif str(type(message)) == "<class 'telebot.types.CallbackQuery'>":
            print("From: %s %s. (id: %s)\ncallback: %s" % (message.from_user.first_name,
                                                           message.from_user.last_name, message.from_user.id, message.data))
        return_value = func(*args, **kwargs)
        return return_value
    return wrapper


def get_entities_text(text, e_list):
    """Вернуть текст к оринальному ввиду форматирования Markdown"""
    if e_list == None:
        return text
    text = list(str(text))
    count_of_enity = 0
    for i in e_list:
        char = ""
        last_char = ""
        if str(i.type) == "bold":
            char = "<b>"
            last_char = "</b>"
        elif str(i.type) == "italic":
            char = "<i>"
            last_char = "</i>"
        elif str(i.type) == 'strikethrough':
            char = '<strike>'
            last_char = "</strike>"
        else:
            continue
        ind = int(i.offset)
        end = int(i.length)
        text.insert(ind + count_of_enity, char)
        text.insert(ind+count_of_enity+end + 1, last_char)
        count_of_enity += 2* len(char) + 1
    return "".join(text)




def create_markup(key:list, row=0):
    """Создать репли клавиатуру из списка"""
    user_markup = telebot.types.ReplyKeyboardMarkup(True)
    if row == 0 or row == 1:
        if isinstance(key, str):
            user_markup.add(key)
        else:
            for i in key:
                user_markup.add(i)
    else:
        key_list = key
        for i in split_list(key_list, row):
            user_markup.add(*[telebot.types.KeyboardButton(name)
                              for name in i])
    return user_markup





def reply_markup_combiner(*keyboards):
    """Комбинирование репли клавиатур"""
    user_markup = telebot.types.ReplyKeyboardMarkup(True)
    answer = []
    for i in keyboards:
        for x in i.keyboard:
            answer.append(x)
    for i in answer:
        if list(i) == i:
            user_markup.add(
                *[telebot.types.KeyboardButton(name['text']) for name in i])
        else:
            user_markup.add(i['text'])
    return user_markup
