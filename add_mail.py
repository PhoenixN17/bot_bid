import models
from models import db

mails = [i.mail for i in models.Email.query.all()]

f = open('mails.txt', 'r')
for i in f.readlines():
	if i[-1] == "\n":
		i = i[:-1]
	if i in mails:
		continue

	db.session.add(models.Email(mail=i))

db.session.commit()

