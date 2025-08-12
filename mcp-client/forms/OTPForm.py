from quart_wtf import QuartForm
from wtforms import SubmitField, StringField, TextAreaField
from wtforms.validators import DataRequired, Length

class OTPForm(QuartForm):

    otp_code_cnfrm = StringField('Enter OTP code', validators=[DataRequired(), Length(min=4, max=10)])
    submit = SubmitField('Confirm 2FA')