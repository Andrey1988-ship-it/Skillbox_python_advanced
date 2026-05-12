from sqlalchemy import Column, Integer, String, ForeignKey, Table, Text
from sqlalchemy.orm import relationship
from app.core.database import Base

# 1. Таблицы связей (Likes и Followers)
followers = Table(
    "followers", Base.metadata,
    Column("follower_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("following_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    extend_existing=True
)

likes = Table(
    "likes", Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("tweet_id", Integer, ForeignKey("tweets.id", ondelete="CASCADE"), primary_key=True),
    extend_existing=True
)


# 2. Модель Пользователя
class User(Base):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    api_key = Column(String, unique=True, index=True, nullable=False)

    tweets = relationship("Tweet", back_populates="author", cascade="all, delete-orphan")

    # Система подписок
    following = relationship(
        "User", secondary=followers,
        primaryjoin=(id == followers.c.follower_id),
        secondaryjoin=(id == followers.c.following_id),
        backref="followers_rel"
    )


# 3. Модель Твита
class Tweet(Base):
    __tablename__ = "tweets"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))

    author = relationship("User", back_populates="tweets")
    # Убедитесь, что имя здесь совпадает с тем, что вы вызываете в роутере
    likes_rel = relationship("User", secondary=likes, backref="liked_tweets")
    attachments = relationship("Media", back_populates="tweet", cascade="all, delete-orphan")



# 4. Модель Медиа (Картинки)
class Media(Base):
    __tablename__ = "medias"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    file_path = Column(String, nullable=False)
    tweet_id = Column(Integer, ForeignKey("tweets.id", ondelete="SET NULL"), nullable=True)

    tweet = relationship("Tweet", back_populates="attachments")
