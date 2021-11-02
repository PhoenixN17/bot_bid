import telebot
import models
import config
import pickle
import json
import random
from tool import language_check, log, create_inlineKeyboard, create_markup
from app import bot, tbf, fsm, db

# f
#db.session.add(models.Email(mail="jeck@gmail.com"))
#db.session.add(models.Quiz(quiz_type="text", quiz_media_id="text", question="whho?", answer="mhe", false=pickle.dumps(["he", "she", "it"]), cost=10))
#db.session.commit()


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
	complete_quiz = [i.id for i in user_complete_quiz]
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
		return

# Обработка ответа
@bot.callback_query_handler(func=lambda call: True and call.data.split(" ")[0] == "answer_quiz")
@log
def quiz_accept_answer(call):
#	bot.delete_message(call.from_user.id)
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
			db.session.add(models.CompleteQuiz(quiz_id=quiz.id, user_id=call.from_user.id, status="win"))
			user.coins = user.coins + quiz.cost
		else:
			bot.send_message(call.from_user.id, text["quiz"]["incorrect_answer"], reply_markup=create_markup(text["quiz"]["next_question"]))
			db.session.add(models.CompleteQuiz(quiz_id=quiz.id, user_id=call.from_user.id, status="lose"))

		db.session.commit()



# ------ Команды ------ #
@bot.message_handler(commands=['my_wallet'])
def my_wallet(message):
	user = models.BotUser.query.filter_by(user_id=message.from_user.id).first()
	bot.send_message(message.from_user.id, language_check()["function"]["wallet"].format(user.coins))



@bot.message_handler(commands=['my_id'])
def my_id(message):
	bot.send_message(message.from_user.id, language_check()["function"]["id"].format(message.from_user.id))







# ------ Админ панель ------ #
@bot.message_handler(commands=['/apanel'])
def apanel(message):
	if message.from_user.id in config.admin:
		bot.send_message(message.from_user.id, "Админ панель", reply_markup=create_inlineKeyboard(language_check()["apanel"]["buttons"]), 2)


# Создание слота



bot.remove_webhook()
if __name__ == '__main__':
	bot.polling(none_stop=True)

'''

@server.route('/' + TOKEN, methods=['POST'])
def getMessage():
  bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
  return "!", 200


@server.route("/")
def webhook():
  bot.remove_webhook()
  bot.set_webhook(url=HEROKU_LINK + TOKEN)
  return "!", 200


# Получаем новые сообщения
if __name__ == "__main__":
  server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000))) 
  print("START")

'''


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
