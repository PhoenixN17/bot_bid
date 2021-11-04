import telebot
import models
import config
import pickle
import json
import time
import forms
import random
from datetime import datetime, timedelta
from tool import language_check, log, create_inlineKeyboard, create_markup
from app import bot, tbf, fsm, db

# f
#db.session.add(models.Email(mail="jerck@gmail.com"))
#
#db.session.commit()






# ------ Админ панель ------ #
@bot.message_handler(commands=['apanel'])
def apanel(message):
	if message.from_user.id in config.admin:
		bot.send_message(message.from_user.id, "Админ панель", reply_markup=create_inlineKeyboard(language_check()["apanel"]["buttons"], 2))



# Добавление вопроса
@bot.callback_query_handler(func=lambda call: True and call.data == "add_question")
@log
def apanel_add_question(call):
	tbf.send_form(call.from_user.id, forms.Question(language_check()))


@tbf.form_event("add_question", action=["submit"])
def apanel_accept_question(call,form_data):
	if form_data.media:
		media_type = form_data.media.media_type	
		file_id = form_data.media.file_id
	else:
		media_type = "text"
		file_id = "text"

	quiz = models.Quiz(quiz_type=media_type, quiz_media_id=file_id, question=form_data.question, answer=form_data.answer, false=pickle.dumps(form_data.false.split("#")), cost=int(form_data.cost))
	db.session.add(quiz)
	db.session.commit()

	bot.send_message(call.from_user.id, language_check()["apanel"]["add_question"]["added"], reply_markup=create_inlineKeyboard(language_check()["apanel"]["buttons"], 2))



# Снятие слота
@bot.callback_query_handler(func=lambda call: True and call.data == "end_lot")
@log
def apanel_end_lot(call):
	lots = models.Auc.query.filter_by(status="active").all()
	bot.delete_message(call.from_user.id, call.message.message_id)
	text = language_check()
	if len(lots) == 0:
		bot.send_message(call.from_user.id, text["apanel"]["end_lot"]["no_lots"], reply_markup=create_inlineKeyboard(text["apanel"]["buttons"], 2))
		return 

	lots_buttons = {}
	for i in lots:
		lots_buttons[i.name] = f"end_lot {i.id}"

	bot.send_message(call.from_user.id, text["apanel"]["end_lot"]["to_end"], reply_markup=create_inlineKeyboard(lots_buttons, 2))


@bot.callback_query_handler(func=lambda call: True and call.data.split(" ")[0] == "end_lot")
@log
def apanel_end_lot_accept(call):
	bot.delete_message(call.from_user.id, call.message.message_id)
	lot = db.session.query(models.Auc, models.ActiveLot).filter(models.Auc.id==call.data.split(" ")[1], models.ActiveLot.lot_id==models.Auc.id).all()
	Players = models.Players.query.filter_by(lot_id=lot[0][0].id)
	# Проверка есть ли победитель у лота
	if lot[0][1].winner_id != None:
		user = models.BotUser.query.filter_by(user_id=call.from_user.id).first()
		user.coins = user.coins - lot[0][1].cost
	else:
		pass

	# выдача победителю и програвшим
	text = language_check()
	for i in Players:
		if i.user_id == lot[0][1].winner_id:
			bot.send_message(i.user_id, text["bet"]["congratulation"].format(lot[0][0].name, lot[0][1].cost))
			bot.send_message(i.user_id, text["bet"]["to_get"])
		else:
			bot.send_message(i.user_id, text["bet"]["sorry"])

		db.session.delete(i)
	
	for i in lot[0]:
		db.session.delete(i)


	db.session.commit()
	bot.send_message(call.from_user.id, text["apanel"]["end_lot"]["successfully"], reply_markup=create_inlineKeyboard(text["apanel"]["buttons"], 2))

	# Сообщение о новом лоте
	active_lots = models.ActiveLot.query.all()
	if len(active_lots) != 0:
		for i in models.BotUser.query.all():
			bot.send_message(i.user_id, text["apanel"]["chose_lot"]["new_lot"].format(lot.cost))


	

# Создание слота
@bot.callback_query_handler(func=lambda call: True and call.data == "create_lot")
@log
def apanel_create_lot(call):
	bot.delete_message(call.from_user.id, call.message.message_id)
	text = language_check()
	bot.send_message(call.from_user.id, text["apanel"]["create_lot"]["send_pic"])
	fsm.set_state(call.from_user.id, "create_lot_pic")


@bot.message_handler(content_types=['photo'], func=lambda message: True and fsm.get_state(message.from_user.id)[0] == "create_lot_pic")
@log
def apanel_lot_pic(message):
	tmp = fsm.get_state(message.from_user.id)
	text = language_check()
	bot.send_message(message.from_user.id, text["apanel"]["create_lot"]["enter_name"])	
	fsm.set_state(message.from_user.id, "create_lot_name", pic=message.photo[0].file_id)


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
	text = language_check()
	try:
		int(message.text)
	except:
		bot.send_message(message.from_user.id, text["apanel"]["create_lot"]["invalid_value"])
	tmp = fsm.get_state(message.from_user.id)

	db.session.add(models.Auc(pic=tmp[1]["pic"], name=tmp[1]["name"], shortname=tmp[1]["shortname"], disc=tmp[1]["disc"], cost=message.text, status="inactive"))
	db.session.commit()
	fsm.reset_state(message.from_user.id)
	bot.send_message(message.from_user.id, text["apanel"]["create_lot"]["created"], reply_markup=create_inlineKeyboard(text["apanel"]["buttons"], 2))


# Выпуск лота
@bot.callback_query_handler(func=lambda call: True and call.data == "send_lot")
@log
def apanel_send_lot(call):
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
	

@bot.callback_query_handler(func=lambda call: True and call.data.split(" ")[0] == "chose_lot")
@log
def apanel_accept_send(call):
	bot.delete_message(call.from_user.id, call.message.message_id)
	text = language_check()
	lot = models.Auc.query.filter_by(id=call.data.split(" ")[1]).first()
	lot.status = "active"
	active_lots = models.ActiveLot.query.all()
	if len(active_lots) == 0:
		users = models.BotUser.query.all()
		for i in users:
			bot.send_message(i.user_id, text["apanel"]["chose_lot"]["message_one"])
			bot.send_message(i.user_id, text["apanel"]["chose_lot"]["message_two"])
			bot.send_message(i.user_id, text["apanel"]["chose_lot"]["message_three"])
			bot.send_message(i.user_id, text["apanel"]["chose_lot"]["message_four"].format(i.coins))
			bot.send_message(i.user_id, text["apanel"]["chose_lot"]["new_lot"].format(lot.cost))
			time.sleep(0.17)
	db.session.add(models.ActiveLot(lot_id=lot.id, cost=lot.cost))
	db.session.commit()
	
	bot.send_message(call.from_user.id, text["apanel"]["chose_lot"]["sended_lot"], reply_markup=create_inlineKeyboard(text["apanel"]["buttons"], 2))
	



@bot.message_handler(commands=['start'])
def start(message):
	fsm.reset_state(message.from_user.id)
	text = language_check()
	if models.BotUser.query.filter_by(user_id=message.from_user.id).first() != None:
		bot.send_message(message.from_user.id, text["hi_again"], reply_markup=create_markup(text["quiz"]["start_quiz"]))
	else:
		fsm.set_state(message.from_user.id, "enter_surname")
		bot.send_message(message.from_user.id, text["register"]["enter_surname"])



# ------ Регистрация ------ #

@bot.message_handler(func=lambda message: True and fsm.get_state(message.from_user.id)[0] == "enter_surname")
@log
def accept_surname(message):
	text = language_check()
	bot.send_message(message.from_user.id, text["register"]["enter_name"])	
	fsm.set_state(message.from_user.id, "enter_name", surname=message.text)


@bot.message_handler(func=lambda message: True and fsm.get_state(message.from_user.id)[0] == "enter_name")
@log
def accept_name(message):
	tmp = fsm.get_state(message.from_user.id)
	text = language_check()
	bot.send_message(message.from_user.id, text["register"]["enter_side"])	
	fsm.set_state(message.from_user.id, "enter_side", surname=tmp[1]["surname"], name=message.text)


@bot.message_handler(func=lambda message: True and fsm.get_state(message.from_user.id)[0] == "enter_side")
@log
def accept_side(message):
	tmp = fsm.get_state(message.from_user.id)
	text = language_check()
	bot.send_message(message.from_user.id, text["register"]["enter_rank"])	
	fsm.set_state(message.from_user.id, "enter_rank", surname=tmp[1]["surname"], name=tmp[1]["name"], side=message.text)


@bot.message_handler(func=lambda message: True and fsm.get_state(message.from_user.id)[0] == "enter_rank")
@log
def accept_rank(message):
	tmp = fsm.get_state(message.from_user.id)
	text = language_check()
	bot.send_message(message.from_user.id, text["register"]["enter_fil_name"])	
	fsm.set_state(message.from_user.id, "enter_fil_name", surname=tmp[1]["surname"], name=tmp[1]["name"], side=tmp[1]["side"], rank=message.text)


@bot.message_handler(func=lambda message: True and fsm.get_state(message.from_user.id)[0] == "enter_fil_name")
@log
def accept_fil_name(message):
	tmp = fsm.get_state(message.from_user.id)
	text = language_check()
	bot.send_message(message.from_user.id, text["register"]["enter_mail"])	
	fsm.set_state(message.from_user.id, "enter_mail", surname=tmp[1]["surname"], name=tmp[1]["name"], side=tmp[1]["side"], rank=tmp[1]["rank"], fil_name=message.text)


@bot.message_handler(func=lambda message: True and fsm.get_state(message.from_user.id)[0] == "enter_mail")
@log
def accept_mail(message):
	tmp = fsm.get_state(message.from_user.id)
	text = language_check()
	if message.text not in [i.mail for i in models.Email.query.all()]:
		bot.send_message(message.from_user.id, text["register"]["non_mail"])	
		return 


	db.session.add(models.BotUser(user_id=message.from_user.id, surname=tmp[1]["surname"], name=tmp[1]["name"], side=tmp[1]["side"], rank=tmp[1]["rank"], fil_name=tmp[1]["fil_name"], mail=message.text, coins=10))
	db.session.commit()
	bot.send_message(message.from_user.id, text["register"]["first_message"].format(message.from_user.first_name))
	bot.send_message(message.from_user.id, text["register"]["second_message"].format(tmp[1]["name"], tmp[1]["side"], tmp[1]["fil_name"]))
	bot.send_message(message.from_user.id, text["register"]["third_message"], reply_markup=create_markup(text["quiz"]["start_quiz"]))
	fsm.reset_state(message.from_user.id)

# Защита от не зарегистрированых юзеров
@bot.message_handler(func=lambda message: True and models.BotUser.query.filter_by(user_id=message.from_user.id).first() == None)
@log
def unreg_wall(message):
	return

# ------ Викторина ------ #
# выдача
@bot.message_handler(func=lambda message: True and (message.text == language_check()["quiz"]["start_quiz"] or message.text == language_check()["quiz"]["next_question"]))
@log
def quiz_send(message):
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
			user.coins = user.coins + quiz.cost
		else:
			bot.send_message(call.from_user.id, text["quiz"]["incorrect_answer"], reply_markup=create_markup(text["quiz"]["next_question"]))
			db.session.add(models.CompleteQuiz(quiz_id=quiz.id, user_id=call.from_user.id, status="lose", cost=quiz.cost))

		db.session.commit()



# ------ Команды ------ #
@bot.message_handler(commands=['my_wallet'])
def my_wallet(message):
	user = models.BotUser.query.filter_by(user_id=message.from_user.id).first()
	bot.send_message(message.from_user.id, language_check()["functions"]["wallet"].format(user.coins))



@bot.message_handler(commands=['my_id'])
def my_id(message):
	bot.send_message(message.from_user.id, language_check()["functions"]["id"].format(message.from_user.id))







# ------ Ставки ------ #
@bot.message_handler(commands=['/bid'])
def bet(message):
	active_lot = models.ActiveLot.query.first()
	text = language_check()
	if active_lot == None:
		bot.send_message(message.from_user.id, text["bet"]["no"])
		return
	
	user = models.BotUser.query.filter_by(user_id=message.from_user.id).first()
	if active_lot.bet_date + timedelta(seconds=10) < datetime.now():
		if active_lot.cost + 10 > user.coins:
			bot.send_message(message.from_user.id, text["bet"]["not_enough"])
		
		else:
			active_lot.winner_id = message.from_user.id
			active_lot.cost = active_lot.cost + 10
			active_lot.bet_date = datetime.now()
			bot.send_message(message.from_user.id, text["bet"]["accept"])
			if models.Players.query.filter_by(user_id=message.from_user.id, lot_id=active_lot.lot_id).first() == None:
				db.session.add(models.Players(lot_id=active_lot.lot_id, user_id=message.from_user.id))
				db.session.commit()
	else:
		bot.send_message(message.from_user.id, text["bet"]["delay"])

	db.session.commit()




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
	bot.send_message(call.from_user.id, text["mod"]["success"].format(call.data.split(" ")[1], call.data.split(" ")[2]))
	user.coins = user.coins + int(call.data.split(" ")[2])
	db.session.commit()
'''

bot.remove_webhook()
if __name__ == '__main__':
	bot.polling(none_stop=True)

'''

@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
  bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
  return "!", 200


@app.route("/")
def webhook():
  bot.remove_webhook()
  bot.set_webhook(url=HEROKU_LINK + TOKEN)
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
