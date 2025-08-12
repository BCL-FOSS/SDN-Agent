from quart_wtf import QuartForm
from wtforms import StringField, SubmitField, RadioField, SelectField, TextAreaField, PasswordField
from wtforms.validators import DataRequired, EqualTo, Length
from utils.Util import Util
from wtforms.widgets import PasswordInput

class ProbeConfigGenForm(QuartForm):
    ctr_opts=[('--deb','Ubuntu/Debian'), ('--rpm','RHEL/CentOS/Fedora/AlmaLinux'), ('--pkg', 'FreeBSD'), ('--txz', 'opnsense/pfsense')]

    installer = SelectField(label='Choose Installer', choices=ctr_opts, validators=[DataRequired()])

    submit = SubmitField('Download Probe Installer')