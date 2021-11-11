import models
from models import db

for i in models.BotUser.query.all():
        db.session.delete(i)

db.session.commit()


