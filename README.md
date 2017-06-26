# A Django + GraphQL + Apollo + React Stack Demo

This repo contains the code shown at the [Singapore Djangonauts June 2017 Meetup](https://www.meetup.com/Singapore-Djangonauts/events/240608776/)

A video of the workshop will be uploaded on engineers.sg, shortly.

This README was basically the "slides" for the workshop, so if you want to learn
as well, just keep on reading!

In this workshop, we will address the following topics:

## [Part 1: The Backend](#part1)

1. [Create a new Django Project](#create-new-django-project)
1. [Create a Simple Django App](#create-simple-app)
1. Add GraphQL to Django
1. Add GaphQL-Schema to Django (CRUD Views & Tests)
1. Add JWT-Authentication to Django

## Part 2: The Frontend

1. Create a new React Project
1. Add ReactRouter to React
1. Add Apollo to React
1. Add Token Middleware for Authentication
1. Add Login / Logout Views
1. Add Query for ListView
1. Add Query with Variables for DetailView
1. Add Mutation for CreateView
1. Show Form Errors on CreateView
1. Add Filtering to ListView
1. Add Pagination to ListView
1. Add Cache Invalidation

# <a name="part1"></a>Part 1: The Backend

## <a name="create-new-django-project"></a>Create a new Django Project

For this demonstration we will need a backend that can serve our GraphQL API.
We will chose Django for this, so the first thing we want to do is to create a
new Django project. If you are new to Python, you need to read about [virtualenvwrapper](https://virtualenvwrapper.readthedocs.io/en/latest/), first.

```bash
mkdir -p ~/Projects/django-graphql-apollo-react-demo/src
cd ~/Projects/django-graphql-apollo-react-demo/src
mkvirtualenv django-graphql-apollo-react-demo
pip install django
pip install pytest
pip install pytest-django
pip install pytest-cov
pip install mixer
django-admin startproject backend
cd backend
./manage.py migrate
./manage.py createsuperuser
./manage.py runserver
```

> You should now be able to browse to `localhost:8000/admin/` and login with
> your superuser account

We like to build our Django apps in a test-driven manner, so let's also create
a few files to setup our testing framework:

**File: ./backend/backend/test_settings.py**

```py
from .settings import *  # NOQA

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',
)

DEFAULT_FILE_STORAGE = 'inmemorystorage.InMemoryStorage'
```

**File: ./backend/pytest.ini**

```config
[pytest]
DJANGO_SETTINGS_MODULE = backend.test_settings
```

**File: ./backend/.coveragerc**

```config
[run]
omit = manage.py, *wsgi.py, *test_settings.py, *settings.py, *urls.py, *__init__.py, */apps.py, */tests/*, */migrations/*
```

> From your `./backend` folder, you should now be able to execute `pytest --cov-report html --cov .` and then `open htmlcov/index.html` to see the coverage report.

## <a name="create-simple-app"></a>Create a Simple Django App

At this point, our Django project is pretty useless, so let's create a simple
Twitter-like app that allows users to create messages. It's a nice example for
an app that has a CreateView, a ListView and a DetailView.

```bash
cd ~/Projects/django-graphql-apollo-react-demo/src/backend
django-admin startapp simple_app
cd simple_app
mkdir tests
touch tests/__init__.py
touch tests/test_models.py
```

Whenever we create a new app, we need to tell Django that this app is now part
of our project:

**File: ./backend/backend/settings.py**

```py
# Add `simple_app` to `INSTALLED_APPS` setting

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'simple_app',
]
```

First, let's create a test for our upcoming new model. The model doesn't do
much, so we will simply test if we are able to create an instance and save it
to the DB. We are using [mixer](https://github.com/klen/mixer) to help us with
the creation of test-fixtures.

**File: ./backend/simple_app/tests/test_models.py**

```py
import pytest
from mixer.backend.django import mixer

# We need to do this so that writing to the DB is possible in our tests.
pytestmark = pytest.mark.django_db


def test_message():
    obj = mixer.blend('simple_app.Message')
    assert obj.pk > 0
```

Next, let's create our `Message` model:

**File: ./backend/simple_app/models.py**

```py
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models

class Message(models.Model):
    user = models.ForeignKey('auth.User')
    message = models.TextField()
    creation_date = models.DateTimeField(auto_now_add=True)
```

Let's also register the new model with the Django admin, so that we can add
entries to the new table:

**File: ./backend/simple_app/admin.py**

```py
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib import admin
from . import models

admin.site.register(models.Message)
```

Whenever we make changes to a model, we need to create and run a migration:

```bash
cd ~/Projects/django-graphql-apollo-react-demo/src/backend
./manage.py makemigrations simple_app
./manage.py migrate
```

> At this point you should be able to browse to `localhost:8000/admin/` and see the table of the new `simple_app` app.

> You should also be able to run `pytest` and see 1 successful test.
