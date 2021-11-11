import pickle
import models

class FSM():
	def __init__(self, db):
		self.db = db
	

	def set_state(self, user_id, state, **arg):
		models.State.query.filter_by(user_id=user_id).delete()
		data = pickle.dumps(arg)
		
		state = models.State(user_id=user_id, state=state, arg=data)
		self.db.session.add(state)
		self.db.session.commit()


	def get_state(self, user_id):
		tmp = models.State.query.filter_by(user_id=user_id).first()
		if tmp:
			arg = pickle.loads(tmp.arg)
			return (tmp.state, arg) 
		else:
			return ("idle", [])


	def reset_state(self, user_id):
		tmp = models.State.query.filter_by(user_id=user_id).first()
		if tmp:
			self.db.session.delete(tmp)
			self.db.session.commit()
		else: 
			return
