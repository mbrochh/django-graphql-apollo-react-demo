# A Django + GraphQL + Apollo + React Stack Demo

This repo contains the code shown at the [Singapore Djangonauts June 2017 Meetup](https://www.meetup.com/Singapore-Djangonauts/events/240608776/)

A video of the workshop can be found on engineers.sg:

[Part 1](https://engineers.sg/video/june-2017-meetup-django-graphql-reactjs-apollo-workshop-singapore-djangonauts-part-1--1856)
[Part 2](https://engineers.sg/video/june-2017-meetup-django-graphql-reactjs-apollo-workshop-singapore-djangonauts-part-2--1857).

The sound in the video is messed up. I'm looking for a venue and an audience
to record the talk one more time :(

This README was basically the "slides" for the workshop, so if you want to
learn as well, just keep on reading!

In this workshop, we will address the following topics:

## [Part 1: The Backend](#part1)

1. [Create a new Django Project](#create-new-django-project)
1. [Create a Simple Django App](#create-simple-app)
1. [Add GraphQL to Django](#add-graphql-to-django)
1. [Add Message-DjangoObjectType to GraphQL Schema](#add-django-object-type)
1. [Add Mutation to GraphQL Schema](#add-mutation)
1. [Add JWT-Authentication to Django](#add-jwt)

## [Part 2: The Frontend](#part2)

1. [Create a new React Project](#create-new-react-project)
1. [Add ReactRouter to React](#add-react-router)
1. [Add Apollo to React](#add-apollo)
1. [Add Query with Variables for DetailView](#add-query-with-variables)
1. [Add Token Middleware for Authentication](#add-token-middleware)
1. [Add Login / Logout Views](#add-login-logout-views)
1. [Add Mutation for CreateView](#add-mutation-for-create-view)
1. [Show Form Errors on CreateView](#show-form-errors)
1. [Add Filtering to ListView](#add-filtering)
1. [Add Pagination to ListView](#add-pagination)
1. [Add Cache Invalidation](#cache-invalidation)

## Part 3: Advanced Topics

I am planning to keep this repo alive and add some more best practices as I
figure them out at work. Some ideas:

1. Create a higher order component "LoginRequired" to protect views
1. Create a higher order component "NetworkStatus" to allow refetching of
   failed queries after the network was down
1. Don't refresh the entire page after login/logout
1. Create Python decorator like "login_required" for mutations and resolvers
1. Some examples for real cache invalidation
1. Hosting (EC2 instance for Django, S3 bucket for frontend files)

If you have more ideas, please add them in the issue tracker!

Before you start, you should read a little bit about [GraphQL](http://graphql.org/learn/) and [Apollo](http://dev.apollodata.com/react/) and [python-graphene](http://docs.graphene-python.org/projects/django/en/latest/).

If you have basic understanding of Python, Django, JavaScript and ReactJS, you
should be able to follow this tutorial and copy and paste the code snippets
shown below and hopefully it will all work out nicely.

The tutorial should give you a feeling for the necessary steps involved when
building a web application with Django, GraphQL and ReactJS.

If you find typos or encounter other issues, please report them at the issue
tracker.

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

Since we have now a Django project with a model, we can start thinking about
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


def test_resolve_all_messages():
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
        interfaces = (graphene.Node, )


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
> You should also be able to browse to `localhost:8000/graphiql/` and run the query:

```graphql
{
  allMessages {
    id, message
  }
}
```

The query `all_messages` returns a list of objects. Let's add another query
that returns just one object:

```py
# File: ./backend/simple_app/tests/test_schema.py

from graphql_relay.node.node import to_global_id

def test_resolve_message():
    msg = mixer.blend('simple_app.Message')
    q = schema.Query()
    id = to_global_id('MessageType', msg.pk)
    res = q.resolve_messages({'id': id}, None, None)
    assert res == msg, 'Should return the requested message'
```

To make the test pass, let's update our schema file:

```py
# File: ./backend/simple_app/schema.py

from graphql_relay.node.node import from_global_id

class Query(graphene.AbstractType):
    message = graphene.Field(MessageType, id=graphene.ID())

    def resolve_message(self, args, context, info):
        rid = from_global_id(args.get('id'))
        # rid is a tuple: ('MessageType', '1')
        return models.Message.objects.get(pk=rid[1])

    [...]
```

> At this point you should be able to run `pytest` and see four passing tests
> You should also be able to browse to `graphiql` and run the query `{ message(id: "TWVzc2FnZVR5cGU6MQ==") { id, message } }`

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

Now we need to update our Django settings with new settings related to the
`rest_framework` and `corsheaders` apps:

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

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
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

# <a name="part2"></a>Part 2: The Frontend

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

## <a name="add-react-router"></a>Add ReactRouter to React

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

Now fill each view with the following placeholder code, just change the class
name and text in the div to the corresponding file-name.

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

## <a name="add-apollo"></a>Add Apollo to React

We can now add Apollo to the mix. First we need to install it via yarn:

```bash
cd ~/Projects/django-graphql-apollo-react-demo/src/frontend/
yarn add react-apollo
```

Similar to react-router, we need to wrap our entire app in a higher order
component that comes with Apollo. There are four steps involved:

1. Import relevant imports from `react-apollo`
2. Create a `networkInterface` that points to the GraphQL API
3. Instantiate `ApolloClient` using our `networkInterface`
4. Wrap entire app in `<ApolloProvider>` component

```jsx
// File: ./frontend/src/App.js

[...]
import {
  ApolloProvider,
  ApolloClient,
  createBatchingNetworkInterface,
} from 'react-apollo'
[...]

const networkInterface = createBatchingNetworkInterface({
  uri: 'http://localhost:8000/gql',
  batchInterval: 10,
  opts: {
    credentials: 'same-origin',
  },
})

const client = new ApolloClient({
  networkInterface: networkInterface,
})

class App extends Component {
  render() {
    return (
      <ApolloProvider client={client}>
        [...]
      </ApolloProvider>
    )
  }
}

export default App
```

In order to test if our Apollo installation is working properly, let's implement
our ListView. There are some notable steps involved, too:

1. Import relevant imports from `react-apollo`
2. Create a `query` variable with the GraphQL query
3. Use `this.props.data.loading` to render "Loading" while query is in flight
4. Use `this.props.data.allMessages` to render all messages
5. Wrap `ListView` in `graphql` decorator

```jsx
// File: ./frontend/src/views/ListView.js

import React from 'react'
import { Link } from 'react-router-dom'
import { gql, graphql } from 'react-apollo'

const query = gql`
{
  allMessages {
    id, message
  }
}
`

class ListView extends React.Component {
  render() {
    let { data } = this.props
    if (data.loading || !data.allMessages) {
      return <div>Loading...</div>
    }
    return (
      <div>
        {data.allMessages.map(item => (
          <p key={item.id}>
            <Link to={`/messages/${item.id}/`}>
              {item.message}
            </Link>
          </p>
        ))}
      </div>
    )
  }
}

ListView = graphql(query)(ListView)
export default ListView
```

> At this point, you should be able to browse to `localhost:3000/` and see a list of messages. If you don't have any message in your database yet, add some at `localhost:8000/admin/`

## <a name="add-query-with-variables"></a>Add Query with Variables for DetailView

We have now learned how to attach a simple query to a component, but what about
queries that need some dynamic values. For example, when we click into the
detail view of an item, we can't just query `allMessages`, we need to query
the message with a certain ID. Let's implement that in our DetailView. The
steps are slightly different here:

1. Our query is a name query (same name as component class name)
2. The named query defines a variable `$id`
3. We pass in `queryOptions` into the `graphql` decorator
4. `queryOptions` has a field `options` which is an anonymous function that
   accepts `props` as a parameter.
5. Thanks to react-router, we have access to `props.match.params.id` (id is the
   `/:id/` part of the path of our Route)

```jsx
// File: ./frontend/src/views/DetailView.js

import React from 'react'
import { gql, graphql } from 'react-apollo'

const query = gql`
query DetailView($id: ID!) {
  message(id: $id) {
    id, creationDate, message
  }
}
`

class DetailView extends React.Component {
  render() {
    let { data } = this.props
    if (data.loading || !data.message) {
      return <div>Loading...</div>
    }
    return (
      <div>
        <h1>Message {data.message.id}</h1>
        <p>{data.message.creationDate}</p>
        <p>{data.message.message}</p>
      </div>
    )
  }
}

const queryOptions = {
  options: props => ({
    variables: {
      id: props.match.params.id,
    },
  }),
}

DetailView = graphql(query, queryOptions)(DetailView)
export default DetailView
```

> At this point you should be able to browse to the list view and click at an item and see the DetailView with correct data.

## <a name="add-token-middleware"></a>Add Token Middleware for Authentication

A very common problem is "How to do authentication?". We will use JWT, so on
the frontend, we need a way to make sure that we send the current token with
every request. On the backend, we need to make sure, to attach the current user
to the request, if a valid token has been sent.

Let's start with the server:

```bash
cd ~/Projects/django-graphql-apollo-react-demo/src/backend/backend/
touch middleware.py
```

First, we will create a new middleware that attaches the current user to the
request, if a valid token is given. We are standing on the shoulder of giants
and re-use the implementation from django-rest-framework-jwt here:

```py
# File: ./backend/backend/middleware.py

from rest_framework_jwt.authentication import JSONWebTokenAuthentication


class JWTMiddleware(object):
    def process_view(self, request, view_func, view_args, view_kwargs):
        token = request.META.get('HTTP_AUTHORIZATION', '')
        if not token.startswith('JWT'):
            return
        jwt_auth = JSONWebTokenAuthentication()
        auth = None
        try:
            auth = jwt_auth.authenticate(request)
        except Exception:
            return
        request.user = auth[0]
```

Next, we need to add this new middleware to our settings. Note: For the sake
of simplicity, I'm setting `JWT_VERIFY_EXPIRATION = False`, which means that
the token will never expire. In the real world, you will want to set some
expiry time like two weeks here and then in your frontend store the token
creation time together with your token in localStorage and whenever the token
is close to the expiry date, call the `api-token-refresh` endpoint to get a
new token.

```py
# File: ./backend/backend/settings.py

JWT_VERIFY_EXPIRATION = False

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'backend.middleware.JWTMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
```

Next, we need to update our schema so that we can query the current user. For
sake of simplicity, I'm putting this new endpoint into the `simple_app`. In
reality I would create a new app `user_profile` and add another schema file
in that new app. As usual, we start with our tests:

```py
# File: ./backend/simple_app/tests/test_schema.py

def test_user_type():
    instance = schema.UserType()
    assert instance


def test_resolve_current_user():
    q = schema.Query()
    req = RequestFactory().get('/')
    req.user = AnonymousUser()
    res = q.resolve_current_user(None, req, None)
    assert res is None, 'Should return None if user is not authenticated'

    user = mixer.blend('auth.User')
    req.user = user
    res = q.resolve_current_user(None, req, None)
    assert res == user, 'Should return the current user if is authenticated'
```

Now we can write our implementation:

```py
# File: ./backend/simple_app/schema.py
[...]
from django.contrib.auth.models import User
[...]


class UserType(DjangoObjectType):
    class Meta:
        model = User

[...]

class Query(graphene.AbstractType):
    current_user = graphene.Field(UserType)

    def resolve_current_user(self, args, context, info):
        if not context.user.is_authenticated():
            return None
        return context.user

    [...]
```

> At this point, you shold be able to browse to `localhost:8000/graphiql` and run the following query: `{ currentUser { id } }`. If you were previously logged in to the Django admin, it should return your admin user as the current user.

Finally, we need to make sure that every request has the token included. Apollo
has the option to add middlewares to manipulate the requests that are being
sent to the GraphQL API. We will try to read the JWT token from the
`localStorage` and attach it to the request headers:

```jsx
// File: ./frontend/src/App.js

[...]

const networkInterface = createBatchingNetworkInterface({
  uri: 'http://localhost:8000/gql/',
  batchInterval: 10,
  opts: {
    credentials: 'same-origin',
  },
})

// Add this new part:
networkInterface.use([
  {
    applyBatchMiddleware(req, next) {
      if (!req.options.headers) {
        req.options.headers = {}
      }

      const token = localStorage.getItem('token')
        ? localStorage.getItem('token')
        : null
      req.options.headers['authorization'] = `JWT ${token}`
      next()
    },
  },
])

const client = new ApolloClient({
  networkInterface: networkInterface,
})

[...]
```

Right now, it's a bit hard to test in our frontend if all this is working,
so let's use the `currentUser` endpoint in our `CreateView` and if the user
is not logged in, let's redirect to the `/login/` view:

```jsx
// File: ./frontend/src/views/CreateView.js

import React from 'react'
import { gql, graphql } from 'react-apollo'

const query = gql`
{
  currentUser {
    id
  }
}
`

class CreateView extends React.Component {
  componentWillUpdate(nextProps) {
    if (!nextProps.data.loading && nextProps.data.currentUser === null) {
      window.location.replace('/login/')
    }
  }

  render() {
    let { data } = this.props
    if (data.loading) {
      return <div>Loading...</div>
    }
    return <div>CreateView</div>
  }
}

CreateView = graphql(query)(CreateView)
export default CreateView
```

> At this point, you should be able to click at the `Create Message` link and be redirected to the `/login/` view.

## <a name="add-login-logout-views"></a>Add Login / Logout Views

Now we want to be able to actually login and receive a valid JWT token, so
lets implement the LoginView. Here are some notable steps:

1. We use the `fetch` api to send the request to the `api-token-auth` endpoint
1. If we provide correct username and password, we save the token to
   localStorage and refresh the page. In the real world, you would want to
   check if there is a `?next` parameter in the URL so that you can redirect
   back to the URL that triggered the login view
1. We use `let data = new FormData(this.form)` to collect all current values
   from all input elements that are inside the form
1. With a neat little React trick `<form ref={ref => this.form = ref}>` we are
   able to get a reference to our form anywhere in our code via `this.form`

```jsx
// File: ./frontend/src/views/LoginView.js

import React from 'react'

export default class LoginView extends React.Component {
  handleSubmit(e) {
    e.preventDefault()
    let data = new FormData(this.form)
    fetch('http://localhost:8000/api-token-auth/', {
      method: 'POST',
      body: data,
    })
      .then(res => {
        res.json().then(res => {
          if (res.token) {
            localStorage.setItem('token', res.token)
            window.location.replace('/')
          }
        })
      })
      .catch(err => {
        console.log('Network error')
      })
  }

  render() {
    return (
      <div>
        <h1>LoginView</h1>
        <form
          ref={ref => (this.form = ref)}
          onSubmit={e => this.handleSubmit(e)}
        >
          <div>
            <label>Username:</label>
            <input type="text" name="username" />
          </div>
          <div>
            <label>Password:</label>
            <input type="password" name="password" />
          </div>
          <button type="submit">Login</button>
        </form>
      </div>
    )
  }
}
```

> At this point you should be able to click at `Login`, provide username and password, then go back to `Create Message`.

When we are at it, let's also create our `LogoutView`. That one is pretty
simple, we just remove the token from localStorage and trigger a page refresh.

```jsx
import React from 'react'

export default class LogoutView extends React.Component {
  handleClick() {
    localStorage.removeItem('token')
    window.location.replace('/')
  }

  render() {
    return (
      <div>
        <h1>Logout</h1>
        <button onClick={() => this.handleClick()}>Logout</button>
      </div>
    )
  }
}
```

> At this point you should be able to login, browse to `Create Message` view and to logout again.

## <a name="add-mutation-for-create-view"></a>Add Mutation for CreateView

Since we are now able to login and visit the CreateView, it is time to add a
mutation to the CreateView that allows us to write new messages into the DB.

Notable steps involved:

1. Create a `const mutation` that is named after the class and needs one variable
1. Create a `submitHandler` that calls `this.props.mutate` and provides the
   required variable
1. Wrap the class in another `graphql` decorator so that the mutation gets
   registered and is available via `this.props.mutate`

```jsx
// File: ./frontend/src/views/CreateView.js

import React from 'react'
import { gql, graphql } from 'react-apollo'

// This is new:
const mutation = gql`
mutation CreateView($message: String!) {
  createMessage(message: $message) {
    status,
    formErrors,
    message {
      id
    }
  }
}
`

const query = gql`
{
  currentUser {
    id
  }
}
`

class CreateView extends React.Component {
  componentWillUpdate(nextProps) {
    if (!nextProps.data.loading && nextProps.data.currentUser === null) {
      window.location.replace('/login/')
    }
  }

  // This is new:
  handleSubmit(e) {
    e.preventDefault()
    let data = new FormData(this.form)
    this.props
      .mutate({ variables: { message: data.get('message') } })
      .then(res => {
        if (res.status === 200) {
          window.location.replace('/')
        }
      })
      .catch(err => {
        console.log('Network error')
      })
  }

  render() {
    // This is new:
    let { data } = this.props
    if (data.loading || data.currentUser === null) {
      return <div>Loading...</div>
    }
    return (
      <div>
        <h1>Create Message</h1>
        <form
          ref={ref => (this.form = ref)}
          onSubmit={e => this.handleSubmit(e)}
        >
          <div>
            <label>Message:</label>
            <textarea name="message" />
          </div>
          <button type="submit">Submit Message</button>
        </form>
      </div>
    )
  }
}

CreateView = graphql(query)(CreateView)
CreateView = graphql(mutation)(CreateView)  // <-- This is new
export default CreateView
```

> At this point you should be able to submit a new message and then see it on the ListView

## <a name="show-form-errors"></a>Show Form Errors on CreateView

What if the user enters an empty message? We would like to show some form
errors. Our schema actually already has this validation in place:

```py
def mutate(root, args, context, info):
    [...]
    message = args.get('message', '').strip()
    if not message:
        return CreateMessageMutation(
            status=400,
            formErrors=json.dumps(
                {'message': ['Please enter a message.']}))
    [...]
```

Note: In the real world you would use a Django form for this and do something
like this:

```py
def mutate(root, args, context, info):
  [...]
  form = CreateMessageForm(data=args)
  if not form.is_valid():
      return CreateMessageMutation(
        status=400, formErrors=json.dumps(form.errors))
```

So validation is already in place, let's update our CreateView so that it
displays the form errors:

```jsx
// File: ./frontend/src/views/CreateView.js

  // Add this constructor:
  constructor(props) {
    super(props)
    this.state = {formErrors: null}
  }

  // Update this function:
  handleSubmit(e) {
    e.preventDefault()
    let data = new FormData(this.form)
    this.props
      .mutate({ variables: { message: data.get('message') } })
      .then(res => {
        if (res.data.createMessage.status === 200) {
          window.location.replace('/')
        }
        if (res.data.createMessage.status === 400) {
          this.setState({
            formErrors: JSON.parse(res.data.createMessage.formErrors),
          })
        }
      })
      .catch(err => {
        console.log('Network error')
      })
  }

  [...]

  // Update this part of the render() function:
  <div>
    <label>Message:</label>
    <textarea name="message" />
    {this.state.formErrors &&
      this.state.formErrors.message &&
      <p>Error: {this.state.formErrors.message}</p>}
  </div>
```

> At this point you should be able to submit an empty message and see a form error.

## <a name="add-filtering"></a>Add Filtering to ListView

So far, our `allMessages` query always returns all messages. It would be nice
if we could add a search bar to our app and filter messages by text.
graphene-django has some integration with [django-filter](https://github.com/carltongibson/django-filter), so this task
can be solved easily.

Note: You can learn more about filtering [here](http://docs.graphene-python.org/projects/django/en/latest/filtering/).

```bash
pip install django-filter
```

```py
# File: ./backend/simple_app/schema.py
[...]
from graphene_django.filter.fields import DjangoFilterConnectionField
[...]

class MessageType(DjangoObjectType):
    class Meta:
        model = models.Message
        filter_fields = {'message': ['icontains']}
        interfaces = (graphene.Node, )
[...]

class Query(graphene.AbstractType):
    [...]
    all_messages = DjangoFilterConnectionField(MessageType)
```

> At this point you should be able to run the following query:

```graphql
{
  allMessages(message_Icontains: "Te") {
    edges {
      node {
        id, message
      }
    }
  }
}
```

Let's update our ListView and add a search field. We will use the `query-string`
module to parse the query string in the URL (i.e. `?search=foo`).

```bash
cd ~/Projects/django-graphql-apollo-react-demo/src/frontend/
yarn add query-string
```

Notable steps to be taken in the ListView:

1. Import the new `queryString` module
1. Change the `const query` so that it can take variables (`$search`)
1. Add a `handleSearchSubmit` handler that changes the URL via
   `this.props.history.push` (thanks to react-router)
1. Add `queryOptions` and pass in the `search` variable into the query from the
   props (`props.location.search`), if available

```jsx
// File: ./frontend/src/views/ListView.js

import React from 'react'
import { Link } from 'react-router-dom'
import { gql, graphql } from 'react-apollo'
import queryString from 'query-string'

const query = gql`
query ListViewSearch($search: String) {
  allMessages(message_Icontains: $search) {
    edges {
      node {
        id, message
      }
    }
  }
}
`

class ListView extends React.Component {
  handleSearchSubmit(e) {
    e.preventDefault()
    let data = new FormData(this.form)
    let query = `?search=${data.get('search')}`
    this.props.history.push(`/${query}`)
  }

  render() {
    let { data } = this.props
    if (data.loading || !data.allMessages) {
      return <div>Loading...</div>
    }
    return (
      <div>
        <form
          ref={ref => (this.form = ref)}
          onSubmit={e => this.handleSearchSubmit(e)}
        >
          <input type="text" name="search" />
          <button type="submit">Search</button>
        </form>
        {data.allMessages.edges.map(item => (
          <p key={item.node.id}>
            <Link to={`/messages/${item.node.id}/`}>
              {item.node.message}
            </Link>
          </p>
        ))}
      </div>
    )
  }
}

const queryOptions = {
  options: props => ({
    variables: {
      search: queryString.parse(props.location.search).search,
    },
  }),
}

ListView = graphql(query, queryOptions)(ListView)
export default ListView
```

> At this point you should be able to submit searches and see filtered results

## <a name="add-pagination"></a>Add Pagination to ListView

Another very common use-case is pagination and/or endless scrolling.
graphene-django has cursor-based pagination built-in, so let's give it a try:

In our schema, we are already using the `DjangoFilterConnectionField` for our
`allMessages` endpoint. Luckily, that has all the magic built-in, already.

Our update ListView should look as follows. Notable changes:

1. The `const query` now takes to variables (`$message`, and `$endCursor`)
1. We extended the query to also return `pageInfo` - this contains information
   about wether or not there are more pages and how to get there.
1. We added a button with a `loadMore()` handler
1. The handler calls [`data.fetchMore`](http://dev.apollodata.com/react/pagination.html#fetch-more)
1. In the `fetchMore` call, we call the same query but now with one more variable
1. We provide an `updateQuery` callback, here we have to decide what to do with
   the new data (we want to add it to the end of the list of current data)
1. In `updateQuery`, we return an object that looks like
   `this.props.data.allMessages` should look like. This will trigger a component
   re-render
1. We updated `render()` to show a `Load more...` button, as long as there are
   more items available

```jsx
// File: ./frontend/src/views/ListView.js

import React from 'react'
import { Link } from 'react-router-dom'
import { gql, graphql } from 'react-apollo'
import queryString from 'query-string'

const query = gql`
query ListViewSearch($search: String, $endCursor: String) {
  allMessages(first: 2, message_Icontains: $search, after: $endCursor) {
    edges {
      node {
        id, message
      }
    },
    pageInfo {
      hasNextPage,
      hasPreviousPage,
      startCursor,
      endCursor
    }
  }
}
`

class ListView extends React.Component {
  handleSearchSubmit(e) {
    e.preventDefault()
    let data = new FormData(this.form)
    let query = `?search=${data.get('search')}`
    this.props.history.push(`/${query}`)
  }

  loadMore() {
    let { data, location } = this.props
    data.fetchMore({
      query: query,
      variables: {
        search: queryString.parse(location.search).search,
        endCursor: data.allMessages.pageInfo.endCursor,
      },
      updateQuery: (prev, next) => {
        const newEdges = next.fetchMoreResult.allMessages.edges
        const pageInfo = next.fetchMoreResult.allMessages.pageInfo
        return {
          allMessages: {
            edges: [...prev.allMessages.edges, ...newEdges],
            pageInfo,
          },
        }
      },
    })
  }

  render() {
    let { data } = this.props
    if (data.loading || !data.allMessages) {
      return <div>Loading...</div>
    }
    return (
      <div>
        <form
          ref={ref => (this.form = ref)}
          onSubmit={e => this.handleSearchSubmit(e)}
        >
          <input type="text" name="search" />
          <button type="submit">Search</button>
        </form>
        {data.allMessages.edges.map(item => (
          <p key={item.node.id}>
            <Link to={`/messages/${item.node.id}/`}>
              {item.node.message}
            </Link>
          </p>
        ))}
        {data.allMessages.pageInfo.hasNextPage &&
          <button onClick={() => this.loadMore()}>Load more...</button>}
      </div>
    )
  }
}

const queryOptions = {
  options: props => ({
    variables: {
      search: queryString.parse(props.location.search).search,
      endCursor: null,
    },
  }),
}

ListView = graphql(query, queryOptions)(ListView)
export default ListView
```

> At this point you should be able to click the `Load more...` button and new items should appear, when there are no more items, the button should disappear. When you click in and out of items from the list, observe the incoming request in the terminal: You will see that loading the same object several times in a row does not trigger new requests, because the data is already in the cache.

## <a name="cache-invalidation"></a>Add Cache Invalidation

First of all, you might have components where you always want to fetch the data
from the network when the component is mounted. In this case, you can change
the `fetchPolicy` on the `queryOptions`:

```jsx
# File: ./frontend/src/views/DetailView.js

const queryOptions = {
  options: props => ({
    variables: {
      id: props.match.params.id,
    },
    fetchPolicy: 'network-only',
  }),
}

DetailView = graphql(query, queryOptions)(DetailView)
```

There are other ways to update the cache right after a mutation, see
[here](http://dev.apollodata.com/react/api-mutations.html#graphql-mutation-options-refetchQueries)
and
[here](http://dev.apollodata.com/react/api-mutations.html#graphql-mutation-options-update).
There is also a project called
[apollo-cache-invalidation](https://www.npmjs.com/package/apollo-cache-invalidation)
which is experimental.

I have not played around enough with cache invalidation to give any guides.
