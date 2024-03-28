import os
from flask import Flask, request
from telebot import types, TeleBot, logger
from dotenv import load_dotenv
import logging
import requests
from bot.CRUD.crud_utils import save, get_phone, update, get_client


load_dotenv()

POSTE_TOKEN=os.getenv('POSTE_TOKEN')
POSTER_URL=os.getenv('POSTER_URL')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_URL = os.getenv('TELEGRAM_URL')
DEBUG_SWITCH = os.getenv('DEBUG_SWITCH')


bot = TeleBot(TELEGRAM_TOKEN, threaded=False)
app = Flask(__name__)
logger = logger
logger.setLevel(logging.DEBUG)


def to_present(phone):
    count = 0
    present_info = {
        'to_cup': 0,
        'cups': 0
    }

    client_id = get_client_id(phone)
    response = requests.get(f'https://joinposter.com/api/clients.getClient?format=json&token={POSTE_TOKEN}&client_id={client_id}')
    accumulation_products = response.json()['response'][0]['accumulation_products']
    prize_products = response.json()['response'][0]['prize_products']

    present_info['cups'] = len(prize_products)

    if accumulation_products:
        for cup in accumulation_products['4']['products']:
            count += cup['count']

    present_info['to_cup'] = 4 - count

    return present_info


def get_client_id(phone):
    response = requests.get(f'https://joinposter.com/api/clients.getClients?format=json&token={POSTE_TOKEN}&phone={phone}')
    if response.json()['response']:
        return response.json()['response'][0]['client_id']
    else:
        return response.json()['response']


@bot.message_handler(commands=['start'])
def start(message):
    name = message.from_user.first_name
    chat_id = message.chat.id
    exist = get_client(chat_id)
    if not exist:
        markup = types.InlineKeyboardMarkup()
        button_phone = types.InlineKeyboardButton(text="Отправить номер телефона", callback_data='send_phone')
        button_manual = types.InlineKeyboardButton(text="Ввести номер вручную", callback_data='enter_phone_manual')
        markup.add(button_phone, button_manual)
        bot.send_message(chat_id, "Укажите номер телефона каторый зарегестрирован в системе дружбы SINA", reply_markup=markup)
    else:
        markup = types.InlineKeyboardMarkup()
        button_yes = types.InlineKeyboardButton(text="Да", callback_data='yes')
        button_no = types.InlineKeyboardButton(text="Нет", callback_data='no')
        markup.add(button_yes, button_no)
        bot.send_message(chat_id, f'Добрый день {name}, вы зарегестрированы с номером телефона {exist["phone"]}. Хотите обновить информацию?', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def send_contact(call):
    chat_id = call.message.chat.id
    if call.data == 'send_phone':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        button_phone = types.KeyboardButton(text="Отправить", request_contact=True)
        markup.add(button_phone)
        bot.send_message(chat_id, "Нажмите кнопку ниже, чтобы отправить ваш номер телефона.", reply_markup=markup)
    elif call.data == 'enter_phone_manual':
        bot.send_message(chat_id, "Введите номер телефона в формате +998123456789")
    elif call.data == 'yes':
        markup = types.InlineKeyboardMarkup()
        button_phone = types.InlineKeyboardButton(text="Отправить номер телефона", callback_data='send_phone')
        button_manual = types.InlineKeyboardButton(text="Ввести номер вручную", callback_data='enter_phone_manual')
        markup.add(button_phone, button_manual)
        bot.send_message(chat_id, "Укажите номер телефона каторый зарегестрирован в системе дружбы SINA", reply_markup=markup)
    elif call.data == 'no':
        bot.send_message(chat_id, "Спасибо.")
    bot.answer_callback_query(call.id)


@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    phone_number = message.contact.phone_number
    chat_id = message.chat.id
    client_id = get_client_id(phone_number)
    if client_id:
        exist = get_client(chat_id)
        if exist:
            update(phone_number, chat_id)
            bot.send_message(chat_id, "Информация обновлена.", reply_markup=types.ReplyKeyboardRemove())
        else:
            save(phone_number, chat_id)
            bot.send_message(message.chat.id, f"Ваш номер телефона: {phone_number}", reply_markup=types.ReplyKeyboardRemove())
    else:
        bot.send_message(chat_id, f'{phone_number} - такого номера телефона в системе дружбы не найдено.\nОтправте номер телефона вручную в формате +998123456789', reply_markup=types.ReplyKeyboardRemove())


@bot.message_handler(regexp=r'^\+\d{12}$')
def handle_manual_number(message):
    phone_number = message.text
    chat_id = message.chat.id
    client_id = get_client_id(phone_number)
    if client_id:
        exist = get_client(chat_id)
        if exist:
            update(phone_number, chat_id)
            bot.send_message(chat_id, "Информация обновлена.")
        else:
            save(phone_number, chat_id)
            bot.send_message(message.chat.id, f"Ваш номер телефона: {phone_number}")
    else:
        bot.send_message(chat_id, f'{phone_number} - такого номера телефона в системе дружбы не найдено.')


@bot.message_handler(commands=['cups'])
def cups(message):
    phone = get_phone(message.chat.id)
    present_info = to_present(phone)
    if present_info['to_cup'] == 0:
        to_cup_ending = 'кружек'
    elif present_info['to_cup'] == 1:
        to_cup_ending = 'кружка'
    else:
        to_cup_ending = 'кружки'

    if present_info['cups'] == 0:
        cups_ending = 'кружек'
    elif present_info['cups'] == 1:
        cups_ending = 'кружка'
    else:
        cups_ending = 'кружки'
    bot.send_message(message.chat.id, f'У вас осталось {present_info["to_cup"]} {to_cup_ending} до бесплатной.\n{present_info["cups"]} накопленых {cups_ending}')


@bot.message_handler(func=lambda message: True, content_types=['text'])
def echo_message(message):
    bot.send_message(message.chat.id, message.text)


@app.route(f'/{TELEGRAM_TOKEN}', methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200


@app.route('/')
def index():
    bot.remove_webhook()
    bot.set_webhook(url=TELEGRAM_URL)
    return 'OK', 200


if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=TELEGRAM_URL)
    app.run(debug=DEBUG_SWITCH)

