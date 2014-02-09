from flask_wtf import Form
from wtforms import BooleanField, PasswordField, TextField, TextAreaField
from wtforms.validators import DataRequired, Length, url


class LoginForm(Form):
    username = TextField('username', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')


class ClientForm(Form):
    name = TextField('Name', validators=[DataRequired(), Length(max=40)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(max=400)])
    redirect_uri = TextField('Redirect URL', validators=[url()])
    homepage = TextField('Homepage URL', validators=[url()])
