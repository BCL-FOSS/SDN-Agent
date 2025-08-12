from quart_wtf import QuartForm
from wtforms import PasswordField, SubmitField, EmailField, StringField
from wtforms.validators import DataRequired, Length, Email
from wtforms.widgets import PasswordInput
from utils.Util import Util

class LoginForm(QuartForm):
    email = EmailField('Email', validators=[DataRequired(), Email(), Length(min=8, max=30)])
    password = PasswordField(
        'Password',
        widget=PasswordInput(),
        validators=[
            DataRequired(),
            Length(min=15, max=50)
        ]
    )
    submit = SubmitField('Login')
        
       

