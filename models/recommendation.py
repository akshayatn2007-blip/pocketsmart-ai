from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    planner_type = Column(String(50), nullable=False, index=True)  # 'home', 'party', 'jewelry'
    budget = Column(Float, nullable=False)
    request_data = Column(Text, nullable=False)   # JSON string of input parameters
    response_data = Column(Text, nullable=False)  # JSON string of recommendations and allocation
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship back to User
    user = relationship("User", back_populates="recommendations")

    def __repr__(self):
        return f"<Recommendation(id={self.id}, user_id={self.user_id}, planner_type='{self.planner_type}', budget={self.budget})>"
