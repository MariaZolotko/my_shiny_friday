# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

import pandas as pd
import requests
from bs4 import BeautifulSoup
import telebot
from telebot import types
import re
from random import randint
import config
import dbworker
import math



apikey='8803784b-fa83-4b12-8060-37049f25ef5d'
apikey1='0949a9ad-718d-4f48-ba42-a5d8845724cc'

bot=telebot.TeleBot(config.token)



@bot.message_handler(commands=["info"])
def cmd_info(message):
    dbworker.del_state(message.chat.id)
    bot.send_message(message.chat.id, "*Я - Пятница!* 🎉\n"
                                      "Готова подобрать для тебя хороший барчик поблизости и проложить маршрут.\n"
                                      "Во-первых, тебе нужно поделиться со мной своими координатами без этого никак.\n"
                                      "Затем задать рамки поиска бара в км.\n"
                                      "Я подберу несколько классных бара рядом.", parse_mode='Markdown')
    bot.send_message(message.chat.id, "Ты выберишь один из них.\n"
                                      "А я провожу тебя до него.\n"
                                      "Давай начнем /start.\n"
                                      "Команда /reset начать заново.")


@bot.message_handler(commands=["start"])
def cmd_start(message):
    dbworker.set_state(message.chat.id,config.States.S_START.value)
    hide_keyboard = types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, "Привет! Я - робопятница 🍷 \n"
                                      "Для подбора питейного заведения нужно поделиться со мной геоданными: /geo.\n"
                                      "Все возможные команды найдешь в /commands.\n"
                                      "Скинуть состояние и начать сначала /reset.", reply_markup=hide_keyboard)


@bot.message_handler(commands=["commands"])
def cmd_commands(message):
    bot.send_message(message.chat.id,
                     "/reset - сбросить все состояния.\n"
                     "/start - начать диалог.\n"
                     "/info - описание Пятницы.\n"
                     "/commands - доступные команды.\n"
                     "/geo - отдать свою локацию для поиска барчика рядом.\n"
                     "/bounds - обозначить границы поиска барчика в км.\n")


@bot.message_handler(commands=["geo"])
def geo(message):
    dbworker.set_state(message.chat.id, config.States.S_ENTER_GEO.value)
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True,one_time_keyboard=True)
    button_geo = types.KeyboardButton(text="Поделиться геоданными", request_location=True)
    keyboard.add(button_geo)

    bot.send_message(message.chat.id, "Нажми на кнопку и передай мне свое местоположение", reply_markup=keyboard)


@bot.message_handler(func=lambda message: (dbworker.get_current_state(message.chat.id) == config.States.S_ENTER_GEO.value)
                                          and message.location is None and message.text.strip().lower() not in
                                          ('/reset', '/info', '/start', '/commands',
                                          '/geo','/bounds'))
def not_geo(message):
    bot.send_message(message.chat.id, "Ты не поделился геоданными, так я не смогу найти рядом бар. \n"
                                           "Тебе нужен бар в пятницу или нет...\n"
                                           "Давай жми, буду причинять тебе добро :) /geo\n")

@bot.message_handler(content_types=["location"])
def location(message):
    global longitude
    global latitude
  #  print(message.location is not None)
  #  print((dbworker.get_current_state(message.chat.id) == config.States.S_ENTER_GEO.value) is True)
    if (dbworker.get_current_state(message.chat.id) == config.States.S_ENTER_GEO.value) and (message.location is not None):
        longitude = message.location.longitude
        latitude = message.location.latitude
        coord = str(message.location.longitude) + ',' + str(message.location.latitude)
        r = requests.get(
            'https://geocode-maps.yandex.ru/1.x/?apikey=' + config.apikey + '&format=json&geocode=' + coord)
        if len(r.json()['response']['GeoObjectCollection']['featureMember']) > 0:
            address = \
            r.json()['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['metaDataProperty']['GeocoderMetaData']['text']
            bot.send_message(message.chat.id, f"*Я нашла тебя:*\n{address}\n", parse_mode='Markdown')
            bot.send_message(message.chat.id, f"Теперь займемся барчиками поблизости /bounds.\n")
            dbworker.set_state(message.chat.id, config.States.S_RECEIVE_GEO.value)
        else:
            bot.send_message(message.chat.id, 'Не удалось получить твой адрес')
    else:
        bot.send_message(message.chat.id, 'Не удалось получить твои координаты')

@bot.message_handler(commands=["bounds"])
def bounds(message):
    if dbworker.get_current_state(message.chat.id) == config.States.S_RECEIVE_GEO.value:
        dbworker.set_state(message.chat.id, config.States.S_ENTER_BOUNDS.value)
        bot.send_message(message.chat.id, f"Введи границы поиска баров в км.\n")
    else:
        bot.send_message(message.chat.id, "Сначала нужно поделиться своими геоданными /geo \n"
                                          "и только потом вводить границы поиска.\n")


@bot.message_handler(func=lambda message: (dbworker.get_current_state(message.chat.id) == config.States.S_ENTER_BOUNDS.value)
                                          and message.text.strip().lower() not in
                                          ('/reset', '/info', '/start', '/commands',
                                          '/geo','/bounds'))
def frame(message):
    if message.text.isdigit():
        full_list = []
        longitude_km=(1/(math.cos(longitude) * 111.3))*int(message.text)#добавляю сюда имя операции а не поле!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        latitude_km=(1/111)*int(message.text)
        coord = str(longitude) + ',' + str(latitude)
        spn = str(longitude_km) + ',' + str(latitude_km)
        r = requests.get(
        'https://search-maps.yandex.ru/v1/?apikey=' + config.apikey1 + '&format=json&text=бар&lang=ru_RU&ll=' + coord + '&spn='+spn+'&rspn=1&results=10')
        if len(r.json()['type']) > 0:
            g = r.json()['features']
            for i, k in enumerate(g):
              l = [i+1,k['properties']['name'], k['properties']['description'],k['geometry']['coordinates']]
              full_list.append(l)
            df = pd.DataFrame(full_list)
            df.rename({1: 'name', 2: 'description', 3: 'coordinates'}, axis=1, inplace=True)
            df[['longitude', 'latitude']] = pd.DataFrame(df.coordinates.tolist(), index=df.index)
            df['href'] = 'https://yandex.ru/maps/?pt=' + df.longitude.map(str) + ',' + df.latitude.map(str)
            bot.send_message(message.chat.id, 'Бары рядом:\n')
            for i,n in enumerate(full_list):
                d=df.href[i]
                bot.send_message(message.chat.id, f'*{n[1]}* [{n[2]}]({d})', parse_mode='Markdown')
        else:
          bot.send_message(message.chat.id, "Не удалось найти бары рядом.\n")
          bot.send_message(message.chat.id, "Используя бесплатную версию API яндекса, я не могу сохранять геоданные.\n")
          bot.send_message(message.chat.id, "Поэтому мы можем попробовать только сначала 😂 /reset.\n")
        dbworker.del_state(message.chat.id)
    else:
        bot.send_message(message.chat.id, "Не правильно введены границы поиска в км.\n")
        bot.send_message(message.chat.id, "Нужно ввести целое число.\n")
        bot.send_message(message.chat.id, "Я не смогла сохранить твои данные на предыдущем шаге из-за условий использования бесплатного API Яндекса.\n")
        bot.send_message(message.chat.id, "Попробуем еще раз? /geo.\n")


@bot.message_handler(commands=["reset"])
def cmd_reset(message):
    dbworker.del_state(message.chat.id)
    bot.send_message(message.chat.id,
                     "Давай попробуем еще раз!\n"
                     "Поделись со мной своими геоданными и введи границы поиска бара.\n"
                     "Я подберу несколько классных бара рядом.")
    bot.send_message(message.chat.id, "Давай начнем /start.\n"
                                      "Команда /reset начать заново.")

def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.


def cmd_sample_message(message):
    bot.send_message(message.chat.id, "Привет, я - Пятница!\n"
                                      "Я могу подобрать тебе вино на вечер или просто найти классный барчик рядом\n"
                                      "Нажимай /start и начнем \n"
                                      "Жмякай /info для описания всех моих возможнойстей.\n"
                                      "В /commands можешь посмотреть доступные команды.")

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    bot.infinity_polling()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
