import telebot
import config
from tb_forms import TelebotForms, ffsm
from fsm import FSM
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = config.db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

bot = telebot.TeleBot(config.TOKEN)
tbf = TelebotForms(bot)
db = SQLAlchemy(app)
fsm = FSM(db)
