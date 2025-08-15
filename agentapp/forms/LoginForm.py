from quart_wtf import QuartForm
from wtforms import PasswordField, SubmitField, StringField
from wtforms.validators import DataRequired, Length
from wtforms.widgets import PasswordInput

class LoginForm(QuartForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=8, max=30)])
    password = PasswordField(
        'Password',
        widget=PasswordInput(),
        validators=[
            DataRequired(),
            Length(min=15, max=50)
        ]
    )
    submit = SubmitField('Login')
        
       

