from flask_wtf import FlaskForm
from flask_wtf.file import FileRequired
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, FileField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError

from models import User


class LoginForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class RegistrationForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired()])
    email = StringField('Электронная почта', validators=[DataRequired(), Email()])
    password1 = PasswordField('Пароль', validators=[DataRequired()])
    password2 = PasswordField(
        'Повторите пароль', validators=[DataRequired(), EqualTo('password1')])
    submit = SubmitField('Создать')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Используйте другое имя пользователя')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Используйте другой адрес электронной почты')


class CourseDescForm(FlaskForm):
    name = StringField("Название", validators=[DataRequired()])
    desc = TextAreaField("Описание", validators=[DataRequired()])
    short_desc = TextAreaField("Описание2", validators=[DataRequired()])
    img = FileField("Картинка", validators=[FileRequired()])
    submit = SubmitField("Сохранить")


class SearchForm(FlaskForm):
    req = StringField('Введите запрос')
    submit = SubmitField('Поиск')


class EditPassword(FlaskForm):
    old_password = PasswordField('Старый пароль', validators=[DataRequired()])

    password1 = PasswordField('Новый пароль', validators=[DataRequired()])
    password2 = PasswordField(
        'Повторите пароль', validators=[DataRequired(), EqualTo('password1')])

    submit = SubmitField('Изменить')

    def validate_password(self, usr, pwd):
        if not usr.check_password(pwd):
            raise ValidationError('Wrong old password')


class EditMainInfo(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired()])
    email = StringField('Электронная почта', validators=[DataRequired(), Email()])
    submit = SubmitField('Сохранить')
