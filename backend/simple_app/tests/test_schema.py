import pytest
from mixer.backend.django import mixer

from .. import schema


pytestmark = pytest.mark.django_db


def test_message_type():
    instance = schema.MessageType()
    assert instance


def test_message():
    msg = mixer.blend('simple_app.Message')
    q = schema.Query()
    res = q.resolve_message({'id': msg.pk}, None, None)
    assert res == msg, 'Should return the requested message'


def test_all_messages():
    mixer.blend('simple_app.Message')
    mixer.blend('simple_app.Message')
    q = schema.Query()
    res = q.resolve_all_messages(None, None, None)
    assert res.count() == 2, 'Should return all messages'
