import re
from fastapi import Depends
from sqlmodel import Session, select
from models import CustomerModel, User
from security.oauth2 import get_current_user

# Utility: next ARC code inside the same session/transaction
def _format_arc(n: int) -> str:
    # ARC001..ARC999 then ARC1000, ARC1001...
    return f"ARC{n:03d}" if n < 1000 else f"ARC{n}"

def _next_customer_id(session: Session) -> str:
    """
    Generate next ARC code by reading the max numeric suffix and adding 1.
    """
    # Extract numeric suffix with regex on the database side if supported,
    # otherwise fetch max customer_id and parse in Python.
    # Here we simply fetch the current max and compute next.
    # Beware: this can race under concurrent inserts; wrap in a transaction.
    max_code = session.exec(
        select(CustomerModel.customer_id).order_by(CustomerModel.customer_id.desc()).limit(1)
    ).first()

    if not max_code:
        next_n = 1
    else:
        code = max_code
        # Parse "ARC" prefix; fall back to 0 if unexpected
        m = re.match(r"^ARC(\d+)$", code or "")
        current = int(m.group(1)) if m else 0
        next_n = current + 1

    return _format_arc(next_n)




# -------------------------------
# Dependency: Filter customers by current user
# -------------------------------
def filter_customers_by_user(current_user: User = Depends(get_current_user)):
    """
    Returns a function that filters customers by assigned_to for normal users.
    Admins see all customers.
    """
    def filter_stmt(stmt):
        if current_user.role != "admin":
            stmt = stmt.where(CustomerModel.assigned_to == current_user.id)
        return stmt
    return filter_stmt



# -------------------------------
# To return the user's name
# -------------------------------
def add_user_name(db, customer: CustomerModel):
    user = db.exec(select(User).where(User.id == customer.assigned_to)).one_or_none()
    data = customer.model_dump()
    data["assigned_to_name"] = user.name if user else None
    return data
