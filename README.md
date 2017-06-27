# A Django + GraphQL + Apollo + React Stack Demo

This repo contains the code shown at the [Singapore Djangonauts June 2017 Meetup](https://www.meetup.com/Singapore-Djangonauts/events/240608776/)

A video of the workshop will be uploaded on engineers.sg, shortly.

This README was basically the "slides" for the workshop, so if you want to learn
as well, just keep on reading!

In this workshop, we will address the following topics:

## [Part 1: The Backend](#part1)

1. [Create a new Django Project](#create-new-django-project)
1. [Create a Simple Django App](#create-simple-app)
1. [Add GraphQL to Django](#add-graphql-to-django)
1. [Add Message-DjangoObjectType to GraphQL Schema](#add-django-object-type)
1. [Add Mutation to GraphQL Schema](#add-mutation)
1. [Add JWT-Authentication to Django](#add-jwt)

## Part 2: The Frontend

1. [Create a new React Project](#create-new-react-project)
1. [Add ReactRouter to React](#add-react-router)
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

Before you start, you should read a little bit about [GraphQL](http://graphql.org/learn/) and [Apollo](http://dev.apollodata.com/react/) and [python-graphene](http://docs.graphene-python.org/projects/django/en/latest/).

If you have basic understanding of Python, Django, JavaScript and ReactJS, you
should be able to follow this tutorial and copy and paste the code snippets
shown below and hopefully it will all work out nicely. It should give you a
feeling for the necessary steps involved, for the files involved and some ideas
for some useful patterns that most people usually need in their apps.

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


```py
# File: ./backend/backend/test_settings.py

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

```config
# File: ./backend/pytest.ini

[pytest]
DJANGO_SETTINGS_MODULE = backend.test_settings
```

```config
# File: ./backend/.coveragerc

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

```py
# File: ./backend/backend/settings.py

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

```py
# File: ./backend/simple_app/tests/test_models.py

import pytest
from mixer.backend.django import mixer

# We need to do this so that writing to the DB is possible in our tests.
pytestmark = pytest.mark.django_db


def test_message():
    obj = mixer.blend('simple_app.Message')
    assert obj.pk > 0
```

Next, let's create our `Message` model:

```py
# File: ./backend/simple_app/models.py
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

```py
# File: ./backend/simple_app/admin.py
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

## <a name="add-graphql-to-django"></a>Add GraphQL to Django

Sinve we have now a Django project with a model, we can start thinking about
adding an API. We will use GraphQL for that.

```bash
cd ~/Projects/django-graphql-apollo-react-demo/src/backend
pip install graphene-django
```

Whenever we add a new app to Django, we need to update our `INSTALLED_APPS`
setting. Because of `graphene-django`, we also need to add one app-specific
setting.

```py
# File: ./backend/backend/settings.py
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'graphene_django',
    'simple_app',
]

GRAPHENE = {
    'SCHEMA': 'backend.schema.schema',
}
```

Now we need to create our main `schema.py` file. This file is similar to our
main `urls.py` - it's task is to import all the schema-files in our project and
merge them into one big schema.

```py
# File: ./backend/backend/schema.py

import graphene

class Queries(
    graphene.ObjectType
):
    dummy = graphene.String()


schema = graphene.Schema(query=Queries)
```

Finally, we need to hook up GraphiQL in our Django `urls.py`:

```py
# File: ./backend/backend/urls.py

from django.conf.urls import url
from django.contrib import admin
from django.views.decorators.csrf import csrf_exempt

from graphene_django.views import GraphQLView


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^graphiql', csrf_exempt(GraphQLView.as_view(graphiql=True))),
    url(r'^gql', csrf_exempt(GraphQLView.as_view(batch=True))),
]
```

> At this point you should be able to browse to `localhost:8000/graphiql` and run the query `{ dummy }`

## <a name="add-django-object-type"></a>Add Message-DjangoObjectType to GraphQL Schema

If you have used Django Rest Framework before, you know that you have to create
serializers for all your models. With GraphQL it is very similar: You have to
create Types for all your models.

We will begin with creating a type for our Message model and when we are at it,
we will also create a query that returns all messages.

In good TDD fashion, we begin with a test for the type and a test for the
query:

```py
# File: ./backend/simple_app/tests/test_schema.py

import pytest
from mixer.backend.django import mixer

from .. import schema


pytestmark = pytest.mark.django_db


def test_message_type():
    instance = schema.MessageType()
    assert instance


def test_all_messages():
    mixer.blend('simple_app.Message')
    mixer.blend('simple_app.Message')
    q = schema.Query()
    res = q.resolve_all_messages(None, None, None)
    assert res.count() == 2, 'Should return all messages'
```

In order to make our test pass, we will now add our type and the query:

```py
# File: ./backend/simple_app/schema.py

import graphene
from graphene_django.types import DjangoObjectType

from . import models


class MessageType(DjangoObjectType):
    class Meta:
        model = models.Message


class Query(graphene.AbstractType):
    all_messages = graphene.List(MessageType)

    def resolve_all_messages(self, args, context, info):
        return models.Message.objects.all()
```

Finally, we need to update your main `schema.py` file:

```py
# File: ./backend/backend/schema.py

import graphene

import simple_app.schema


class Queries(
    simple_app.schema.Query,
    graphene.ObjectType
):
    dummy = graphene.String()


schema = graphene.Schema(query=Queries)
```

> At this point, you should be able to run `pytest` and get three passing tests.
> You should also be able to add a few messages to the DB at `localhost:8000/admin/simple_app/message/`
> You should also be able to browse to `localhost:8000/graphiql/` and run the query `{ allMessages { id, message } }`

The query `all_messages` returns a list of objects. Let's add another query
that returns just one object:

```py
# File: ./backend/simple_app/tests/test_schema.py

def test_message():
    msg = mixer.blend('simple_app.Message')
    q = schema.Query()
    res = q.resolve_messages(None, {'id': msg.pk}, None)
    assert res == msg, 'Should return the requested message'
```

To make the test pass, let's update our schema file:

```py
# File: ./backend/simple_app/schema.py

class Query(graphene.AbstractType):
    message = graphene.Field(MessageType, id=graphene.Int())

    def resolve_message(self, args, context, info):
        return models.Message.objects.get(pk=args.get('id'))

    [...]
```

> At this point you should be able to run `pytest` and see four passing tests
> You should also be able to browse to `graphiql` and run the query `{ message(id:1) { id, message } }`

## <a name="add-mutation"></a>Add Mutation to GraphQL Schema

Our API is able to return items from our DB. Now it is time to allow to write
messages. Anything that changes data in GraphQL is called a "Mutation". We
want to ensure that our mutation does three things:

1. Return a 403 status if the user is not logged in
1. Return a 400 status and form errors if the user does not provide a message
1. Return a 200 status and the newly created message if everything is OK

```py
# File: ./backend/simple_app/tests/test_schema.py

from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory

def test_create_message_mutation():
    user = mixer.blend('auth.User')
    mut = schema.CreateMessageMutation()

    data = {'message': 'Test'}
    req = RequestFactory().get('/')
    req.user = AnonymousUser()
    res = mut.mutate(None, data, req, None)
    assert res.status == 403, 'Should return 403 if user is not logged in'

    req.user = user
    res = mut.mutate(None, {}, req, None)
    assert res.status == 400, 'Should return 400 if there are form errors'
    assert 'message' in res.formErrors, (
        'Should have form error for message field')

    req.user = user
    res = mut.mutate(None, {'message': 'Test'}, req, None)
    assert res.status == 200, 'Should return 400 if there are form errors'
    assert res.message.pk == 1, 'Should create new message'
```

With these tests in place, we can implement the actual mutation:

```py
# File: ./backend/simple_app/schema.py

import json

class CreateMessageMutation(graphene.Mutation):
    class Input:
        message = graphene.String()

    status = graphene.Int()
    formErrors = graphene.String()
    message = graphene.Field(MessageType)

    @staticmethod
    def mutate(root, args, context, info):
        if not context.user.is_authenticated():
            return CreateMessageMutation(status=403)
        message = args.get('message', '').strip()
        # Here we would usually use Django forms to validate the input
        if not message:
            return CreateMessageMutation(
                status=400,
                formErrors=json.dumps(
                    {'message': ['Please enter a message.']}))
        obj = models.Message.objects.create(
            user=context.user, message=message
        )
        return CreateMessageMutation(status=200, message=obj)


class Mutation(graphene.AbstractType):
    create_message = CreateMessageMutation.Field()
```

This new `Mutation` class is currently not hooked up in our main `schema.py`
file, so let's add that:

```py
# File: ./backend/backend/schema.py

class Mutations(
    simple_app.schema.Mutation,
    graphene.ObjectType,
):
    pass

[...]

schema = graphene.Schema(query=Queries, mutation=Mutations)
```

> At this point you should be able to run `pytest` and get five passing tests.
> You should also be able to browse to `graphiql` and run this mutation:

```graphql
mutation {
  createMessage(message: "Test") {
    status,
    formErrors,
    message {
      id
    }
  }
}
```

## <a name="add-jwt"></a>Add JWT-Authentication to Django

One of the most common things that every web application needs is
authentication. During my research I found [django-graph-auth](https://github.com/morgante/django-graph-auth), which is
based on Django Rest Frameworks JWT plugin. There is als [pyjwt](https://pyjwt.readthedocs.io/en/latest/), which would allow you to
implement your own endpoints.

I didn't have the time to evaluate `django-graph-auth` yet, and I didn't have
the confidence to run my own implementation. For that reason, I chose the
practical approach and used what is tried and tested by a very large user base
and added Django Rest Framework and
[django-rest-framework-jwt](https://github.com/GetBlimp/django-rest-framework-jwt)
to the project.

We will also need to install [django-cors-headers](https://github.com/ottoyiu/django-cors-headers) because
during local development, the backend and the frontend are served from
different ports, so we need to enable to accept requests from all origins.

```bash
cd ~/Projects/django-graphql-apollo-react-demo/src/backend
pip install djangorestframework
pip install djangorestframework-jwt
pip install django-cors-headers
```

Now we need to update our Django settings:

```py
# File: ./backend/backend/settings.py**

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'graphene_django',
    'simple_app',
]

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_jwt.authentication.JSONWebTokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ),
}

CORS_ORIGIN_ALLOW_ALL = True
```

Now that Rest Framework is configured, we need to add a few URLs:

```py
# File: ./backend/backend/urls.py

[...]
from rest_framework_jwt.views import obtain_jwt_token
from rest_framework_jwt.views import refresh_jwt_token
from rest_framework_jwt.views import verify_jwt_token


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^graphiql', csrf_exempt(GraphQLView.as_view(graphiql=True))),
    url(r'^gql', csrf_exempt(GraphQLView.as_view(batch=True))),
    url(r'^api-token-auth/', obtain_jwt_token),
    url(r'^api-token-refresh/', refresh_jwt_token),
    url(r'^api-token-verify/', verify_jwt_token),
]
```

> At this point you should be able to get a token by sending this request: `curl -X POST -d "username=admin&password=test1234" http://localhost:8000/api-token-auth/`

# Part 2: The Frontend

In Part 1, we create a Django backend that serves a GraphQL API. In this part
we will create a ReactJS frontend that consumes that API.

## <a name="create-new-react-project"></a>Create a new React Project

Facebook has released a wonderful command line tool that kickstarts a new
ReactJS project with a powerful webpack configuration. Let's use that:

```bash
cd ~/Projects/django-graphql-apollo-react-demo/src
npm install -g create-react-app
create-react-app frontend
cd frontend
yarn start
```

> At this point you should be able to run `yarn start` and the new ReactJS project should open up in a browser tab

## Add ReactRouter to React](#add-react-router)

```bash
cd ~/Projects/django-graphql-apollo-react-demo/src/frontend
yarn add react-router-dom
```

First, we need to replace the example code in `App.js` with our own code:

```jsx
import React, { Component } from 'react'
import { BrowserRouter as Router, Route, Switch, Link } from 'react-router-dom'
import CreateView from './views/CreateView'
import DetailView from './views/DetailView'
import ListView from './views/ListView'
import LoginView from './views/LoginView'
import LogoutView from './views/LogoutView'

class App extends Component {
  render() {
    return (
      <Router>
        <div>
          <ul>
            <li><Link to="/">Home</Link></li>
            <li><Link to="/messages/create/">Create Message</Link></li>
            <li><Link to="/login/">Login</Link></li>
            <li><Link to="/logout/">Logout</Link></li>
          </ul>
          <Route exact path="/" component={ListView} />
          <Route exact path="/login/" component={LoginView} />
          <Route exact path="/logout/" component={LogoutView} />
          <Switch>
            <Route path="/messages/create/" component={CreateView} />
            <Route path="/messages/:id/" component={DetailView} />
          </Switch>
        </div>
      </Router>
    )
  }
}

export default App
```

You will notice that we imported a bunch of views that don't yet exist. Let's
create them:

```bash
cd ~/Projects/django-graphql-apollo-react-demo/src/frontend/src/
mkdir views
touch views/CreateView.js
touch views/DetailView.js
touch views/ListView.js
touch views/LoginView.js
touch views/LogoutView.js
```

Now fill each view with the following placeholder code:

```jsx
// File: ./frontend/src/views/ListView.js

import React from 'react'

export default class ListView extends React.Component {
  render() {
    return <div>ListView</div>
  }
}
```

> At this point you should be able to run `yarn start` and see your projects. When you click at the links, the corresponding views should be rendered and the URL should change.
