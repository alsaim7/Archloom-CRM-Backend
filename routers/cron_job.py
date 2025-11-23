from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import text
import os
from database import get_session

router = APIRouter()
security = HTTPBearer()

@router.get("/cron/auto-activate")
async def auto_activate(credentials: HTTPAuthorizationCredentials = Depends(security)):
    
    # Only require auth in production
    if credentials.credentials != os.getenv("CRON_SECRET"):
        raise HTTPException(status_code=401, detail="Unauthorized")

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
        print("🔥 CRON ERROR:", str(e))
        db.rollback()
        return {"status": "error", "message": str(e)}

    finally:
        db.close()