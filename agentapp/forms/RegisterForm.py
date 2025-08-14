from quart_wtf import QuartForm
from wtforms import StringField, PasswordField, SubmitField, EmailField
from wtforms.validators import DataRequired, Length, Email, EqualTo, Regexp
from wtforms.widgets import PasswordInput
from utils.Util import Util
from wtforms.validators import ValidationError

class RegisterForm(QuartForm):
    fname = StringField('First Name', validators=[DataRequired(), Length(min=2, max=25)])
    lname = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=25)])
    email = EmailField('Email', validators=[DataRequired(), Email(),Length(min=8, max=30)])
    company = StringField('Company', validators=[DataRequired(), Length(min=2, max=25)])
    uname = StringField('Username', validators=[DataRequired(), Length(min=5, max=15)])
    password = PasswordField(
        'Password',
        widget=PasswordInput(),
        validators=[
            DataRequired(),
            EqualTo('password_confirm', message=''),
            Length(min=15, max=50)
        ]
    )
    password_confirm = PasswordField(
        'Confirm Password',
        widget=PasswordInput(),
        validators=[
            DataRequired(),
            Length(min=15, max=50)
        ]
    )

    submit = SubmitField("Create Account")