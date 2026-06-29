import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

# Adjust these imports based on your actual folder structure
from app import app
from database import get_db

client = TestClient(app)

# --- The Pytest Fixture (Replaces the Decorator) ---
@pytest.fixture
def mock_session():
    """
    A pytest fixture that mocks the FastAPI database dependency, 
    injects the mocked session into the test, and cleans up afterwards.
    """
    # 1. Create the mock session
    session = MagicMock()
    
    # 2. Simulate db.refresh() populating the ID
    def mock_refresh(instance):
        instance.id = 99
        
    session.refresh.side_effect = mock_refresh
    
    # 3. Override the dependency in the app
    app.dependency_overrides[get_db] = lambda: session
    
    # 4. Yield the session to the test function
    yield session 
    
    # 5. Teardown: Always clean up after the test finishes!
    app.dependency_overrides.clear()


# --- The Unit Tests ---

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
        "id": 99  # Matches our fake ID from the fixture
    }
    
    # Verify the mock session was interacted with correctly
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()

    # Verify the correct data was passed to db.add()
    added_url_object = mock_session.add.call_args[0][0]
    assert added_url_object.original_url == "https://www.example.com"
    assert added_url_object.short_code == "ex123"


def test_create_url_validation_error_no_db_call(mock_session: MagicMock):
    """Test that if Pydantic validation fails, the DB is never called."""
    # Missing short_code in request body
    response = client.post(
        "/urls",
        json={"original_url": "https://www.example.com"}
    )
    
    assert response.status_code == 422
    
    # Ensure our database mock was NEVER interacted with
    mock_session.add.assert_not_called()
    mock_session.commit.assert_not_called()