from quart_wtf import QuartForm
from wtforms import StringField, SubmitField, RadioField, SelectField, TextAreaField, PasswordField
from wtforms.validators import DataRequired, EqualTo, Length
from utils.Util import Util
from wtforms.widgets import PasswordInput

class SitesForm(QuartForm):

    site_name = StringField(label="enter name for new site", validators=[DataRequired()])

    submit = SubmitField('Create Site')