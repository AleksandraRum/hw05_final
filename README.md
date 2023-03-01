# Социальная сеть Yatube для публикации постов и картинок
## Проект создан в рамках обучения в Яндекс.Практикум

[![CI](https://github.com/yandex-praktikum/hw05_final/actions/workflows/python-app.yml/badge.svg?branch=master)](https://github.com/yandex-praktikum/hw05_final/actions/workflows/python-app.yml)

## Описание:

 Социальная сеть для публикации постов и картинок. Пользователи могут подписываться на избранных авторов, оставлять и удалять комментари к постам, включать свои посты в тематические группы.
 В проекте реализована система регистрации новых пользователей, восстановление пароля через почту, пагинация страниц, кэширование. Также осуществляется покрытие проекта Unittest.

## Стек технологий:

 Python 3.7.0
 Django 3.2.13
 HTML

## Установка и запуск проекта:

1. Клонировать репозиторий:

```
git clone https://github.com/AleksandraRum/hw05_final.git
```

2. Установить виртуальное окружение, активировать и установить в него необходимые зависимости:

```
python3 -m venv venv

. venv/bin/activate

python3 -m pip install --upgrade pip

pip install -r requirements.txt

```

3. Перейти в директорию с файлом manage.py и выполнить миграции:

```
cd yatube

python manage.py migrate
```

4. Запустить проект в режиме Django:

```
python manage.py runserver
```