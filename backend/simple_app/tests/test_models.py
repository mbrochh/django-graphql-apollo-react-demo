from mixer.backend.django import mixer


def test_message():
    obj = mixer.blend('simple_app.Message')
    assert obj is True
