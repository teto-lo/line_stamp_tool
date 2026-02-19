from sqlalchemy import create_engine, Column, String, Integer, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import uuid

Base = declarative_base()

class StampSet(Base):
    __tablename__ = 'stamp_sets'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    genre = Column(String, nullable=False)  # animal / original_character / concept / ai_free
    character_description = Column(Text)
    reference_image_path = Column(String, nullable=True)
    status = Column(String, nullable=False, default='direction_pending')
    created_at = Column(DateTime, default=datetime.utcnow)
    approved_at = Column(DateTime, nullable=True)
    slack_ts = Column(String, nullable=True)
    lora_exported = Column(Boolean, default=False)
    seed = Column(Integer, nullable=True)
    character_consistency = Column(Boolean, default=True)  # キャラクターの一貫性が必要か
    
    # LoRA関連
    lora_model_path = Column(String, nullable=True)  # 学習済みLoRAモデルのパス
    lora_status = Column(String, nullable=False, default='none')  # 'none' / 'training' / 'completed'
    
    # バリエーション関連
    parent_set_id = Column(String, nullable=True)  # バリエーション元のset_id
    variation_theme = Column(String, nullable=True)  # バリエーションテーマ
    
    # Relationship
    stamps = relationship("Stamp", back_populates="set", cascade="all, delete-orphan")
    variations = relationship("StampSet", remote_side=[id], backref="parent")
    
    # Status constants
    STATUSES = [
        'direction_pending',
        'direction_approved', 
        'patterns_pending',
        'patterns_approved',
        'samples_generating',
        'samples_review',
        'full_generating',
        'full_review',
        'completed'
    ]

class Stamp(Base):
    __tablename__ = 'stamps'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    set_id = Column(String, ForeignKey('stamp_sets.id'), nullable=False)
    number = Column(Integer, nullable=False)
    phrase = Column(Text, nullable=False)
    prompt = Column(Text, nullable=False)
    negative_prompt = Column(Text, nullable=True)
    image_path = Column(String, nullable=True)
    status = Column(String, nullable=False, default='pending')
    seed = Column(Integer, nullable=True)
    is_sample = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    retry_count = Column(Integer, default=0)  # 再生成回数
    
    # Relationship
    set = relationship("StampSet", back_populates="stamps")
    
    # Status constants
    STATUSES = ['pending', 'approved', 'rejected', 'regenerating']

# Database setup
def init_db(db_path: str):
    engine = create_engine(f'sqlite:///{db_path}')
    Base.metadata.create_all(engine)
    return engine

def get_session(engine):
    Session = sessionmaker(bind=engine)
    return Session()
