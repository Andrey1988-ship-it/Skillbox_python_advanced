# from sqlalchemy import Column, Integer, String
# from sqlalchemy.orm import relationship
# from app.core.database import Base
# from app.models.base_tables import followers, likes
# from app.models.tweet import Tweet  # <--- Импортируй класс
#
#
# class User(Base):
#     __tablename__ = "users"
#     __table_args__ = {'extend_existing': True}
#
#     id = Column(Integer, primary_key=True)
#     name = Column(String, nullable=False)
#     api_key = Column(String, unique=True, index=True, nullable=False)
#
#     # Используй имя класса Tweet БЕЗ кавычек
#     tweets = relationship(Tweet, back_populates="author", cascade="all, delete-orphan")
#     liked_tweets = relationship(Tweet, secondary=likes, back_populates="likes")
#
#     following = relationship(
#         "User", secondary=followers,
#         primaryjoin=(id == followers.c.follower_id),
#         secondaryjoin=(id == followers.c.following_id),
#         backref="followers_rel"
#     )
