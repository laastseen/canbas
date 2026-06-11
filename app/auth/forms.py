from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional

CONSENT_PD_MESSAGE = "Необходимо согласие на обработку персональных данных"


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
    consent_pd = BooleanField(
        "Согласие на обработку персональных данных",
        validators=[DataRequired(message=CONSENT_PD_MESSAGE)],
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
    consent_pd = BooleanField(
        "Согласие на обработку персональных данных",
        validators=[DataRequired(message=CONSENT_PD_MESSAGE)],
    )
    submit = SubmitField("Сохранить")
