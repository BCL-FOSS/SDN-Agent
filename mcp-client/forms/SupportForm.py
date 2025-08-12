from quart_wtf import QuartForm
from wtforms import SubmitField, StringField
from wtforms.validators import DataRequired, Length
from utils.Util import Util

class SupportForm(QuartForm):
    message = StringField('Message', validators=[DataRequired(), Length(min=10, max=80)])
    submit = SubmitField('Submit Ticket')

    async def async_validate_message(self, field):
        util_obj=Util()
        util_obj.form_input_validation(string_to_check=field.data)