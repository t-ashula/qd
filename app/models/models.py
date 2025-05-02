import uuid

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class Episode(Base):  # type: ignore[valid-type, misc]
    """
    Episodes table for storing uploaded media files metadata
    """

    __tablename__ = "episodes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    media_type = Column(String, nullable=False)  # content-type
    name = Column(String, nullable=False)  # original filename
    bytes = Column(Integer, nullable=False)  # file size
    length = Column(Integer, nullable=True)  # duration in ms
    hash = Column(String(64), nullable=True, unique=True)  # sha256 hash
    created_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"<Episode(id='{self.id}', name='{self.name}')>"


class EpisodeSegment(Base):  # type: ignore[valid-type, misc]
    """
    Episode segments table for storing transcribed segments
    """

    __tablename__ = "episode_segments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    episode_id = Column(String, ForeignKey("episodes.id"), nullable=False)
    seg_no = Column(Integer, nullable=False)
    start = Column(Integer, nullable=False)  # start time in ms
    end = Column(Integer, nullable=False)  # end time in ms
    text = Column(Text, nullable=False)  # transcribed text
    created_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"<EpisodeSegment(id={self.id}, episode_id='{self.episode_id}', seg_no={self.seg_no})>"
