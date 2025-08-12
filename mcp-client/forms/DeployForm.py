from quart_wtf import QuartForm
from wtforms import StringField, SubmitField, RadioField, SelectField, TextAreaField, PasswordField
from wtforms.validators import DataRequired, EqualTo, Length
from utils.Util import Util
from wtforms.widgets import PasswordInput

class DeployForm(QuartForm):

    srvr_opts=[('387', 'Ubuntu 20.04'), ('1743', 'Ubuntu 22.04'), 
               ('2284', 'Ubuntu 24.04')]
    
    plans=[('vc2-4c-8gb','Small'),('vc2-6c-16gb','Medium'), ('vc2-8c-32gb','Large')]
    
    ctr_opts=[('ubnt','Ubiquiti UniFi Network Server'), ('omd','TP-Link Omada Controller')]

    regions=[('blr','India'), ('sgp','Singapore'), ('icn','Korea'), ('dfw','US-Dallas'), ('ewr','US-New Jersey'), ('mia','US-Miami'), 
             ('ord','US-Chicago'), ('sea','US-Seattle'),  ('sjc','US-California')]


    controller = SelectField(label='Choose Network Controller', choices=ctr_opts, validators=[DataRequired()])
    
    plan = SelectField(label='Choose a plan', choices=plans, validators=[DataRequired()])

    region = SelectField(label='Choose a region', choices=regions, validators=[DataRequired()])

    submit = SubmitField('Deploy Server')