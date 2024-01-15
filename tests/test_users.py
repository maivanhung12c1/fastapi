from app import schemas
from app.config import settings
import pytest
from jose import jwt
from app.config import settings
# from .database import client, session




def test_create_user(client):
    res = client.post(
        url="/users/",
        json={
            "email": "usertest@gmail.com",
            "password": "test1999"
        }
    )
    
    new_user = schemas.UserOut(**res.json())
    assert new_user.email == "usertest@gmail.com"
    assert res.status_code == 201

def test_login_user(client, test_user):
    res = client.post(
        url="/login/",
        data={
            "username": test_user["email"],
            "password": test_user["password"]
        }
    )
    
    login_res = schemas.Token(**res.json())
    payload = jwt.decode(token=login_res.access_token, key=settings.secret_key, algorithms=[settings.algorithm])
    id = payload.get("user_id")
    assert id == test_user["id"]
    assert login_res.token_type == "bearer"
    assert res.status_code == 200

@pytest.mark.parametrize("email, password, status_code", [
    ("wrongemail@gmail.com", "password123", 403),
    ("usertest@gmail.com", "wrongpassword", 403),
    ("wrongemail@gmail.com", "wrongpassword", 403),
    (None, "password123", 422),
    ("usertest@gmail.com", None, 422),
])
def test_incorrect_login(test_user, client, email, password, status_code):
    res = client.post(
        url="/login/",
        data={
            "username": email,
            "password": password
        }
    )

    assert res.status_code == status_code
    # assert res.json().get("detail") == "Invalid Credentials"
