from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField
from wtforms.validators import InputRequired, DataRequired, Email, Length

class UserAddForm(FlaskForm):
    """Form for adding users."""

    username = StringField('Username', validators=[InputRequired(message="Username Required")])
    first_name = StringField("First Name", validators=[InputRequired(message="First Name Required")])
    last_name = StringField("Last Name", validators=[InputRequired(message="Last Name Required")])
    password = PasswordField('Password', validators=[Length(min=6)])
   


class LoginForm(FlaskForm):
    """Login form."""

    username = StringField('Username', validators=[InputRequired()])
    password = PasswordField('Password', validators=[Length(min=6)])

class UserEditForm(FlaskForm):
    """Form for editing users."""
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    username = StringField('Username', validators=[DataRequired()])
    image_url = StringField('(Optional) Image URL')
    header_image_url = StringField('(Optional) Header Image URL')
    bio = StringField('Bio', validators=[Length(max=150)])




