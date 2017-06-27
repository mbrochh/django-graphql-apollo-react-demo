import pytest
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from mixer.backend.django import mixer
from graphql_relay.node.node import to_global_id

from .. import schema


pytestmark = pytest.mark.django_db


def test_user_type():
    instance = schema.UserType()
    assert instance


def test_message_type():
    instance = schema.MessageType()
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


def test_resolve_message():
    msg = mixer.blend('simple_app.Message')
    q = schema.Query()
    id = to_global_id('MessageType', msg.pk)
    res = q.resolve_message({'id': id}, None, None)
    assert res == msg, 'Should return the requested message'


def test_resolve_all_messages():
    mixer.blend('simple_app.Message')
    mixer.blend('simple_app.Message')
    q = schema.Query()
    res = q.resolve_all_messages(None, None, None)
    assert res.count() == 2, 'Should return all messages'


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
