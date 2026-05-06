import pytest
import json
from django.urls import reverse
from django.contrib.auth import get_user_model


User = get_user_model()

@pytest.fixture
def test_user(db):
    return User.objects.create_user(
        username='testuser',
        password='testpassword',
        email='testuser@example.com'
    )

@pytest.mark.django_db
def test_login_success(client, test_user):
    url = reverse('users:login')
    response = client.post(url, data=json.dumps({
        'username': 'testuser',
        'password': 'testpassword'
    }), content_type='application/json')
    assert response.status_code == 200
    assert response.json()['success'] is True

@pytest.mark.django_db
def test_login_failure(client, test_user):
    url = reverse('users:login')
    response = client.post(url, data=json.dumps({
        'username': 'testuser',
        'password': 'wrongpassword'
    }), content_type='application/json')
    assert response.status_code == 401
    assert response.json()['success'] is False

@pytest.mark.django_db
def test_register_success(client):
    url = reverse('users:register')
    response = client.post(url, data=json.dumps({
        'username': 'newuser',
        'password': 'newpassword',
        'password_confirm': 'newpassword',
        'email': 'newuser@example.com'
    }), content_type='application/json')
    assert response.status_code == 201
    assert response.json()['success'] is True

@pytest.mark.django_db
def test_register_failure(client, test_user):
    url = reverse('users:register')
    response = client.post(url, data=json.dumps({
        'username': 'testuser',
        'password': 'newpassword',
        'password_confirm': 'newpassword',
        'email': 'another@example.com'
    }), content_type='application/json')
    assert response.status_code == 400
    assert response.json()['success'] is False

@pytest.mark.django_db
def test_logout(client, test_user):
    # First, log in to get the token
    login_url = reverse('users:login')
    login_response = client.post(login_url, data=json.dumps({
        'username': 'testuser',
        'password': 'testpassword'
    }), content_type='application/json')
    token = login_response.json().get('token', {}).get('access_token')

    # Now, log out using the token
    logout_url = reverse('users:logout')
    logout_response = client.post(logout_url, HTTP_AUTHORIZATION=f'Bearer {token}')
    assert logout_response.status_code == 200
    assert logout_response.json()['success'] is True
    