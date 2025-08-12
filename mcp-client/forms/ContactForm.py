from quart_wtf import QuartForm
from wtforms import SubmitField, StringField, TextAreaField
from wtforms.validators import DataRequired, Length

class ContactForm(QuartForm):

    name = StringField('Name', validators=[DataRequired(), Length(min=10, max=80)])
    email = StringField('Email', validators=[DataRequired(), Length(min=10, max=80)])
    phone = StringField('Phone', validators=[DataRequired(), Length(min=10, max=80)])
    message = TextAreaField('Message', validators=[DataRequired(), Length(min=10, max=80)])
    submit = SubmitField('Contact Us')