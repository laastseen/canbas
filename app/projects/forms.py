from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional


class TeamForm(FlaskForm):
    name = StringField("Название команды", validators=[DataRequired(), Length(max=120)])
    submit = SubmitField("Создать команду")


class ProjectForm(FlaskForm):
    team_id = SelectField("Команда", coerce=int, validators=[DataRequired()])
    name = StringField("Название проекта", validators=[DataRequired(), Length(max=120)])
    description = TextAreaField("Описание", validators=[Optional(), Length(max=1000)])
    submit = SubmitField("Создать проект")


class JoinTeamForm(FlaskForm):
    invite_code = StringField("Код приглашения", validators=[DataRequired(), Length(min=8, max=10)])
    submit = SubmitField("Вступить в команду")
