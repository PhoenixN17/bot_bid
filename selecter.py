import models

for i in models.ActiveLot.query.all():
	print(i)


