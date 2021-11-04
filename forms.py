from tb_forms import BaseForm,fields

class Question(BaseForm):
	""" Создать форму для регистрации """
	def __init__(self, language):
		self.language = language
		self.update_name = "add_question"
		self.close_form_but = True
		self.freeze_mode = True
		self.submit_button_text = self.language["submit"]
		self.cancel_button_text  = self.language["cancel_button"]
		self.stop_freeze_text = self.language["freeze_form_alert"]
		self.input_not_valid = self.language["invalid_input"]

		self.media = fields.MediaField(self.language["apanel"]["add_question"]["media"], self.language["apanel"]["add_question"]["send_media"], required=False)
		self.question = fields.StrField(self.language["apanel"]["add_question"]["question"], self.language["apanel"]["add_question"]["send_question"])
		self.answer = fields.StrField(self.language["apanel"]["add_question"]["answer"], self.language["apanel"]["add_question"]["send_answer"])
		self.false = fields.StrField(self.language["apanel"]["add_question"]["false"], self.language["apanel"]["add_question"]["send_false"])
		self.cost = fields.StrField(self.language["apanel"]["add_question"]["cost"], self.language["apanel"]["add_question"]["send_cost"])



	def form_validator(self, call, form_data):
		try:
			int(form_data.cost)
		except:
			return self.language["invalid_input"]

		return True