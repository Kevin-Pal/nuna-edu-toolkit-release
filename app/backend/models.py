from sqlalchemy import Column, Integer, String, ForeignKey, Index
from sqlalchemy.orm import relationship
from .database import Base
import time

class User(Base):
    __tablename__ = "users"

    userId = Column(String, primary_key=True, index=True)
    password_hash = Column(String, nullable=False)
    email = Column(String, nullable=False)
    created_at = Column(Integer, nullable=False, default=lambda: int(time.time()))
    last_sync_time = Column(Integer, nullable=False, default=0)
    last_sync_status = Column(String, nullable=False, default="idle")  # idle/running/failed/success
    last_sync_msg = Column(String, nullable=True)

    audio_segments = relationship("AudioData", back_populates="user")
    blocks = relationship("AnnotationBlock", back_populates="user")
    points = relationship("AnnotationPoint", back_populates="user")

class AudioData(Base):
    __tablename__ = "audio_data"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    userId = Column(String, ForeignKey("users.userId"), nullable=False)
    file_path = Column(String, nullable=False)
    date = Column(String, nullable=False) # YYYYMMDD
    start_ts = Column(Integer, nullable=False)
    duration_sec = Column(Integer, nullable=False, default=60)
    pre_label_status = Column(String, nullable=False, default="empty") # empty/queued/running/done/failed
    label_status = Column(String, nullable=False, default="unlabeled") # unlabeled/partially_labeled/labeled
    created_at = Column(Integer, nullable=False, default=lambda: int(time.time()))
    updated_at = Column(Integer, nullable=False, default=lambda: int(time.time()), onupdate=lambda: int(time.time()))

    user = relationship("User", back_populates="audio_segments")
    
    __table_args__ = (
        Index('idx_audio_user_date', 'userId', 'date'),
        Index('idx_audio_user_start', 'userId', 'start_ts'),
    )

class AnnotationBlock(Base):
    __tablename__ = "annotation_blocks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    userId = Column(String, ForeignKey("users.userId"), nullable=False)
    date = Column(String, nullable=False)
    start_audio_id = Column(Integer, nullable=False)
    end_audio_id = Column(Integer, nullable=False)
    segment_count = Column(Integer, nullable=False)
    
    scene_adj = Column(String, nullable=False)
    scene_noun = Column(String, nullable=False)
    scene_note = Column(String, nullable=True)
    
    be_adv = Column(String, nullable=False)
    be_verb = Column(String, nullable=False)
    be_note = Column(String, nullable=True)
    
    emo_valence = Column(String, nullable=False) # low/mid/high
    emo_arousal = Column(String, nullable=False) # low/mid/high/very_high
    
    created_at = Column(Integer, nullable=False, default=lambda: int(time.time()))
    updated_at = Column(Integer, nullable=False, default=lambda: int(time.time()), onupdate=lambda: int(time.time()))

    user = relationship("User", back_populates="blocks")
    points = relationship("AnnotationPoint", back_populates="block", cascade="all, delete-orphan")

class AnnotationPoint(Base):
    __tablename__ = "annotation_points"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    userId = Column(String, ForeignKey("users.userId"), nullable=False)
    block_id = Column(Integer, ForeignKey("annotation_blocks.id"), nullable=False)
    start_audio_id = Column(Integer, nullable=False)
    end_audio_id = Column(Integer, nullable=False)
    segment_count = Column(Integer, nullable=False)
    
    pe_type = Column(String, nullable=False) # env_fluctuation/personal_action
    
    env_subject = Column(String, nullable=True)
    env_predicate = Column(String, nullable=True)
    
    act_adv = Column(String, nullable=True)
    act_verb = Column(String, nullable=True)
    
    pe_note = Column(String, nullable=True)
    
    emo_valence = Column(String, nullable=False)
    emo_arousal = Column(String, nullable=False)
    
    created_at = Column(Integer, nullable=False, default=lambda: int(time.time()))
    updated_at = Column(Integer, nullable=False, default=lambda: int(time.time()), onupdate=lambda: int(time.time()))

    user = relationship("User", back_populates="points")
    block = relationship("AnnotationBlock", back_populates="points")


class PrelabelJob(Base):
    __tablename__ = "prelabel_jobs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    userId = Column(String, ForeignKey("users.userId"), nullable=False)
    day_id = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")  # pending/running/done/failed
    created_at = Column(Integer, nullable=False, default=lambda: int(time.time()))
    started_at = Column(Integer, nullable=True)
    finished_at = Column(Integer, nullable=True)
    error_log = Column(String, nullable=True)
    pipeline_version = Column(String, nullable=False, default="mvp-mock-v1")

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
    task_type = Column(String, nullable=False)  # asr / sed_asc_har
    content_json = Column(String, nullable=False)
    created_at = Column(Integer, nullable=False, default=lambda: int(time.time()))

    __table_args__ = (
        Index("idx_prelabel_result_job", "job_id"),
        Index("idx_prelabel_result_user_day", "userId", "day_id"),
    )
