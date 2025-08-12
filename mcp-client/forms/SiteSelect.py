from quart_wtf import QuartForm
from wtforms import SubmitField, SelectField

class SiteSelect(QuartForm):

    sites_list = SelectField(label="Choose a site...")

    submit = SubmitField('View Site')