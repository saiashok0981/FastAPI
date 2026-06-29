import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta, timezone

from app import app
from database import get_db
from models import User, URL, Click
from routers.auth import get_current_user, get_optional_current_user

client = TestClient(app)

# --- The Pytest Fixture ---
@pytest.fixture
def mock_session():
    """
    A pytest fixture that mocks the FastAPI database dependency, 
    injects the mocked session into the test, and cleans up afterwards.
    """
    session = MagicMock()
    
    # Simulate db.refresh() populating the ID and default timestamps
    def mock_refresh(instance):
        instance.id = 99
        if hasattr(instance, "created_at") and getattr(instance, "created_at") is None:
            instance.created_at = datetime.now(timezone.utc).replace(tzinfo=None)
        if hasattr(instance, "timestamp") and getattr(instance, "timestamp") is None:
            instance.timestamp = datetime.now(timezone.utc).replace(tzinfo=None)
        
    session.refresh.side_effect = mock_refresh
    
    # Configure query chain to return None by default so lookups (like duplicate code checks) do not trigger errors
    session.query.return_value.filter.return_value.first.return_value = None
    session.query.return_value.filter.return_value.all.return_value = []
    session.query.return_value.offset.return_value.limit.return_value.all.return_value = []
    
    # Override database session dependency
    app.dependency_overrides[get_db] = lambda: session
    
    yield session 
    
    # Clean up overrides
    app.dependency_overrides.clear()


# --- Unit Tests ---

def test_create_url_with_mocked_db(mock_session: MagicMock):
    """Test successful URL creation using the fixture"""
    response = client.post(
        "/urls",
        json={"original_url": "https://www.example.com", "short_code": "ex123"}
    )
    
    # Assert API response
    assert response.status_code == 200
    assert response.json() == {
        "message": "URL created successfully",
        "id": 99
    }
    
    # Verify mock session interaction
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()

    # Verify original URL and short code values
    added_url_object = mock_session.add.call_args[0][0]
    assert added_url_object.original_url == "https://www.example.com"
    assert added_url_object.short_code == "ex123"


def test_create_url_validation_error_no_db_call(mock_session: MagicMock):
    """Test that if Pydantic validation fails, the DB is never called."""
    # Missing original_url in request body
    response = client.post(
        "/urls",
        json={"short_code": "ex123"}
    )
    
    assert response.status_code == 422
    
    # Ensure database mock was never touched
    mock_session.add.assert_not_called()
    mock_session.commit.assert_not_called()


def test_redirect_to_original_url(mock_session: MagicMock):
    """Test successful redirection mapping and background analytics logging."""
    fake_url = URL(id=10, original_url="https://google.com", short_code="gog123", expires_at=None)
    
    # Configure mock session to return our fake URL record when queried
    mock_session.query.return_value.filter.return_value.first.return_value = fake_url
    
    response = client.get("/gog123", follow_redirects=False)
    
    assert response.status_code == 307
    assert response.headers["location"] == "https://google.com"


def test_redirect_to_expired_url(mock_session: MagicMock):
    """Test that visiting an expired shortened link raises a 410 Gone."""
    expired_time = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=1)
    fake_url = URL(id=10, original_url="https://expired.com", short_code="exp1", expires_at=expired_time)
    
    mock_session.query.return_value.filter.return_value.first.return_value = fake_url
    
    response = client.get("/exp1")
    assert response.status_code == 410
    assert response.json()["detail"] == "This shortened URL has expired"


def test_redirect_url_not_found(mock_session: MagicMock):
    """Test redirection request for a non-existent short code raises 404."""
    mock_session.query.return_value.filter.return_value.first.return_value = None
    
    response = client.get("/nonexistent")
    assert response.status_code == 404
    assert response.json()["detail"] == "Shortened URL not found"


def test_get_url_qr_code(mock_session: MagicMock):
    """Test QR code generation output for a valid short code."""
    fake_url = URL(id=10, original_url="https://google.com", short_code="gog123", expires_at=None)
    mock_session.query.return_value.filter.return_value.first.return_value = fake_url
    
    response = client.get("/urls/gog123/qr")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert len(response.content) > 0


def test_health_check_healthy(mock_session: MagicMock):
    """Test health check route returns healthy details when DB connection works."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "database": "connected"}


def test_health_check_unhealthy(mock_session: MagicMock):
    """Test health check route returns 503 when DB connection throws."""
    mock_session.execute.side_effect = Exception("DB Connection Failed")
    
    response = client.get("/health")
    assert response.status_code == 503
    assert "Database connection failed" in response.json()["detail"]


def test_user_registration(mock_session: MagicMock):
    """Test registering a new user."""
    response = client.post(
        "/auth/register",
        json={"username": "testuser", "email": "test@example.com", "password": "securepassword"}
    )
    assert response.status_code == 201
    assert response.json()["username"] == "testuser"
    assert response.json()["email"] == "test@example.com"
    assert "id" in response.json()


def test_user_registration_duplicate(mock_session: MagicMock):
    """Test registration block on duplicate username."""
    existing_user = User(id=1, username="testuser", email="test@example.com", hashed_password="hashed")
    mock_session.query.return_value.filter.return_value.first.return_value = existing_user
    
    response = client.post(
        "/auth/register",
        json={"username": "testuser", "email": "other@example.com", "password": "password"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Username already registered"


def test_user_login_success(mock_session: MagicMock):
    """Test user login returns a valid JWT access token."""
    from services.auth import hash_password
    pwd_hash = hash_password("mypassword")
    fake_user = User(id=1, username="loginuser", email="login@example.com", hashed_password=pwd_hash)
    
    mock_session.query.return_value.filter.return_value.first.return_value = fake_user
    
    response = client.post(
        "/auth/login",
        data={"username": "loginuser", "password": "mypassword"}
    )
    assert response.status_code == 200
    json_data = response.json()
    assert "access_token" in json_data
    assert json_data["token_type"] == "bearer"


def test_user_login_failure(mock_session: MagicMock):
    """Test login failure with invalid password."""
    from services.auth import hash_password
    pwd_hash = hash_password("mypassword")
    fake_user = User(id=1, username="loginuser", email="login@example.com", hashed_password=pwd_hash)
    
    mock_session.query.return_value.filter.return_value.first.return_value = fake_user
    
    response = client.post(
        "/auth/login",
        data={"username": "loginuser", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"


def test_authenticated_profile(mock_session: MagicMock):
    """Test getting profile information for an authenticated user."""
    fake_user = User(id=42, username="authuser", email="auth@example.com", created_at=datetime.now(timezone.utc).replace(tzinfo=None))
    app.dependency_overrides[get_current_user] = lambda: fake_user
    
    response = client.get("/auth/me")
    assert response.status_code == 200
    assert response.json()["username"] == "authuser"
    assert response.json()["id"] == 42


def test_analytics_and_urls_management(mock_session: MagicMock):
    """Test authenticated URL queries, updates, deletes, and analytics views."""
    fake_user = User(id=42, username="owneruser", email="owner@example.com")
    app.dependency_overrides[get_current_user] = lambda: fake_user
    app.dependency_overrides[get_optional_current_user] = lambda: fake_user
    
    fake_url = URL(
        id=88,
        original_url="https://someplace.com",
        short_code="some88",
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        expires_at=None,
        owner_id=fake_user.id
    )
    
    # 1. Test create URL as authenticated user
    mock_session.query.return_value.filter.return_value.first.return_value = None
    response = client.post(
        "/urls",
        json={"original_url": "https://someplace.com", "short_code": "some88"}
    )
    assert response.status_code == 200
    
    # 2. Mock GET list of user URLs
    mock_session.query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = [fake_url]
    response = client.get("/urls")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["short_code"] == "some88"
    
    # Reset mock queries to return fake_url on detail lookups
    mock_session.query.return_value.filter.return_value.first.return_value = fake_url
    
    # 3. Test update URL
    response = client.put(
        "/urls/some88",
        json={"original_url": "https://newplace.com"}
    )
    assert response.status_code == 200
    
    # 4. Test read analytics
    # Configure mock for click aggregate calculations
    mock_session.query.return_value.filter.return_value.scalar.return_value = 5  # total clicks count
    mock_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
        Click(id=1, url_id=88, timestamp=datetime.now(timezone.utc).replace(tzinfo=None), ip_address="127.0.0.1", user_agent="Mozilla Firefox", referrer="Direct")
    ]
    
    response = client.get("/urls/some88/analytics")
    assert response.status_code == 200
    assert response.json()["click_count"] == 5
    assert len(response.json()["clicks"]) == 1
    
    # 5. Test delete URL
    response = client.delete("/urls/some88")
    assert response.status_code == 200
    assert response.json()["message"] == "URL deleted successfully"