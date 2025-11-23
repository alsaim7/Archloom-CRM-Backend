from fastapi import APIRouter, Request, HTTPException
from sqlalchemy import text
import os
from database import get_session  # adjust to match your project

router = APIRouter()

@router.get("/cron/auto-activate")
async def auto_activate(request: Request):
    # Security check
    auth = request.headers.get("Authorization")
    if auth != f"Bearer {os.getenv('SECRET_KEY')}":
        raise HTTPException(status_code=401, detail="Unauthorized")

    # SQL query
    query = text("""
        UPDATE customers
        SET status='ACTIVE',
            hold_since=NULL
        WHERE status='HOLD'
          AND hold_since <= CURRENT_DATE - INTERVAL '12 days';
    """)

    db = get_session()
    try:
        db.execute(query)
        db.commit()
        return {"status": "success", "message": "Hold leads auto-updated"}
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()