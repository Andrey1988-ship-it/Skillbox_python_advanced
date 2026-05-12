from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.base import User, followers

# Важно: убираем /users из префикса здесь, так как в main.py
# мы уже добавили prefix="/api". Теперь роуты будут /api/users/me и т.д.
router = APIRouter(prefix="/users", tags=["users"])


# Вспомогательная функция для проверки api-key
async def get_current_user(api_key: str = Header(None), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.api_key == api_key))
    user = result.scalars().first()

    if not user:
        # Вместо обычного raise HTTPException, возвращаем JSON по ТЗ
        raise HTTPException(
            status_code=401,
            detail={
                "result": False,
                "error_type": "Unauthorized",
                "error_message": "Некорректный API-ключ"
            }
        )
    return user


# 1. Получение информации о своем профиле
@router.get("/me")
async def get_me(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User)
        .options(selectinload(User.following), selectinload(User.followers_rel))
        .where(User.id == user.id)
    )
    u = result.scalars().first()

    return {
        "result": True,
        "user": {
            "id": u.id,
            "name": u.name,
            "followers": [{"id": f.id, "name": f.name} for f in u.followers_rel],
            "following": [{"id": f.id, "name": f.name} for f in u.following]
        }
    }


# 2. Получение информации о чужом профиле
@router.get("/{id}")
async def get_user(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User)
        .options(selectinload(User.following), selectinload(User.followers_rel))
        .where(User.id == id)
    )
    u = result.scalars().first()
    if not u:
        return {"result": False, "error_type": "404", "error_message": "Пользователь не найден"}

    return {
        "result": True,
        "user": {
            "id": u.id,
            "name": u.name,
            "followers": [{"id": f.id, "name": f.name} for f in u.followers_rel],
            "following": [{"id": f.id, "name": f.name} for f in u.following]
        }
    }


# 3. Подписка на пользователя
@router.post("/{id}/follow")
async def follow(id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user.id == id:
        return {"result": False, "error_message": "Нельзя подписаться на самого себя"}

    # Проверка на существование того, на кого подписываемся
    target_res = await db.execute(select(User).where(User.id == id))
    if not target_res.scalars().first():
        return {"result": False, "error_message": "Пользователь не найден"}

    # Добавляем запись в таблицу связей
    stmt = followers.insert().values(follower_id=current_user.id, following_id=id)
    try:
        await db.execute(stmt)
        await db.commit()
    except Exception:
        return {"result": False, "error_message": "Вы уже подписаны"}

    return {"result": True}


# 4. Отписка от пользователя (Обязательно по ТЗ)
@router.delete("/{id}/follow")
async def unfollow(id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    stmt = delete(followers).where(
        followers.c.follower_id == current_user.id,
        followers.c.following_id == id
    )
    result = await db.execute(stmt)
    await db.commit()

    if result.rowcount == 0:
        return {"result": False, "error_message": "Вы не были подписаны на этого пользователя"}

    return {"result": True}


@router.post("", status_code=201)
async def create_user(
    name: str,
    api_key: str,
    db: AsyncSession = Depends(get_db)
):
    new_user = User(name=name, api_key=api_key)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return {"result": True, "user_id": new_user.id}