import os
from flask import Flask, request
from telebot import types, TeleBot, logger
from dotenv import load_dotenv
import logging
import requests
from bot.CRUD.crud_utils import save, get_phone, update


load_dotenv()

POSTE_TOKEN=os.getenv('TOKEN_POSTER')
POSTER_URL=os.getenv('URL_POSTER')
TELEGRAM_TOKEN = os.getenv('TOKEN')
TELEGRAM_URL = os.getenv('URL')
DEBUG_SWITCH = os.getenv('DEBUG_SWITCH')
print('!!!!!!!!!!!!')
print(POSTER_URL)
print(TELEGRAM_TOKEN)
print(TELEGRAM_URL)
print(POSTE_TOKEN)
print(DEBUG_SWITCH)
print('!!!!!!!!!!!!')

bot = TeleBot(TOKEN, threaded=False)
app = Flask(__name__)
logger = logger
logger.setLevel(logging.DEBUG)

user_data = {}

def to_present(phone):
    count = 0
    client_id = get_client_id(phone)
    response = requests.get(f'https://joinposter.com/api/clients.getClient?format=json&token={TOKEN_POSTER}&client_id={client_id}')
    accumulation_products = response.json()['response'][0]['accumulation_products']
    prize_products = response.json()['response'][0]['prize_products']
    if prize_products:
        return count
    if accumulation_products:
        for cup in accumulation_products['4']['products']:
            count = 4 - cup['count']
        return count
    return 4


def get_client_id(phone):
    response = requests.get(f'https://joinposter.com/api/clients.getClients?format=json&token={TOKEN_POSTER}&phone={phone}')
    return response.json()['response'][0]['client_id']


@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    button_phone = types.InlineKeyboardButton(text="Отправить номер телефона", callback_data='send_phone')
    button_manual = types.InlineKeyboardButton(text="Ввести номер вручную", callback_data='enter_phone_manual')
    markup.add(button_phone, button_manual)
    bot.send_message(message.chat.id, "Укажите номер телефона каторый зарегестрирован в системе дружбы SINA", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def send_contact(call):
    chat_id = call.message.chat.id
    phone_number = user_data.get(chat_id)
    if call.data == 'send_phone':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        button_phone = types.KeyboardButton(text="Отправить", request_contact=True)
        markup.add(button_phone)
        bot.send_message(chat_id, "Нажмите кнопку ниже, чтобы отправить ваш номер телефона.", reply_markup=markup)
    elif call.data == 'enter_phone_manual':
        bot.send_message(chat_id, "Введите номер телефона в формате +998123456789")
    elif call.data == 'yes' and phone_number:
        update(phone_number, chat_id)
        bot.send_message(chat_id, "Информация обновлена.", reply_markup=types.ReplyKeyboardRemove())
    elif call.data == 'no':
        bot.send_message(chat_id, "Спасибо.")
    bot.answer_callback_query(call.id)


@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    markup = types.InlineKeyboardMarkup()
    button_yes = types.InlineKeyboardButton(text="Да", callback_data='yes')
    button_no = types.InlineKeyboardButton(text="Нет", callback_data='no')
    markup.add(button_yes, button_no)
    phone_number = message.contact.phone_number
    chat_id = message.chat.id
    error = save(phone_number, chat_id)
    if error:
        if 'chat_id' in error:
            bot.send_message(message.chat.id, f"Вы уже зарегестрированы", reply_markup=types.ReplyKeyboardRemove())
            return
        if 'phone' in error:
            user_data[chat_id] = phone_number
            bot.send_message(message.chat.id, f"Номер: {phone_number}, уже есть в базе. Хотите обновить информацию?")
            bot.send_message(message.chat.id, 'Хотите обновить онформацию?', reply_markup=markup)
            return
    bot.send_message(message.chat.id, f"Ваш номер телефона: {phone_number}")


@bot.message_handler(regexp=r'^\+\d{12}$')
def handle_manual_number(message):
    markup = types.InlineKeyboardMarkup()
    button_yes = types.InlineKeyboardButton(text="Да", callback_data='yes')
    button_no = types.InlineKeyboardButton(text="Нет", callback_data='no')
    markup.add(button_yes, button_no)
    phone_number = message.text
    chat_id = message.chat.id
    error = save(phone_number, chat_id)
    if error:
        if 'chat_id' in error:
            bot.send_message(message.chat.id, f"Вы уже зарегестрированы")
            return
        if 'phone' in error:
            user_data[chat_id] = phone_number
            bot.send_message(message.chat.id, f"Номер: {phone_number}, уже есть в базе. Хотите обновить информацию?")
            bot.send_message(message.chat.id, 'Хотите обновить онформацию?', reply_markup=markup)
            return
    bot.send_message(message.chat.id, f"Ваш номер телефона: {phone_number}")


@bot.message_handler(commands=['cups'])
def cups(message):
    phone = get_phone(message.chat.id)
    bot.send_message(message.chat.id, f'Увас осталось {to_present(phone )} кружек до бесплатной')


@bot.message_handler(func=lambda message: True, content_types=['text'])
def echo_message(message):
    bot.send_message(message.chat.id, message.text)


@app.route(f'/{TOKEN}', methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200


@app.route('/')
def index():
    bot.remove_webhook()
    bot.set_webhook(url=URL)
    return 'OK', 200


if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=URL)
    app.run(debug=DEBUG_SWITCH)

