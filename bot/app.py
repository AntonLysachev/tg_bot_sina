import os
from flask import Flask, request
import telebot
from dotenv import load_dotenv
import logging
import requests
from bot.CRUD.crud_utils import save, get_phone

load_dotenv()
TOKEN_POSTER=os.getenv('TOKEN_POSTER')
URL_POSTER=os.getenv('URL_POSTER')
TOKEN = os.getenv('TOKEN')
URL = os.getenv('URL')
DEBUG_SWITCH = os.getenv('DEBUG_SWITCH')

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)
logger = telebot.logger
logger.setLevel(logging.DEBUG)


def to_present(phone):
    count = 0
    client_id = get_client_id(phone)
    response = requests.get(f'https://joinposter.com/api/clients.getClient?format=json&token=394478:04986675b4f2df00cf1d6b257085f8e4&client_id={client_id}')
    accumulation_products = response.json()['response'][0]['accumulation_products']
    prize_products = response.json()['response'][0]['prize_products']
    if prize_products:
        return count
    if accumulation_products:
        for cup in accumulation_products['4']['products']:
            count += cup['count']
        return count
    return 4

def get_client_id(phone):
    response = requests.get(f'https://joinposter.com/api/clients.getClients?format=json&token=394478:04986675b4f2df00cf1d6b257085f8e4&phone={phone}')
    return response.json()['response'][0]['client_id']


@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button_phone = telebot.types.KeyboardButton(text="Отправить номер телефона", request_contact=True)
    button_manual = telebot.types.KeyboardButton(text="Ввести номер вручную")
    markup.add(button_phone, button_manual)
    bot.send_message(message.chat.id, "Оставьте ваш контактный номер, чтобы наш менеджер смог связаться с вами.", reply_markup=markup)


@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    phone_number = message.contact.phone_number
    bot.send_message(message.chat.id, f"Спасибо! Ваш номер телефона: {phone_number}")


@bot.message_handler(func=lambda message: message.text == "Ввести номер вручную")
def handle_manual_input(message):
    bot.send_message(message.chat.id, "Введите номер телефона в формате +998123456789")


@bot.message_handler(regexp=r'^\+\d{12}$')
def handle_manual_number(message):
    phone_number = message.text
    chat_id = message.chat.id
    save(phone_number, chat_id)
    bot.send_message(message.chat.id, f"Спасибо! Ваш номер телефона: {phone_number}")


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
    update = telebot.types.Update.de_json(json_string)
    print(update)
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

