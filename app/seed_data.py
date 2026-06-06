"""Populate database with realistic demo data."""

import random
from datetime import date, datetime, timedelta

from app.admin.services import ensure_default_settings, set_setting
from app.extensions import db
from app.models import (
    Comment,
    Project,
    Tag,
    Task,
    TaskActivity,
    Team,
    TeamMember,
    User,
)

STATUSES = ["todo", "in_progress", "done"]
PRIORITIES = ["low", "medium", "high"]

USERS = [
    ("admin", "admin@canbas.ru", "admin123", True),
    ("anna_dev", "anna@studio.ru", "demo1234", False),
    ("boris_pm", "boris@studio.ru", "demo1234", False),
    ("clara_design", "clara@studio.ru", "demo1234", False),
    ("denis_qa", "denis@studio.ru", "demo1234", False),
    ("elena_marketing", "elena@startup.io", "demo1234", False),
    ("fedor_backend", "fedor@startup.io", "demo1234", False),
    ("galina_ops", "galina@startup.io", "demo1234", False),
    ("igor_mobile", "igor@freelance.dev", "demo1234", False),
    ("julia_analyst", "julia@freelance.dev", "demo1234", False),
]

TEAMS = [
    ("Студия «Пиксель»", 1, [2, 3, 4, 5]),
    ("Стартап LaunchPad", 6, [6, 7, 8]),
    ("Фриланс-команда", 9, [9, 10, 2]),
    ("Canbas Core", 1, [2, 7, 9]),
]

PROJECTS = {
    "Студия «Пиксель»": [
        ("Редизайн сайта клиента", "Обновление UI/UX корпоративного портала"),
        ("Мобильное приложение", "MVP для iOS и Android"),
    ],
    "Стартап LaunchPad": [
        ("MVP платформы", "Базовый функционал для первых пользователей"),
        ("Маркетинг Q2", "Кампания запуска продукта"),
    ],
    "Фриланс-команда": [
        ("Интеграции API", "Подключение платёжных систем"),
    ],
    "Canbas Core": [
        ("Canbas v2", "Развитие таск-трекера"),
    ],
}

TASK_TITLES = [
    "Сверстать главную страницу",
    "Настроить CI/CD pipeline",
    "Подготовить тест-кейсы",
    "Согласовать макеты с заказчиком",
    "Оптимизировать запросы к БД",
    "Написать документацию API",
    "Провести code review",
    "Исправить баг с авторизацией",
    "Добавить уведомления по email",
    "Обновить зависимости",
    "Спроектировать схему БД",
    "Подготовить презентацию для инвесторов",
    "Настроить мониторинг",
    "Создать landing page",
    "Провести юзабилити-тестирование",
    "Интегрировать аналитику",
    "Рефакторинг модуля задач",
    "Подготовить релизные заметки",
    "Настроить резервное копирование",
    "Проверить адаптив на планшетах",
    "Добавить фильтры в список задач",
    "Описать процесс онбординга",
    "Согласовать KPI спринта",
    "Подключить OAuth",
    "Провести ретроспективу",
    "Обновить иконки в интерфейсе",
    "Настроить staging-сервер",
    "Подготовить FAQ для пользователей",
    "Исправить отображение дедлайнов",
    "Добавить экспорт в CSV",
    "Проверить безопасность форм",
    "Создать шаблоны проектов",
    "Настроить webhooks",
    "Провести нагрузочное тестирование",
    "Обновить пользовательское руководство",
]

COMMENT_TEXTS = [
    "Взял в работу, ориентировочно к пятнице.",
    "Нужны уточнения по ТЗ — оставил комментарий в Figma.",
    "Готово, можно проверять на staging.",
    "Нашёл edge case, добавил в описание задачи.",
    "Перенёс дедлайн — жду ответ от клиента.",
    "Сделал PR, назначил ревьюера.",
    "Тесты проходят, можно мёржить.",
    "Добавил скриншоты в описание.",
    "Предлагаю разбить на две подзадачи.",
    "Согласовано с PM, двигаемся дальше.",
]

TAG_NAMES = ["frontend", "backend", "design", "bug", "urgent", "docs", "devops", "marketing"]

ACTIVITY_ACTIONS = [
    ("created", "Задача создана"),
    ("status_changed", "Статус изменён"),
    ("assigned", "Назначен исполнитель"),
    ("comment_added", "Добавлен комментарий"),
    ("priority_changed", "Изменён приоритет"),
]


def _random_past(days=60):
    delta = random.randint(0, days * 24 * 3600)
    return datetime.utcnow() - timedelta(seconds=delta)


def _random_future(days=14):
    return date.today() + timedelta(days=random.randint(1, days))


def clear_database():
    db.drop_all()
    db.create_all()


def seed_database(force=False):
    if User.query.count() > 0 and not force:
        print("База уже содержит данные. Используйте --force для перезаписи.")
        return

    if force:
        clear_database()

    ensure_default_settings()
    set_setting("site_name", "Canbas")
    set_setting("registration_enabled", "true")

    user_map = {}
    for username, email, password, is_superadmin in USERS:
        user = User(
            username=username,
            email=email,
            is_superadmin=is_superadmin,
            is_active=True,
            created_at=_random_past(90),
        )
        user.set_password(password)
        db.session.add(user)
        user_map[username] = user
    db.session.flush()

    tags = {}
    for name in TAG_NAMES:
        tag = Tag(name=name)
        db.session.add(tag)
        tags[name] = tag
    db.session.flush()

    all_users = list(user_map.values())
    team_objects = []

    for team_name, owner_idx, member_indices in TEAMS:
        owner = all_users[owner_idx - 1]
        team = Team(
            name=team_name,
            owner_id=owner.id,
            invite_code=Team.generate_invite_code(),
            created_at=_random_past(80),
        )
        db.session.add(team)
        db.session.flush()
        team_objects.append(team)

        member_ids = {owner.id}
        db.session.add(TeamMember(team_id=team.id, user_id=owner.id, role="admin"))
        for idx in member_indices:
            user = all_users[idx - 1]
            if user.id in member_ids:
                continue
            member_ids.add(user.id)
            role = "admin" if random.random() < 0.2 else "member"
            db.session.add(TeamMember(team_id=team.id, user_id=user.id, role=role))

    db.session.flush()

    task_count = 0
    for team in team_objects:
        for proj_name, proj_desc in PROJECTS.get(team.name, []):
            project = Project(
                team_id=team.id,
                name=proj_name,
                description=proj_desc,
                created_at=_random_past(70),
            )
            db.session.add(project)
            db.session.flush()

            team_members = [m.user_id for m in TeamMember.query.filter_by(team_id=team.id).all()]
            num_tasks = random.randint(6, 10)
            titles = random.sample(TASK_TITLES, min(num_tasks, len(TASK_TITLES)))

            for title in titles:
                creator_id = random.choice(team_members)
                assignee_id = random.choice(team_members) if random.random() > 0.15 else None
                status = random.choices(STATUSES, weights=[3, 4, 5])[0]
                created = _random_past(55)
                task = Task(
                    project_id=project.id,
                    title=title,
                    description=f"Описание задачи «{title}». Детали согласованы с командой {team.name}.",
                    status=status,
                    priority=random.choice(PRIORITIES),
                    assignee_id=assignee_id,
                    creator_id=creator_id,
                    due_date=_random_future() if random.random() > 0.3 else None,
                    created_at=created,
                    updated_at=created + timedelta(hours=random.randint(1, 200)),
                )
                task.tags = random.sample(list(tags.values()), k=random.randint(0, 3))
                db.session.add(task)
                db.session.flush()
                task_count += 1

                db.session.add(
                    TaskActivity(
                        task_id=task.id,
                        actor_id=creator_id,
                        action="created",
                        details="Задача создана",
                        created_at=created,
                    )
                )
                if assignee_id:
                    db.session.add(
                        TaskActivity(
                            task_id=task.id,
                            actor_id=creator_id,
                            action="assigned",
                            details="Назначен исполнитель",
                            created_at=created + timedelta(minutes=5),
                        )
                    )
                if status != "todo":
                    db.session.add(
                        TaskActivity(
                            task_id=task.id,
                            actor_id=assignee_id or creator_id,
                            action="status_changed",
                            details=f"Статус: {status}",
                            created_at=created + timedelta(hours=2),
                        )
                    )

                for _ in range(random.randint(0, 3)):
                    author_id = random.choice(team_members)
                    db.session.add(
                        Comment(
                            task_id=task.id,
                            author_id=author_id,
                            body=random.choice(COMMENT_TEXTS),
                            created_at=created + timedelta(hours=random.randint(3, 100)),
                        )
                    )

    db.session.commit()
    print(f"Готово: {User.query.count()} пользователей, {Team.query.count()} команд, "
          f"{Project.query.count()} проектов, {Task.query.count()} задач.")
    print("Super-admin: admin@canbas.ru / admin123")
