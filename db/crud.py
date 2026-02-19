from sqlalchemy.orm import Session
from sqlalchemy import and_
from .models import StampSet, Stamp
from typing import List, Optional
import uuid
from datetime import datetime

class StampSetCRUD:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, name: str, genre: str, character_description: str = None, 
               reference_image_path: str = None, slack_ts: str = None, 
               character_consistency: bool = True, parent_set_id: str = None,
               variation_theme: str = None) -> StampSet:
        stamp_set = StampSet(
            name=name,
            genre=genre,
            character_description=character_description,
            reference_image_path=reference_image_path,
            slack_ts=slack_ts,
            character_consistency=character_consistency,
            parent_set_id=parent_set_id,
            variation_theme=variation_theme
        )
        self.db.add(stamp_set)
        self.db.commit()
        self.db.refresh(stamp_set)
        return stamp_set
    
    def get(self, set_id: str) -> Optional[StampSet]:
        return self.db.query(StampSet).filter(StampSet.id == set_id).first()
    
    def get_by_slack_ts(self, slack_ts: str) -> Optional[StampSet]:
        return self.db.query(StampSet).filter(StampSet.slack_ts == slack_ts).first()
    
    def get_all(self, status: Optional[str] = None) -> List[StampSet]:
        query = self.db.query(StampSet)
        if status:
            query = query.filter(StampSet.status == status)
        return query.order_by(StampSet.created_at.desc()).all()
    
    def update_status(self, set_id: str, status: str) -> Optional[StampSet]:
        stamp_set = self.get(set_id)
        if stamp_set:
            stamp_set.status = status
            if status in ['direction_approved', 'patterns_approved', 'completed']:
                stamp_set.approved_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(stamp_set)
        return stamp_set
    
    def update_slack_ts(self, set_id: str, slack_ts: str) -> Optional[StampSet]:
        stamp_set = self.get(set_id)
        if stamp_set:
            stamp_set.slack_ts = slack_ts
            self.db.commit()
            self.db.refresh(stamp_set)
        return stamp_set
    
    def update_character_description(self, set_id: str, description: str) -> Optional[StampSet]:
        stamp_set = self.get(set_id)
        if stamp_set:
            stamp_set.character_description = description
            self.db.commit()
            self.db.refresh(stamp_set)
        return stamp_set
    
    def update_reference_image(self, set_id: str, image_path: str) -> Optional[StampSet]:
        stamp_set = self.get(set_id)
        if stamp_set:
            stamp_set.reference_image_path = image_path
            self.db.commit()
            self.db.refresh(stamp_set)
        return stamp_set
    
    def update_seed(self, set_id: str, seed: int) -> Optional[StampSet]:
        stamp_set = self.get(set_id)
        if stamp_set:
            stamp_set.seed = seed
            self.db.commit()
            self.db.refresh(stamp_set)
        return stamp_set
    
    def update_lora_status(self, set_id: str, lora_status: str, lora_model_path: str = None) -> Optional[StampSet]:
        stamp_set = self.get(set_id)
        if stamp_set:
            stamp_set.lora_status = lora_status
            if lora_model_path:
                stamp_set.lora_model_path = lora_model_path
            self.db.commit()
            self.db.refresh(stamp_set)
        return stamp_set
    
    def get_variations(self, parent_set_id: str) -> List[StampSet]:
        return self.db.query(StampSet).filter(StampSet.parent_set_id == parent_set_id).all()
    
    def get_completed_sets(self) -> List[StampSet]:
        return self.db.query(StampSet).filter(StampSet.status == 'completed').all()
    
    def mark_lora_exported(self, set_id: str) -> Optional[StampSet]:
        stamp_set = self.get(set_id)
        if stamp_set:
            stamp_set.lora_exported = True
            self.db.commit()
            self.db.refresh(stamp_set)
        return stamp_set

class StampCRUD:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, set_id: str, number: int, phrase: str, prompt: str, 
               negative_prompt: str = None, seed: int = None, is_sample: bool = False) -> Stamp:
        stamp = Stamp(
            set_id=set_id,
            number=number,
            phrase=phrase,
            prompt=prompt,
            negative_prompt=negative_prompt,
            seed=seed,
            is_sample=is_sample
        )
        self.db.add(stamp)
        self.db.commit()
        self.db.refresh(stamp)
        return stamp
    
    def get(self, stamp_id: str) -> Optional[Stamp]:
        return self.db.query(Stamp).filter(Stamp.id == stamp_id).first()
    
    def get_by_set(self, set_id: str, is_sample: Optional[bool] = None) -> List[Stamp]:
        query = self.db.query(Stamp).filter(Stamp.set_id == set_id)
        if is_sample is not None:
            query = query.filter(Stamp.is_sample == is_sample)
        return query.order_by(Stamp.number).all()
    
    def get_pending_stamps(self, set_id: str) -> List[Stamp]:
        return self.db.query(Stamp).filter(
            Stamp.set_id == set_id,
            Stamp.status == 'pending'
        ).order_by(Stamp.number).all()
    
    def get_completed_count(self, set_id: str) -> int:
        return self.db.query(Stamp).filter(
            Stamp.set_id == set_id,
            Stamp.status == 'approved'
        ).count()
    
    def increment_retry_count(self, stamp_id: str) -> Optional[Stamp]:
        stamp = self.get(stamp_id)
        if stamp:
            stamp.retry_count += 1
            self.db.commit()
            self.db.refresh(stamp)
        return stamp
    
    def update_status(self, stamp_id: str, status: str) -> Optional[Stamp]:
        stamp = self.get(stamp_id)
        if stamp:
            stamp.status = status
            self.db.commit()
            self.db.refresh(stamp)
        return stamp
    
    def update_image_path(self, stamp_id: str, image_path: str) -> Optional[Stamp]:
        stamp = self.get(stamp_id)
        if stamp:
            stamp.image_path = image_path
            self.db.commit()
            self.db.refresh(stamp)
        return stamp
    
    def update_prompt(self, stamp_id: str, prompt: str, negative_prompt: str = None) -> Optional[Stamp]:
        stamp = self.get(stamp_id)
        if stamp:
            stamp.prompt = prompt
            if negative_prompt:
                stamp.negative_prompt = negative_prompt
            self.db.commit()
            self.db.refresh(stamp)
        return stamp
    
    def delete_by_set(self, set_id: str) -> int:
        count = self.db.query(Stamp).filter(Stamp.set_id == set_id).count()
        self.db.query(Stamp).filter(Stamp.set_id == set_id).delete()
        self.db.commit()
        return count
