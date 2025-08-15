from quart_wtf import QuartForm
from wtforms import StringField, SubmitField, SelectField, PasswordField
from wtforms.validators import DataRequired, EqualTo, Length
from wtforms.widgets import PasswordInput

class SDNCredForm(QuartForm):
        
    ctr_opts=[('ubnt','Ubiquiti UniFi Network Server'), ('omd','TP-Link Omada Controller')]

    controller = SelectField(label='Choose Network Controller', choices=ctr_opts, validators=[DataRequired()])

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

    submit = SubmitField('Add SDN Crendentials')