import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from models.recommendation import Recommendation
from models.user import User

class RecommendationService:
    @classmethod
    def save_recommendation(
        cls,
        db: Session,
        planner_type: str,
        budget: float,
        request_data: Dict[str, Any],
        response_data: Dict[str, Any],
        user: Optional[User] = None
    ) -> Recommendation:
        rec = Recommendation(
            user_id=user.id if user else None,
            planner_type=planner_type,
            budget=budget,
            request_data=json.dumps(request_data, default=str),
            response_data=json.dumps(response_data, default=str),
            created_at=datetime.utcnow()
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)
        return rec

    @classmethod
    def get_user_history(cls, db: Session, user: Optional[User], limit: int = 50) -> List[Dict[str, Any]]:
        query = db.query(Recommendation)
        if user:
            query = query.filter(Recommendation.user_id == user.id)
        else:
            query = query.filter(Recommendation.user_id.is_(None))
        records = query.order_by(Recommendation.created_at.desc()).limit(limit).all()

        results = []
        for r in records:
            try:
                req_json = json.loads(r.request_data)
            except Exception:
                req_json = {}
            try:
                res_json = json.loads(r.response_data)
            except Exception:
                res_json = {}
            results.append({
                "id": r.id,
                "planner_type": r.planner_type,
                "budget": r.budget,
                "created_at": r.created_at.isoformat(),
                "title": res_json.get("title", f"{r.planner_type.capitalize()} Plan"),
                "summary": res_json.get("summary", ""),
                "request_data": req_json,
                "response_data": res_json
            })
        return results

    @classmethod
    def get_recommendation_details(
        cls,
        db: Session,
        planner_type: Optional[str] = None,
        rec_id: Optional[int] = None,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        if rec_id:
            record = db.query(Recommendation).filter(Recommendation.id == rec_id).first()
            if record:
                return {
                    "id": record.id,
                    "planner_type": record.planner_type,
                    "budget": record.budget,
                    "created_at": record.created_at.isoformat(),
                    "request_data": json.loads(record.request_data),
                    "response_data": json.loads(record.response_data)
                }
        
        # If no specific rec_id, fetch latest for the planner type
        query = db.query(Recommendation)
        if planner_type:
            query = query.filter(Recommendation.planner_type == planner_type)
        record = query.order_by(Recommendation.created_at.desc()).first()
        if record:
            data = json.loads(record.response_data)
            if category:
                # Filter items matching category
                data["items"] = [it for it in data.get("items", []) if category.lower() in it.get("category", "").lower()]
            return {
                "id": record.id,
                "planner_type": record.planner_type,
                "budget": record.budget,
                "created_at": record.created_at.isoformat(),
                "response_data": data
            }

        return {"message": "No recommendation found matching criteria", "status": "empty"}

recommendation_service = RecommendationService()
