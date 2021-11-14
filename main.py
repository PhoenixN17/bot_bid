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

print(-1)
global quiz_status
quiz_status = True

# ------ Админ панель ------ #
@bot.message_handler(commands=['apanel'])
def apanel(message):
	try:
		if message.from_user.id in config.admin:
			bot.send_message(message.from_user.id, "Админ панель", reply_markup=create_inlineKeyboard(language_check()["apanel"]["buttons"], 2))
	except Exception as e:
		print(e)


# Удаление вопроса
@bot.callback_query_handler(func=lambda call: True and call.data == "delete_question")
@log
def apanel_delete_question(call):
	try:
		bot.delete_message(call.from_user.id, call.message.message_id)
		bot.send_message(call.from_user.id, language_check()["apanel"]["delete_question"]["enter_id"])
		fsm.set_state(call.from_user.id, "delete_question_id")
	except Exception as e:
		print(e)



@bot.message_handler(func=lambda message: True and fsm.get_state(message.from_user.id)[0] == "delete_question_id")
@log
def apanel_accept_delete_question(message):
	try:
		text = language_check()
		try:
			int(message.text)
		except:
			return
		question = models.Quiz.query.filter_by(id=int(message.text)).first()
		if question == None:
			pass
		else:
			db.session.delete(question)
			db.session.commit()
		bot.send_message(message.from_user.id, "Админ панель", reply_markup=create_inlineKeyboard(language_check()["apanel"]["buttons"], 2))
	except Exception as e:
		print(e)



# Удаление лота
@bot.callback_query_handler(func=lambda call: True and call.data == "delete_lot")
@log
def apanel_delete_question(call):
	try:
		bot.delete_message(call.from_user.id, call.message.message_id)
		lots = models.Auc.query.filter_by(status="inactive").all()
		text = language_check()
		if len(lots) == 0:
			bot.send_message(call.from_user.id, text["apanel"]["end_lot"]["no_lots"], reply_markup=create_inlineKeyboard(text["apanel"]["buttons"], 2))
			return 

		lots_buttons = {}
		for i in lots:
			lots_buttons[f"{i.name}({i.cost})"] = f"delete_lot {i.id}"

		bot.send_message(call.from_user.id, text["apanel"]["delete_lot"]["chose_lot"], reply_markup=create_inlineKeyboard(lots_buttons, 2))
	except Exception as e:
		print(e)



@bot.callback_query_handler(func=lambda call: True and call.data.split(" ")[0] == "delete_lot")
@log
def apanel_delete_question(call):
	try:
		lot = models.Auc.query.filter_by(id=call.data.split(" ")[1]).first()
		text = language_check()
		db.session.delete(lot)
		db.session.commit()
		bot.send_message(call.from_user.id, text["apanel"]["delete_lot"]["deleted"], reply_markup=create_inlineKeyboard(text["apanel"]["buttons"], 2))
	except Exception as e:
		print(e)

		





# Добавление вопроса
@bot.callback_query_handler(func=lambda call: True and call.data == "add_question")
@log
def apanel_add_question(call):
	tbf.send_form(call.from_user.id, forms.Question(language_check()))


@tbf.form_event("add_question", action=["submit"])
def apanel_accept_question(call,form_data):
	try:
		text = language_check()
		if form_data.media:
			media_type = form_data.media.media_type	
			file_id = form_data.media.file_id
		else:
			media_type = "text"
			file_id = "text"

		quiz = models.Quiz(quiz_type=media_type, quiz_media_id=file_id, question=form_data.question, answer=form_data.answer, false=pickle.dumps(form_data.false.split("#")), cost=int(form_data.cost))
		db.session.add(quiz)
		db.session.commit()
		quiz = models.Quiz.query.filter_by(quiz_type=media_type, quiz_media_id=file_id, question=form_data.question, answer=form_data.answer).first()
		print(quiz)
		
		bot.send_message(call.from_user.id, text["apanel"]["add_question"]["question_id"].format(str(quiz.id)))
		bot.send_message(call.from_user.id, text["apanel"]["add_question"]["added"], reply_markup=create_inlineKeyboard(text["apanel"]["buttons"], 2))
	except Exception as e:
		print(e)




# Снятие слота
@bot.callback_query_handler(func=lambda call: True and call.data == "end_lot")
@log
def apanel_end_lot(call):
	try:
		lots = models.Auc.query.filter_by(status="active").all()
		bot.delete_message(call.from_user.id, call.message.message_id)
		text = language_check()
		if len(lots) == 0:
			bot.send_message(call.from_user.id, text["apanel"]["end_lot"]["no_lots"], reply_markup=create_inlineKeyboard(text["apanel"]["buttons"], 2))
			return 

		lots_buttons = {}
		for i in lots:
			lots_buttons[f"{i.name}({i.cost})"] = f"end_lot {i.id}"

		bot.send_message(call.from_user.id, text["apanel"]["end_lot"]["to_end"], reply_markup=create_inlineKeyboard(lots_buttons, 2))
	except Exception as e:
		print(e)



@bot.callback_query_handler(func=lambda call: True and call.data.split(" ")[0] == "end_lot")
@log
def apanel_end_lot_accept(call):
	try:
		bot.delete_message(call.from_user.id, call.message.message_id)
		lot = db.session.query(models.Auc, models.ActiveLot).filter(models.Auc.id==call.data.split(" ")[1], models.ActiveLot.lot_id==models.Auc.id).all()
		Players = models.Players.query.filter_by(lot_id=lot[0][0].id)
		# Проверка есть ли победитель у лота
		if lot[0][1].winner_id != None:
			user = models.BotUser.query.filter_by(user_id=lot[0][1].winner_id).first()
			user.coins = user.coins - lot[0][1].cost
		else:
			pass
		db.session.commit()
		# выдача победителю и програвшим
		text = language_check()
		for i in Players:
			try:
				if i.user_id == lot[0][1].winner_id:
					player = models.BotUser.query.filter_by(user_id=i.user_id).first()
					bot.send_message(i.user_id, text["bet"]["congratulation"].format(lot[0][0].name, lot[0][1].cost))
					bot.send_message(i.user_id, text["bet"]["to_get"])
					bot.send_message(config.group_id, text["logs"]["win"].format(f"{player.surname} {player.name}", lot[0][0].name, lot[0][1].cost))
				else:
					bot.send_message(i.user_id, text["bet"]["sorry"])
				time.sleep(0.04)

				db.session.delete(i)
			except Exception as e:
				print(e)
		
		lot[0][0].status = "inactive"
		db.session.delete(lot[0][1])


		db.session.commit()
		bot.send_message(call.from_user.id, text["apanel"]["end_lot"]["successfully"], reply_markup=create_inlineKeyboard(text["apanel"]["buttons"], 2))

		# Сообщение о новом лоте
		active_lots = models.ActiveLot.query.all()
		if len(active_lots) != 0:
			for i in models.BotUser.query.all():
				bot.send_message(i.user_id, text["apanel"]["chose_lot"]["new_lot"].format(lot[0].cost))
		else:
			for i in models.BotUser.query.all():
				try:
				#	bot.send_message(i.user_id, text["bet"]["end"], reply_markup=create_markup(text["quiz"]["start_quiz"]))
					bot.send_message(i.user_id, text["bet"]["end"])
					time.sleep(0.03)
				except Exception as e:
					print(e)
	except Exception as e:
		print(e)



	

# Создание слота
@bot.callback_query_handler(func=lambda call: True and call.data == "create_lot")
@log
def apanel_create_lot(call):
	try:
		bot.delete_message(call.from_user.id, call.message.message_id)
		text = language_check()
		bot.send_message(call.from_user.id, text["apanel"]["create_lot"]["send_pic"])
		fsm.set_state(call.from_user.id, "create_lot_pic")
	except Exception as e:
		print(e)



@bot.message_handler(content_types=['photo'], func=lambda message: True and fsm.get_state(message.from_user.id)[0] == "create_lot_pic")
@log
def apanel_lot_pic(message):
	try:
		tmp = fsm.get_state(message.from_user.id)
		text = language_check()
		bot.send_message(message.from_user.id, text["apanel"]["create_lot"]["enter_name"])	
		fsm.set_state(message.from_user.id, "create_lot_name", pic=message.photo[0].file_id)
	except Exception as e:
		print(e)



@bot.message_handler(func=lambda message: True and fsm.get_state(message.from_user.id)[0] == "create_lot_name")
@log
def apanel_lot_name(message):
	tmp = fsm.get_state(message.from_user.id)
	text = language_check()
	bot.send_message(message.from_user.id, text["apanel"]["create_lot"]["enter_shortname"])	
	fsm.set_state(message.from_user.id, "create_lot_shortname", pic=tmp[1]["pic"], name=message.text)


@bot.message_handler(func=lambda message: True and fsm.get_state(message.from_user.id)[0] == "create_lot_shortname")
@log
def apanel_lot_shortname(message):
	tmp = fsm.get_state(message.from_user.id)
	text = language_check()
	bot.send_message(message.from_user.id, text["apanel"]["create_lot"]["enter_disc"])	
	fsm.set_state(message.from_user.id, "create_lot_disc", pic=tmp[1]["pic"], name=tmp[1]["name"], shortname=message.text)


@bot.message_handler(func=lambda message: True and fsm.get_state(message.from_user.id)[0] == "create_lot_disc")
@log
def apanel_lot_disc(message):
	tmp = fsm.get_state(message.from_user.id)
	text = language_check()
	bot.send_message(message.from_user.id, text["apanel"]["create_lot"]["enter_cost"])	
	fsm.set_state(message.from_user.id, "create_lot_cost", pic=tmp[1]["pic"], name=tmp[1]["name"], shortname=tmp[1]["shortname"], disc=message.text)


@bot.message_handler(func=lambda message: True and fsm.get_state(message.from_user.id)[0] == "create_lot_cost")
@log
def apanel_lot_cost(message):
	try:
		text = language_check()
		try:
			int(message.text)
		except:
			bot.send_message(message.from_user.id, text["apanel"]["create_lot"]["invalid_value"])
			return
		tmp = fsm.get_state(message.from_user.id)

		lot = models.Auc(pic=tmp[1]["pic"], name=tmp[1]["name"], shortname=tmp[1]["shortname"], disc=tmp[1]["disc"], cost=message.text, status="inactive")
		db.session.add(lot)
		db.session.commit()
		fsm.reset_state(message.from_user.id)
		bot.send_message(message.from_user.id, text["apanel"]["create_lot"]["lot_id"].format(lot.id))
		bot.send_message(message.from_user.id, text["apanel"]["create_lot"]["created"], reply_markup=create_inlineKeyboard(text["apanel"]["buttons"], 2))
	except Exception as e:
		print(e)



# Выпуск лота
@bot.callback_query_handler(func=lambda call: True and call.data == "send_lot")
@log
def apanel_send_lot(call):
	try:
		lots = models.Auc.query.all()
		bot.delete_message(call.from_user.id, call.message.message_id)
		text = language_check()
		print(lots)
		if len(lots) == 0:
			bot.send_message(call.from_user.id, text["apanel"]["chose_lot"]["no_lots"], reply_markup=create_inlineKeyboard(text["apanel"]["buttons"], 2))
			return 

		lots_buttons = {}
		for i in lots:
			if i.status == "inactive":
				lots_buttons[i.name] = f"chose_lot {i.id}"

		bot.send_message(call.from_user.id, text["apanel"]["chose_lot"]["to_send"], reply_markup=create_inlineKeyboard(lots_buttons, 2))
	except Exception as e:
		print(e)

		

@bot.callback_query_handler(func=lambda call: True and call.data.split(" ")[0] == "chose_lot")
@log
def apanel_accept_send(call):
	try:
		bot.delete_message(call.from_user.id, call.message.message_id)
		text = language_check()
		lot = models.Auc.query.filter_by(id=call.data.split(" ")[1]).first()
		lot.status = "active"
		active_lots = models.ActiveLot.query.all()
		if len(active_lots) == 0:
			users = models.BotUser.query.all()
			for i in users:
				try:
					bot.send_message(i.user_id, text["apanel"]["chose_lot"]["message_four"].format(i.coins))
					time.sleep(0.03)
					bot.send_message(i.user_id, text["apanel"]["chose_lot"]["new_lot"].format(lot.cost), reply_markup=create_markup(text["bet"]["bet"]))
					time.sleep(0.03)
					bot.send_photo(i.user_id, lot.pic, lot.disc)
					time.sleep(0.03)
				except Exception as e:
					print(e, i)
					continue
		db.session.add(models.ActiveLot(lot_id=lot.id, cost=lot.cost))
		db.session.commit()
		
		bot.send_message(call.from_user.id, text["apanel"]["chose_lot"]["sended_lot"], reply_markup=create_inlineKeyboard(text["apanel"]["buttons"], 2))
	except Exception as e:
		print(e)


#-- Цепочки --№
@bot.callback_query_handler(func=lambda call: True and call.data.split(" ")[0] == "view_chain_menu")
@log
def apanel_view_chain(call):
	text = language_check()
	bot.delete_message(call.from_user.id, call.message.message_id)
	bot.send_message(call.from_user.id, text["apanel"]["chain"]["menu"], reply_markup=create_inlineKeyboard(text["apanel"]["chain"]["buttons"], 2))


# Создание цепочик
@bot.callback_query_handler(func=lambda call: True and call.data.split(" ")[0] == "create_chain")
@log
def apanel_create_chain(call):
	text = language_check()
	bot.delete_message(call.from_user.id, call.message.message_id)
	bot.send_message(call.from_user.id, text["apanel"]["chain"]["send_name"])
	fsm.set_state(call.from_user.id, "enter_chain_name")


@bot.message_handler(func=lambda message: True and fsm.get_state(message.from_user.id)[0] == "enter_chain_name")
@log
def accept_chain_name(message):
	text = language_check()
	bot.send_message(message.from_user.id, text["apanel"]["chain"]["send_message"])
	fsm.set_state(message.from_user.id, "chain_send_message", name=message.text, args=[])




@bot.message_handler(content_types=['video', 'photo', 'text'], func=lambda message: True and fsm.get_state(message.from_user.id)[0] == "chain_send_message")
@log
def accept_chain_message(message):
	text = language_check()
	tmp = fsm.get_state(message.from_user.id)
	if message.text == text["apanel"]["chain"]["stop"]:
		db.session.add(models.Chain(name=tmp[1]["name"], parts=pickle.dumps(tmp[1]["args"])))
		db.session.commit()
		bot.send_message(message.from_user.id, text["apanel"]["chain"]["chain_created"], reply_markup=telebot.types.ReplyKeyboardRemove())
		fsm.reset_state(message.from_user.id)
		return

	if message.content_type == "photo":
		tmp[1]["args"].append(["photo", message.photo[0].file_id, message.caption])
	elif message.content_type == "text":
		tmp[1]["args"].append(["text", "text", message.text])
	elif message.content_type == "video":
		tmp[1]["args"].append(["video", message.video.file_id, message.caption])

	bot.send_message(message.from_user.id, text["apanel"]["chain"]["press_stp"], reply_markup=create_markup(text["apanel"]["chain"]["stop"]))


	fsm.set_state(message.from_user.id, "chain_send_message", name=tmp[1]["name"], args=tmp[1]["args"])


# Отправка цепочки
@bot.callback_query_handler(func=lambda call: True and call.data == "send_chain")
@log
def apanel_send_chain(call):
	chains = models.Chain.query.all()
	bot.delete_message(call.from_user.id, call.message.message_id)
	text = language_check()
	if len(chains) == 0:
		bot.send_message(call.from_user.id, text["apanel"]["chain"]["no_chains"], reply_markup=create_inlineKeyboard(text["apanel"]["chain"]["buttons"], 2))
		return 

	chains_buttons = {}
	for i in chains:
		chains_buttons[i.name] = f"send_chain {i.id}"

	bot.send_message(call.from_user.id, text["apanel"]["chain"]["to_send"], reply_markup=create_inlineKeyboard(chains_buttons, 2))


@bot.callback_query_handler(func=lambda call: True and call.data.split(" ")[0] == "send_chain")
@log
def apanel_send_chain(call):
	bot.delete_message(call.from_user.id, call.message.message_id)
	chain = models.Chain.query.filter_by(id=call.data.split(" ")[1]).first()
	parts = pickle.loads(chain.parts)
	for user in models.BotUser.query.all():
		try:
			for i in parts:
				print(i)
				if i[0] == "photo":
					bot.send_photo(user.user_id, i[1], caption=i[2])
				elif i[0] == "video":
					bot.send_video(user.user_id, i[1], caption=i[2])
				elif i[0] == "text":
					bot.send_message(user.user_id, i[2])
		except Exception as e:
			print(e)
	bot.send_message(call.from_user.id, language_check()["apanel"]["chain"]["sended"])



# Удаление цепочки
@bot.callback_query_handler(func=lambda call: True and call.data == "del_chain")
@log
def apanel_del_chain(call):
	chains = models.Chain.query.all()
	bot.delete_message(call.from_user.id, call.message.message_id)
	text = language_check()
	if len(chains) == 0:
		bot.send_message(call.from_user.id, text["apanel"]["chain"]["no_chains"], reply_markup=create_inlineKeyboard(text["apanel"]["chain"]["buttons"], 2))
		return 

	chains_buttons = {}
	for i in chains:
		chains_buttons[i.name] = f"del_chain {i.id}"

	bot.send_message(call.from_user.id, text["apanel"]["chain"]["to_del"], reply_markup=create_inlineKeyboard(chains_buttons, 2))


@bot.callback_query_handler(func=lambda call: True and call.data.split(" ")[0] == "del_chain")
@log
def apanel_del_chain(call):
	bot.delete_message(call.from_user.id, call.message.message_id)
	chain = models.Chain.query.filter_by(id=call.data.split(" ")[1]).first()
	db.session.delete(chain)
	db.session.commit()
	bot.send_message(call.from_user.id, language_check()["apanel"]["chain"]["deleted"])





@bot.message_handler(commands=['start'])
def start(message):
	try:
		fsm.reset_state(message.from_user.id)
		text = language_check()
		if models.BotUser.query.filter_by(user_id=message.from_user.id).first() != None:
			#bot.send_message(message.from_user.id, text["hi_again"], reply_markup=create_markup(text["quiz"]["start_quiz"]))
			bot.send_message(message.from_user.id, text["hi_again"])
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
	bot.send_message(message.from_user.id, text["register"]["third_message"])
	#bot.send_message(message.from_user.id, text["register"]["third_message"], reply_markup=create_markup(text["quiz"]["start_quiz"]))
	fsm.reset_state(message.from_user.id)



# ------ Викторина ------ #
# выдача
@bot.message_handler(func=lambda message: True and message.text in [language_check()["quiz"]["start_quiz"], language_check()["quiz"]["next_question"]])
@log
def quiz_send(message):
	print(2, quiz_status)
	if quiz_status == True:
		active_lots = models.Auc.query.filter_by(status="active").all()
		print(active_lots)
		if len(active_lots) == 0:
			print(2.1)
			if message.text == language_check()["quiz"]["start_quiz"]:
				all_quiz = [i.id for i in models.Quiz.query.all()]
				user_complete_quiz = [i.quiz_id for i in models.CompleteQuiz.query.filter_by(user_id=message.from_user.id).all()]
				for i in all_quiz:
					if i not in user_complete_quiz:
						text = language_check()
						user = models.BotUser.query.filter_by(user_id=message.from_user.id).first()
						bot.send_message(message.from_user.id, text["quiz"]["third_message"], reply_markup=create_markup(text["quiz"]["next_question"]))
						break
			else:
				print(3)
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
				bot.send_message(call.from_user.id, random.choice(text["quiz"]["correct_answers"]).format(quiz.cost), reply_markup=create_markup(text["quiz"]["next_question"]))
				db.session.add(models.CompleteQuiz(quiz_id=quiz.id, user_id=call.from_user.id, status="win", cost=quiz.cost))
				bot.send_message(config.group_id, text["logs"]["answer"].format(f"{user.surname} {user.name}", quiz.id, quiz.cost))
				user.coins = user.coins + quiz.cost
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
				bot.send_message(message.from_user.id, text["bet"]["accept"])
				bot.send_message(config.group_id, text["logs"]["auc"].format(f"{user.surname} {user.name}", active_lot.cost, active_lot.lot_id))
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
	print(message)
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



# ------ Модератор ------ #
@bot.message_handler(commands=['off_coin'])
def off_coin(message):
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
	bot.send_message(config.group_id, text["logs"]["offline"].format(f"{mod.surname} {mod.name}", f"{user.surname} {user.name}", call.data.split(" ")[2]))
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
