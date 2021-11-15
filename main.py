import telebot
import models
import config
import pickle
import json
import time
import requests
import forms
import os
import random
from datetime import datetime, timedelta
from tool import language_check, log, create_inlineKeyboard, create_markup
from app import bot, tbf, fsm, db, app
from flask import request










@bot.message_handler(commands=['off_coin'])
@log
def off_coin(message):
	if message.from_user.id in config.mod:
		fsm.set_state(message.from_user.id, "enter_coins")
		bot.send_message(message.from_user.id, language_check()["mod"]["enter_coins"])


@bot.message_handler(func=lambda message: True and fsm.get_state(message.from_user.id)[0] == "enter_coins")
@log
def accept_coins(message):
	text = language_check()
	tmp = fsm.get_state(message.from_user.id)
	bot.send_message(message.from_user.id, text["mod"]["enter_id"])	
	fsm.set_state(message.from_user.id, "enter_id", coins=message.text)


@bot.message_handler(func=lambda message: True and fsm.get_state(message.from_user.id)[0] == "enter_id")
@log
def accept_id(message):
	try:
		int(message.text)
	except:
		return
	text = language_check()
	tmp = fsm.get_state(message.from_user.id)
	user = models.BotUser.query.filter_by(user_id=message.text).first()
	if user == None:
		bot.send_message(message.from_user.id, text["mod"]["no_user"])
	else:
		bot.send_message(message.from_user.id, text["mod"]["info"].format(message.text, user.name, user.surname), reply_markup=create_inlineKeyboard({"Зачислить":f"give_coins {message.text} {tmp[1]['coins']}"}))


@bot.callback_query_handler(func=lambda call: True and call.data.split(" ")[0] == "give_coins")
@log
def accept_coins(call):
	bot.delete_message(call.from_user.id, call.message.message_id)
	text = language_check()
	user = models.BotUser.query.filter_by(user_id=int(call.data.split(" ")[1])).first()
	mod = models.BotUser.query.filter_by(user_id=call.from_user.id).first()
	bot.send_message(call.from_user.id, text["mod"]["success"].format(call.data.split(" ")[1], call.data.split(" ")[2]))
	user.coins = user.coins + int(call.data.split(" ")[2])
	bot.send_message(user.user_id, text["functions"]["get"].format(call.data.split(" ")[2]))
	db.session.commit()
	fsm.reset_state(call.from_user.id)






"""

bot.remove_webhook()
if __name__ == '__main__':
	bot.polling(none_stop=True)


"""

@app.route('/' + config.TOKEN, methods=['POST'])
def getMessage():
  bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
  return "!", 200


@app.route("/")
def webhook():
  bot.remove_webhook()
  bot.set_webhook(url=config.HEROKU_LINK + config.TOKEN)
  return "!", 200


# Получаем новые сообщения
if __name__ == "__main__":
  app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000))) 
  print("START")



# template #
'''
content_types=['video', 'document', 'audio', 'voice', 'photo', 'text'], 

with open(f"./photos/{}","rb") as file:
	file = file.read()
bot.send_video'message'from_user'id, file)

@bot.message_handler(func=lambda message: True and)
@log
def message_handler(message):


@bot.callback_query_handler(func=lambda call: True and)
@log
def callback_handler(call):
'''
