import pytest

@pytest.mark.asyncio
async def test_get_me(client, test_user):
    """Тест получения информации о своем профиле"""
    response = await client.get(
        "/api/users/me",
        headers={"api-key": "test_key"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["result"] is True
    assert data["user"]["name"] == "Test User"

@pytest.mark.asyncio
async def test_create_tweet(client, test_user):
    """Тест создания нового твита"""
    tweet_data = {
        "tweet_data": "Hello World from Pytest!",
        "tweet_media_ids": []
    }
    response = await client.post(
        "/api/tweets",
        json=tweet_data,
        headers={"api-key": "test_key"}
    )
    assert response.status_code == 201
    assert response.json()["result"] is True
    assert "tweet_id" in response.json()

@pytest.mark.asyncio
async def test_invalid_api_key(client):
    response = await client.get(
        "/api/users/me",
        headers={"api-key": "wrong_key"}
    )
    assert response.status_code == 401
    data = response.json()
    # FastAPI вставляет тело ошибки в ключ 'detail'
    assert data["detail"]["result"] is False
    assert "error_message" in data["detail"]


@pytest.mark.asyncio
async def test_get_tweets_feed(client, test_user):
    """Тест получения ленты твитов"""
    response = await client.get("/api/tweets")
    assert response.status_code == 200
    data = response.json()
    assert data["result"] is True
    assert isinstance(data["tweets"], list)
