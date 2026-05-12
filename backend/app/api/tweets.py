import os
import uuid
import aiofiles
from fastapi import APIRouter, Depends, Header, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import delete
from sqlalchemy import func
from app.core.database import get_db
from app.models.base import User, Tweet, Media, likes
from app.api.users import get_current_user

# Убираем префикс /tweets, чтобы /medias работал по адресу /api/medias
router = APIRouter(tags=["tweets"])


# 1. Загрузка медиафайлов (ПО ТЗ: /api/medias)
@router.post("/medias", status_code=201)
async def upload_media(
        file: UploadFile = File(...),
        db: AsyncSession = Depends(get_db)
):
    os.makedirs("static/uploads", exist_ok=True)
    file_extension = os.path.splitext(file.filename)[1]
    file_name = f"{uuid.uuid4()}{file_extension}"
    file_path = f"static/uploads/{file_name}"

    # Асинхронное сохранение файла
    async with aiofiles.open(file_path, "wb") as buffer:
        content = await file.read()
        await buffer.write(content)

    new_media = Media(file_path=f"/static/uploads/{file_name}")
    db.add(new_media)
    await db.commit()
    await db.refresh(new_media)

    return {"result": True, "media_id": new_media.id}


# 2. Создание нового твита (ПО ТЗ: /api/tweets)
@router.post("/tweets", status_code=201)
async def create_tweet(
        data: dict,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    try:
        # Важно: берем ключ 'tweet_data', как присылает фронтенд
        new_tweet = Tweet(content=data.get('tweet_data'), author_id=user.id)
        db.add(new_tweet)
        await db.flush()

        # Привязываем медиа, если они есть
        media_ids = data.get('tweet_media_ids', [])
        if media_ids:
            result = await db.execute(select(Media).where(Media.id.in_(media_ids)))
            medias = result.scalars().all()
            for media in medias:
                media.tweet_id = new_tweet.id

        await db.commit()
        return {"result": True, "tweet_id": new_tweet.id}
    except Exception as e:
        await db.rollback()
        return {"result": False, "error_type": "TweetError", "error_message": str(e)}


# 3. Получение ленты (Только подписки + свои по ТЗ)
from sqlalchemy import func # Не забудь импорт func в начале файла!

@router.get("/tweets")  # Маршрут /api/tweets
async def get_tweets(db: AsyncSession = Depends(get_db)):
    # 1. Считаем общее количество твитов для фронтенда (обязательно!)
    count_query = await db.execute(select(func.count(Tweet.id)))
    total_count = count_query.scalar()

    # 2. Загружаем твиты (проверь, чтобы в модели было likes_rel или likes)
    # Используй то имя связи, которое у тебя сейчас работает в Tweet
    result = await db.execute(
        select(Tweet)
        .options(
            selectinload(Tweet.author),
            selectinload(Tweet.likes_rel), # Если ошибка - замени на Tweet.likes
            selectinload(Tweet.attachments)
        )
        .order_by(Tweet.id.desc())
    )
    tweets_list = result.scalars().all()

    # 3. Формируем ответ строго по контракту
    return {
        "result": True,
        "tweets": [
            {
                "id": t.id,
                "content": t.content,
                "author": {"id": t.author.id, "name": t.author.name},
                "likes": [{"user_id": l.id, "name": l.name} for l in t.likes_rel],
                "attachments": [a.file_path for a in t.attachments]
            }
            for t in tweets_list
        ]
    }




# 4. Удаление твита
@router.delete("/tweets/{id}")
async def delete_tweet(
        id: int,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Tweet).where(Tweet.id == id, Tweet.author_id == user.id))
    tweet = result.scalars().first()
    if not tweet:
        return {"result": False, "error_message": "Твит не найден"}

    await db.delete(tweet)
    await db.commit()
    return {"result": True}


# 5. Лайки
@router.post("/tweets/{id}/likes", status_code=201)
async def add_like(id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from sqlalchemy.dialects.postgresql import insert
    stmt = insert(likes).values(user_id=user.id, tweet_id=id).on_conflict_do_nothing()
    await db.execute(stmt)
    await db.commit()
    return {"result": True}


@router.delete("/tweets/{id}/likes")
async def remove_like(id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await db.execute(delete(likes).where(likes.c.user_id == user.id, likes.c.tweet_id == id))
    await db.commit()
    return {"result": True}
