# Дипломный проект Foodgram

![workflow](https://github.com/DashaMalva/foodgram-project-react/actions/workflows/foodgram_workflow.yml/badge.svg)  
  
[![Python](https://img.shields.io/badge/-Python-464646?style=flat-square&logo=Python)](https://www.python.org/)
[![Django](https://img.shields.io/badge/-Django-464646?style=flat-square&logo=Django)](https://www.djangoproject.com/)
[![Django REST Framework](https://img.shields.io/badge/-Django%20REST%20Framework-464646?style=flat-square&logo=Django%20REST%20Framework)](https://www.django-rest-framework.org/)
[![gunicorn](https://img.shields.io/badge/-gunicorn-464646?style=flat-square&logo=gunicorn)](https://gunicorn.org/)
[![Nginx](https://img.shields.io/badge/-NGINX-464646?style=flat-square&logo=NGINX)](https://nginx.org/ru/)
[![PostgreSQL](https://img.shields.io/badge/-PostgreSQL-464646?style=flat-square&logo=PostgreSQL)](https://www.postgresql.org/)
[![docker](https://img.shields.io/badge/-Docker-464646?style=flat-square&logo=docker)](https://www.docker.com/)
[![GitHub%20Actions](https://img.shields.io/badge/-GitHub%20Actions-464646?style=flat-square&logo=GitHub%20actions)](https://github.com/features/actions)
[![Yandex.Cloud](https://img.shields.io/badge/-Yandex.Cloud-464646?style=flat-square&logo=Yandex.Cloud)](https://cloud.yandex.ru/)


## Описание приложения
```Foodgram``` или приложение «Продуктовый помощник» - это сайт, на котором пользователи публикуют рецепты, добавляют чужие рецепты в избранное и подписываются на публикации других авторов. Сервис «Список покупок» позволяет пользователям создавать список продуктов, которые нужно купить для приготовления выбранных блюд.

### Возможности приложения
- Просмотр опубликованных рецептов.
- Публикация рецептов.
- При создании рецепта выбираются ингредиенты из предустановленного списка, указывается их количество.
- Фильтрация рецептов по тегам.
- Добавление рецептов в Избранное.
- Добавление рецептов в Список покупок.
- Печать Списка покупок: печать требуемых для приготовления блюд ингредиентов и их количества.
- Подписка на авторов.
- Просмотр своих подписок. Для каждого автора выведены его последние опубликованные рецепты.
- Страница автора со списков его опубликованных рецептов.
- Регистрация и авторизация пользователей. Разные уровни доступа для гостей и авторизованных пользователей.


## Учебная составляющая
Для реализации проекта Яндекс.Практикумом были предоставлены техническое задание и готовый фронтенд (одностраничное приложение на фреймворке React). На основе этого был полностью написан бэкенд приложения (созданы модели, админ-панель и реализован API).

## Технологии
* Python 3.10
* Django 4.1.4
* Django Rest Framework 3.12.4
* Gunicorn 20.1.0
* Psycopg2 binary 2.9.5

### Проект упакован в связанные контейнеры Docker:

* контейнер для бекэнда проекта;
* контейнер для фронтэнда проекта;
* контейнер для базы данных Postgres (образ postgres:13.0-alpine);
* контейнер для веб-сервера Nginx (образ nginx:1.21.3-alpine).


### Команды для запуска приложения в контейнерах
- Развернуть проект:
```
docker-compose up -d
```
- Выполнить миграции, создать суперпользователя и собрать статику:
```
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py createsuperuser
docker-compose exec backend python manage.py collectstatic --no-input
```
- Наполнить проект данными об ингредиентах для рецептов:
```
docker-compose exec backend python manage.py load_csv
```

### Шаблон env-файла
В env-файле директории infra должны храниться переменные окружения для работы с базой данных.
Пример наполнения env-файла:
> DB_ENGINE=django.db.backends.postgresql<br>
> DB_NAME=postgres<br>
> POSTGRES_USER=postgres<br>
> POSTGRES_PASSWORD=12345<br>
> DB_HOST=db
> DB_PORT=5432


## Документация API Foodgram
```http://daryamatv.ddns.net/api/docs/redoc.html```


## Лицензия
The MIT License (MIT)

### Автор проекта
Студент Яндекс.Практикум,<br>
Дарья Матвиевская
