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



global quiz_status
quiz_status = True





# ------ Викторина ------ #
# выдача
@bot.message_handler(func=lambda message: True and message.text in [language_check()["quiz"]["start_quiz"], language_check()["quiz"]["next_question"]])
@log
def quiz_send(message):
	if quiz_status == True:
		active_lots = models.Auc.query.filter_by(status="active").all()
		if len(active_lots) == 0:
			if message.text == language_check()["quiz"]["start_quiz"]:
				all_quiz = [i.id for i in models.Quiz.query.all()]
				user_complete_quiz = [i.quiz_id for i in models.CompleteQuiz.query.filter_by(user_id=message.from_user.id).all()]
				for i in all_quiz:
					if i not in user_complete_quiz:
						text = language_check()
						user = models.BotUser.query.filter_by(user_id=message.from_user.id).first()
						bot.send_message(message.from_user.id, text["quiz"]["third_message"], reply_markup=create_markup(text["quiz"]["next_question"]))
						return
				bot.send_message(message.from_user.id, language_check()["quiz"]["finish"])
			else:
				quiz = []
				all_quiz = models.Quiz.query.all()
				user_complete_quiz = models.CompleteQuiz.query.filter_by(user_id=message.from_user.id).all()
				# Убираем пройденые викторины и сортируем список
				complete_quiz = [i.quiz_id for i in user_complete_quiz]
				for i in all_quiz:
					if i.id in complete_quiz:
						continue
					quiz.append(i)

				if len(quiz) != 0:
					# -- Выдача случайного вопроса -- #
					quiz = random.choice(quiz)
						
					  # генерация главиатуры для викторины #
					quiz_buttons = [i for i in pickle.loads(quiz.false)]
					quiz_buttons.append(quiz.answer)
					quiz_button = random.shuffle(quiz_buttons)
					quiz_keyboard = {}
					for i in range(len(quiz_buttons)):
						quiz_keyboard[quiz_buttons[i]] = f"answer_quiz {quiz.id} {i}"

						
					  # Отправка #
					if quiz.quiz_type == "text":
						bot.send_message(message.from_user.id, quiz.question, reply_markup=create_inlineKeyboard(quiz_keyboard, 2))
					elif quiz.quiz_type == "photo":
						bot.send_photo(message.from_user.id, quiz.quiz_media_id, caption=quiz.question, reply_markup=create_inlineKeyboard(quiz_keyboard, 2))
					elif quiz.quiz_type == "video":
						bot.send_video(message.from_user.id, quiz.quiz_media_id, caption=quiz.question, reply_markup=create_inlineKeyboard(quiz_keyboard, 2))
					elif quiz.quiz_type == "audio":
						bot.send_audio(message.from_user.id, quiz.quiz_media_id, caption=quiz.question, reply_markup=create_inlineKeyboard(quiz_keyboard, 2))
				else:
					count = 0
					for i in user_complete_quiz:
						if i.status == "win":
							count += int(i.cost)

					text = language_check()
					bot.send_message(message.from_user.id, text["quiz"]["end"])
					bot.send_message(message.from_user.id, text["quiz"]["count"].format(count), reply_markup=create_markup(text["quiz"]["start_quiz"]))
					user = models.BotUser.query.filter_by(user_id=message.from_user.id)
					if user.coins < count + 10:
						user.coins = count + 10
						db.session.commit()
					return



# Обработка ответа
@bot.callback_query_handler(func=lambda call: True and call.data.split(" ")[0] == "answer_quiz")
@log
def quiz_accept_answer(call):
	try:
		bot.delete_message(call.from_user.id, call.message.message_id)
		answer_status = models.CompleteQuiz.query.filter_by(quiz_id=call.data.split(" ")[1], user_id=call.from_user.id).first()
		# Проверка не проходил ли раньше пользователь этот вопрос
		if answer_status == None:
			quiz = models.Quiz.query.filter_by(id=call.data.split(" ")[1]).first()
			user = models.BotUser.query.filter_by(user_id=call.from_user.id).first()
			text = language_check()
			# Получаем ответ
			for i in call.message.json["reply_markup"]["inline_keyboard"]:
				for x in i:
					if x["callback_data"] == call.data:
						answer = x["text"]
						break
			
			# Выдаём результат
			if answer == quiz.answer:
				user.coins = user.coins + quiz.cost
				db.session.commit()
				bot.send_message(call.from_user.id, random.choice(text["quiz"]["correct_answers"]).format(quiz.cost), reply_markup=create_markup(text["quiz"]["next_question"]))
				time.sleep(0.03)
				db.session.add(models.CompleteQuiz(quiz_id=quiz.id, user_id=call.from_user.id, status="win", cost=quiz.cost))
				if random.randint(1, 10) == 5:
					bot.send_message(config.quiz_group_id, text["logs"]["answer"].format(f"{user.surname} {user.name}", quiz.id, quiz.cost))
					time.sleep(0.03)
			else:
				bot.send_message(call.from_user.id, text["quiz"]["incorrect_answer"], reply_markup=create_markup(text["quiz"]["next_question"]))
				db.session.add(models.CompleteQuiz(quiz_id=quiz.id, user_id=call.from_user.id, status="lose", cost=quiz.cost))

			db.session.commit()
	except Exception as e:
		print(e)




# ------ Команды ------ #
@bot.message_handler(commands=['my_wallet'])
def my_wallet(message):
	user = models.BotUser.query.filter_by(user_id=message.from_user.id).first()
	bot.send_message(message.from_user.id, language_check()["functions"]["wallet"].format(user.coins))



@bot.message_handler(commands=['my_id'])
def my_id(message):
	bot.send_message(message.from_user.id, language_check()["functions"]["id"].format(message.from_user.id))


@bot.message_handler(commands=['support'])
def support(message):
	keyboard = telebot.types.InlineKeyboardMarkup()
	url_button = telebot.types.InlineKeyboardButton(text="Оператор 1", url="https://t.me/moderator_free")
	url_button1 = telebot.types.InlineKeyboardButton(text="Оператор 2", url="https://t.me/moderator_freedom")
	keyboard.add(url_button, url_button1)
	bot.send_message(message.from_user.id, language_check()["functions"]["support"], reply_markup=keyboard)


@bot.message_handler(commands=['upload_video'])
def upload_video(message):
	bot.send_message(message.from_user.id, language_check()["functions"]["upload"])
	fsm.set_state(message.from_user.id, "upload_video")


@bot.message_handler(content_types=["video"], func=lambda message: True and fsm.get_state(message.from_user.id)[0] == "upload_video")
def get_video(message):
	bot.send_message(message.from_user.id, language_check()["functions"]["accepted"])
	for i in config.mod:
		bot.send_video(i, message.video.file_id)


# ------ Ставки ------ #
@bot.message_handler(func=lambda message: True and (message.text == language_check()["bet"]["bet"] or message.text == "/bid"))
def bet(message):
	try:
		active_lot = models.ActiveLot.query.first()
		text = language_check()
		if active_lot == None:
			bot.send_message(message.from_user.id, text["bet"]["no"])
			return
		
		user = models.BotUser.query.filter_by(user_id=message.from_user.id).first()
		if active_lot.bet_date + timedelta(seconds=10) > datetime.now() and active_lot.winner_id == message.from_user.id:
			bot.send_message(message.from_user.id, text["bet"]["delay"])
			
		else:
			if active_lot.cost + 10 > user.coins:
				bot.send_message(message.from_user.id, text["bet"]["not_enough"])
				return
			else:
				active_lot.winner_id = message.from_user.id
				active_lot.cost = active_lot.cost + 10
				active_lot.bet_date = datetime.now()
				lot = models.Auc.query.filter_by(id=active_lot.lot_id).first()
				bot.send_message(message.from_user.id, text["bet"]["accept"])
				bot.send_message(config.auc_group_id, text["logs"]["auc"].format(f"{user.surname} {user.name}", active_lot.cost, lot.name))
				player = models.Players.query.filter_by(user_id=message.from_user.id, lot_id=active_lot.lot_id).first()
				if player == None:
					db.session.add(models.Players(lot_id=active_lot.lot_id, user_id=message.from_user.id, cost=active_lot.cost))
				else:
					player.cost = active_lot.cost
				db.session.commit()

		db.session.commit()
	except Exception as e:
		print(e)


@bot.message_handler(func=lambda message: True and message.text in ['/start_quiz', "/stop_quiz"])
def quiz_statuss(message):
	global quiz_status
	if message.from_user.id in config.admin:
		users = models.BotUser.query.all()
		if message.text == "/start_quiz":
			quiz_status = True
			for i in users:
				try:
					bot.send_message(i.user_id, language_check()["quiz"]["start"], reply_markup=create_markup(language_check()["quiz"]["start_quiz"]))
					time.sleep(0.03)
				except Exception as e:
					print(e)
		elif message.text == "/stop_quiz":
			quiz_status = False
			text = language_check()
			for i in users:
				try:
					bot.send_sticker(i.user_id, "CAACAgIAAxkBAAIFdWGMDiEV6Y9SDC3lRcYbDmD3ZsxUAAJ5EQACbaNZSMtrjsQSTZFfIgQ")
					bot.send_message(i.user_id, text["quiz"]["end_"].format(i.coins), reply_markup=telebot.types.ReplyKeyboardRemove())
					time.sleep(0.03)
					bot.send_message(i.user_id, text["quiz"]["end_1"])
					time.sleep(0.03)
				except Exception as e:
					print(e)



		
		


@bot.message_handler(commands=['start'])
def start(message):
	try:
		fsm.reset_state(message.from_user.id)
		text = language_check()
		if models.BotUser.query.filter_by(user_id=message.from_user.id).first() != None:
			bot.send_message(message.from_user.id, text["hi_again"], reply_markup=create_markup(text["quiz"]["start_quiz"]))
		#	bot.send_message(message.from_user.id, text["hi_again"])
		else:
			bot.send_sticker(message.from_user.id, "CAACAgIAAxkBAAIFb2GMDYddnS6cDjqGoR5O2TDV4guTAAKbFQACLJxhSPmAdDVYBxbQIgQ")
			fsm.set_state(message.from_user.id, "enter_name")
			bot.send_message(message.from_user.id, text["register"]["first"])
			bot.send_message(message.from_user.id, text["register"]["enter_name"])
	except Exception as e:
		print(e)


# ------ Регистрация ------ #

@bot.message_handler(func=lambda message: True and fsm.get_state(message.from_user.id)[0] == "enter_name")
@log
def accept_name(message):
	text = language_check()
	bot.send_message(message.from_user.id, text["register"]["enter_surname"])	
	fsm.set_state(message.from_user.id, "enter_surname", name=message.text)


@bot.message_handler(func=lambda message: True and fsm.get_state(message.from_user.id)[0] == "enter_surname")
@log
def accept_surname(message):
	tmp = fsm.get_state(message.from_user.id)
	text = language_check()
	bot.send_message(message.from_user.id, text["register"]["enter_fil_name"], reply_markup=create_markup(text["register"]["fil_name"], 2))	
	fsm.set_state(message.from_user.id, "enter_fil_name", name=tmp[1]["name"], surname=message.text)


@bot.message_handler(func=lambda message: True and fsm.get_state(message.from_user.id)[0] == "enter_fil_name")
@log
def accept_fil_surname(message):
	text = language_check()
	if message.text not in text["register"]["fil_name"]:
		return
	tmp = fsm.get_state(message.from_user.id)
	bot.send_message(message.from_user.id, text["register"]["enter_rank"], reply_markup=telebot.types.ReplyKeyboardRemove())	
	fsm.set_state(message.from_user.id, "enter_rank", name=tmp[1]["name"], surname=tmp[1]["surname"], fil_name=message.text)


@bot.message_handler(func=lambda message: True and fsm.get_state(message.from_user.id)[0] == "enter_rank")
@log
def accept_rank(message):
	tmp = fsm.get_state(message.from_user.id)
	text = language_check()
	bot.send_message(message.from_user.id, text["register"]["enter_mail"])	
	fsm.set_state(message.from_user.id, "enter_mail", name=tmp[1]["name"], surname=tmp[1]["surname"], fil_name=tmp[1]["fil_name"], rank=message.text)



@bot.message_handler(func=lambda message: True and fsm.get_state(message.from_user.id)[0] == "enter_mail")
@log
def accept_mail(message):
	tmp = fsm.get_state(message.from_user.id)
	text = language_check()

#	if message.text.lower() not in [i.mail.lower() for i in models.Email.query.all()]:
#		bot.send_sticker(message.from_user.id, "CAACAgIAAxkBAAIFcWGMDcKKAvfcx697mQObB5vhU6KSAAIYEQACTDBhSKedF-uBP0JrIgQ")
#		bot.send_message(message.from_user.id, text["register"]["non_mail"])	
#		bot.send_message(message.from_user.id, text["register"]["non_mail1"])
#		bot.send_message(message.from_user.id, text["register"]["non_mail2"])
#		return 


	db.session.add(models.BotUser(user_id=message.from_user.id, surname=tmp[1]["surname"], name=tmp[1]["name"], rank=tmp[1]["rank"], fil_name=tmp[1]["fil_name"], mail=message.text.lower(), coins=10))
	db.session.commit()
	bot.send_sticker(message.from_user.id, "CAACAgIAAxkBAAIFc2GMDgAB3zqME8BnshYFgiqXiZqgWwACcREAAkWIYUglPsZ0uJ5pPSIE")
	bot.send_message(message.from_user.id, text["register"]["first_message"].format(tmp[1]["name"], tmp[1]["fil_name"]))
	bot.send_message(message.from_user.id, text["register"]["second_message"])
	#bot.send_message(message.from_user.id, text["register"]["third_message"])
	bot.send_message(message.from_user.id, text["register"]["third_message"], reply_markup=create_markup(text["quiz"]["start_quiz"]))
	fsm.reset_state(message.from_user.id)



	
		
		
		
		
		
		
		
		
		
		
		
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