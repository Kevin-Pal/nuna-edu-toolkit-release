import time
from sqlalchemy import Column, Integer, String, ForeignKey, Index
from database import Base


class User(Base):
    __tablename__ = "users"

    userId = Column(String, primary_key=True, index=True)


class AudioData(Base):
    __tablename__ = "audio_data"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    userId = Column(String, ForeignKey("users.userId"), nullable=False)
    date = Column(String, nullable=False)
    start_ts = Column(Integer, nullable=False)
    file_path = Column(String, nullable=False)
    pre_label_status = Column(String, nullable=False, default="empty")


class PrelabelJob(Base):
    __tablename__ = "prelabel_jobs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    userId = Column(String, ForeignKey("users.userId"), nullable=False)
    day_id = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")
    created_at = Column(Integer, nullable=False, default=lambda: int(time.time()))
    started_at = Column(Integer, nullable=True)
    finished_at = Column(Integer, nullable=True)
    error_log = Column(String, nullable=True)
    pipeline_version = Column(String, nullable=False, default="mvp-asr-v1")

    __table_args__ = (
        Index("idx_prelabel_user_day_created", "userId", "day_id", "created_at"),
        Index("idx_prelabel_user_status", "userId", "status"),
    )


class PrelabelResult(Base):
    __tablename__ = "prelabel_results"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("prelabel_jobs.id"), nullable=False)
    userId = Column(String, ForeignKey("users.userId"), nullable=False)
    day_id = Column(String, nullable=False)
    audio_id = Column(Integer, nullable=True)
    minute_ts = Column(Integer, nullable=True)
    task_type = Column(String, nullable=False)
    content_json = Column(String, nullable=False)
    created_at = Column(Integer, nullable=False, default=lambda: int(time.time()))

    __table_args__ = (
        Index("idx_prelabel_result_job", "job_id"),
        Index("idx_prelabel_result_user_day", "userId", "day_id"),
    )
