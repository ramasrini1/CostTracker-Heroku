from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, BooleanField, IntegerField, RadioField, SelectField
from wtforms.validators import InputRequired, Optional, DataRequired, Length
from wtforms import PasswordField, TextAreaField, validators


class AddEventForm(FlaskForm):
    """Form for adding events."""

    evt_name = StringField("Event Name")

class AddExpenseForm(FlaskForm):
  """Add Expenes Form """
  
  evt = SelectField("Event", coerce=int)
  friend = SelectField("Friend")
  cost = IntegerField("Enter Your expense amt", validators=[validators.NumberRange(min=1, max=None)] )
  cost_info = StringField("Cost Info(optional)")


class UserAddForm(FlaskForm):
    """Form for adding users."""
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[Length(min=6)])
   
class LoginForm(FlaskForm):
    """Login form."""
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[Length(min=6)])

class AdminForm(FlaskForm):
    """Admin form."""
    access_token = StringField('Access Token', validators=[Length(min=6)])