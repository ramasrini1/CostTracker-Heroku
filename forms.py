from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, BooleanField, IntegerField, RadioField, SelectField
from wtforms.validators import InputRequired, Optional, DataRequired, Length
from wtforms import PasswordField, TextAreaField, validators


class AddGroupForm(FlaskForm):
    """Form for adding groups."""
    gp_name = StringField("Group Name")

class ShowGroupForm(FlaskForm):
    """Form for adding groups."""
    group = SelectField("Group Name")
    
class AddExpenseForm(FlaskForm):
  """Add Expenes Form """
  
  gp = SelectField("Select Group")
  friend = SelectField("Select Friend", validators=[InputRequired()])
  cost = IntegerField("Enter expense amt", validators=[validators.NumberRange(min=1, max=None)] )
  cost_info = StringField("Expense Info(optional)")


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