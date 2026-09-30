from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel

class ProductItem(BaseModel):
    name: str
    category: str
    estimated_price: float
    quantity: int = 1
    reason: str
    platform: str
    purchase_link: str
    badge: Optional[str] = None
    specs: Optional[str] = None

class CategoryAllocation(BaseModel):
    category: str
    allocated_amount: float
    percentage: float

class BudgetSummary(BaseModel):
    total_budget: float
    estimated_total: float
    remaining_budget: float
    is_within_budget: bool

class RecommendationResponse(BaseModel):
    planner_type: str
    title: str
    summary: str
    ai_analysis: Optional[str] = None
    budget_summary: BudgetSummary
    allocations: List[CategoryAllocation]
    items: List[ProductItem]
    created_at: str
    recommendation_id: Optional[int] = None

class HistoryResponseItem(BaseModel):
    id: int
    planner_type: str
    budget: float
    created_at: datetime
    request_data: Dict[str, Any]
    response_data: Dict[str, Any]

    class Config:
        from_attributes = True
