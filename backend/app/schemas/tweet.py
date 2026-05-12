from pydantic import BaseModel
from typing import List, Optional

# Базовая схема ответа (для всех эндпоинтов по ТЗ)
class BaseResponse(BaseModel):
    result: bool = True

# Ошибка (по ТЗ)
class ErrorResponse(BaseResponse):
    result: bool = False
    error_type: str
    error_message: str

# Схема пользователя (краткая)
class UserSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

# Схема для создания твита
class TweetCreate(BaseModel):
    tweet_data: str
    tweet_media_ids: Optional[List[int]] = None

# Полная схема твита для ленты
class TweetOut(BaseModel):
    id: int
    content: str
    author: UserSchema
    likes: List[UserSchema]
    attachments: List[str]

    class Config:
        from_attributes = True

# Ответ при получении списка твитов
class TweetListOut(BaseResponse):
    tweets: List[TweetOut]
