from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from app.core.database import Base
from typing import Optional
import datetime

#This is the model for the paragraphs table
class Paragraph(Base):
    
    __tablename__ = "paragraphs"
    
    id = Column(Integer, primary_key=True, index=True)#auto-incrementing unique ID
    content = Column(Text, nullable=False, index=True)#kept it as text because it can be long
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)#timestamp of when the paragraph was stored
    
    def __repr__(self):
        return f"<Paragraph(id={self.id}, created_at={self.created_at})>"

