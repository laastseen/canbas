from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import DateField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional


class TaskForm(FlaskForm):
    title = StringField("Название", validators=[DataRequired(), Length(max=200)])
    description = TextAreaField("Описание", validators=[Optional(), Length(max=2000)])
    status = SelectField(
        "Статус",
        choices=[("todo", "К выполнению"), ("in_progress", "В работе"), ("done", "Выполнено")],
        validators=[DataRequired()],
    )
    priority = SelectField(
        "Приоритет",
        choices=[("low", "Низкий"), ("medium", "Средний"), ("high", "Высокий")],
        validators=[DataRequired()],
    )
    assignee_id = SelectField("Исполнитель", coerce=int, validators=[Optional()])
    due_date = DateField("Срок выполнения", validators=[Optional()])
    tags = StringField("Теги", validators=[Optional(), Length(max=255)])
    submit = SubmitField("Сохранить задачу")


class CommentForm(FlaskForm):
    body = TextAreaField("Комментарий", validators=[DataRequired(), Length(max=1000)])
    submit = SubmitField("Добавить комментарий")


class AttachmentForm(FlaskForm):
    file = FileField(
        "Вложение",
        validators=[
            DataRequired(),
            FileAllowed(["png", "jpg", "jpeg", "gif", "pdf", "doc", "docx", "txt", "zip"]),
        ],
    )
    submit = SubmitField("Загрузить")
