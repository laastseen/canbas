from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional


class LoginForm(FlaskForm):
    email = StringField("Электронная почта", validators=[DataRequired(), Email()])
    password = PasswordField("Пароль", validators=[DataRequired()])
    submit = SubmitField("Войти")


class RegistrationForm(FlaskForm):
    username = StringField("Имя пользователя", validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField("Электронная почта", validators=[DataRequired(), Email()])
    password = PasswordField("Пароль", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        "Подтверждение пароля",
        validators=[DataRequired(), EqualTo("password")],
    )
    submit = SubmitField("Зарегистрироваться")


class ProfileForm(FlaskForm):
    username = StringField("Имя пользователя", validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField("Электронная почта", validators=[DataRequired(), Email()])
    current_password = PasswordField("Текущий пароль", validators=[Optional()])
    new_password = PasswordField("Новый пароль", validators=[Optional(), Length(min=6)])
    confirm_new_password = PasswordField(
        "Подтверждение нового пароля",
        validators=[Optional(), EqualTo("new_password", message="Пароли не совпадают")],
    )
    submit = SubmitField("Сохранить")
