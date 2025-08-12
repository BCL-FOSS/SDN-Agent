from quart_wtf import QuartForm
from wtforms import StringField, SubmitField, RadioField, SelectField, TextAreaField, PasswordField
from wtforms.validators import DataRequired, EqualTo, Length
from utils.Util import Util
from wtforms.widgets import PasswordInput

class APIKeyGenForm(QuartForm):

    ctr_opts=[('agnt','Agentik SDN Automation'), ('mon','Network Monitor')]

    controller = SelectField(label='Choose service', choices=ctr_opts, validators=[DataRequired()])
    
    submit = SubmitField('Generate API Key')