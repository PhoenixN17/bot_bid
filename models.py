from app import db
from datetime import datetime

def auto_repr(self):
    """ Автоматическое REPR форматирование для обьектов """
    base_repr = "<{}(".format(self.__class__.__name__)
    for name in self.__dict__:
        if name[0] == "_":
            continue
        value = self.__dict__[name]
        base_repr += "{}='{}',".format(name,value)
    base_repr = base_repr[:-1]
    base_repr += ")>"
    return base_repr




########### Для работы основного бота  ###########


class State(db.Model):
	"""Модель для состояние юзеров"""
	__tablename__ = 'user_state'
	user_id = db.Column(db.Integer(), primary_key=True)
	state = db.Column(db.String())
	arg = db.Column(db.Binary())

	def __repr__(self):
		return auto_repr(self)


class BotUser(db.Model):
	"""Модель юзеров"""
	__tablename__ = "user"
	id = db.Column(db.Integer(), primary_key=True)
	user_id = db.Column(db.Integer(), unique=True)
	surname = db.Column(db.String())
	name = db.Column(db.String())
	side = db.Column(db.String())
	rank = db.Column(db.String())
	fil_name = db.Column(db.String())
	mail = db.Column(db.String())
	coins = db.Column(db.Integer())
	


	def __repr__(self):
		return auto_repr(self)


class Email(db.Model):
	"""Модель почт"""
	__tablename__ = "email"
	id = db.Column(db.Integer(), primary_key=True)
	mail = db.Column(db.String())

	def __repr__(self):
		return auto_repr(self)


class Quiz(db.Model):
	"""Модель вопросов"""
	__tablename__ = "quiz"
	id = db.Column(db.Integer(), primary_key=True)
	quiz_type = db.Column(db.String())
	quiz_media_id = db.Column(db.String())
	question = db.Column(db.String())
	answer = db.Column(db.String())
	false = db.Column(db.Binary())
	cost = db.Column(db.Integer())

	

	def __repr__(self):
		return auto_repr(self)


class CompleteQuiz(db.Model):
	"""Модель выполненых вопросов"""
	__tablename__ = "complete_quiz"
	id = db.Column(db.Integer(), primary_key=True)
	quiz_id = db.Column(db.Integer())
	user_id = db.Column(db.Integer())
	status = db.Column(db.String())
	cost = db.Column(db.Integer())

	

	def __repr__(self):
		return auto_repr(self)

class Auc(db.Model):
	"""Модель выполненых вопросов"""
	__tablename__ = "auc"
	id = db.Column(db.Integer(), primary_key=True)
	pic = db.Column(db.String())
	name = db.Column(db.String())
	shortname = db.Column(db.String())
	disc = db.Column(db.String())
	cost = db.Column(db.Integer())
	status = db.Column(db.String())
	

	def __repr__(self):
		return auto_repr(self)


class ActiveLot(db.Model):
	"""Модель выполненых вопросов"""
	__tablename__ = "active_lot"
	id = db.Column(db.Integer(), primary_key=True)
	lot_id = db.Column(db.Integer())
	winner_id = db.Column(db.Integer())
	cost = db.Column(db.Integer())	
	bet_date = db.Column(db.DateTime(), default=datetime.utcnow)


	def __repr__(self):
		return auto_repr(self)



class Players(db.Model):
	"""Модель выполненых вопросов"""
	__tablename__ = "players"
	id = db.Column(db.Integer(), primary_key=True)
	lot_id = db.Column(db.Integer())
	user_id = db.Column(db.Integer())



	def __repr__(self):
		return auto_repr(self)


db.create_all()
db.session.commit()