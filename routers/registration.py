from datetime import date, datetime, timedelta
import re
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlmodel import Session, select, func
from database import get_session
from schemas.registration_schema import CustomerCreateSchema, CustomerReadSchema, CustomerUpdateSchema
from models import CustomerModel, User
from utils import _next_customer_id, filter_customers_by_user, add_user_name
from security.oauth2 import get_current_user


router = APIRouter(
    tags=["Customer"],
    dependencies=[Depends(get_current_user)]
)



# -------------------------------
# Create customer
# -------------------------------
@router.post("/customers", response_model=CustomerReadSchema)
def create_customer(
    payload: CustomerCreateSchema,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    try:
        customer_id = _next_customer_id(db)

        # Use assigned_to from payload if provided AND user is admin, otherwise use current user
        if current_user.role == "admin" and payload.assigned_to:
            assigned_to = payload.assigned_to
        else:
            assigned_to = current_user.id

        customer = CustomerModel(
            customer_id=customer_id,
            fullname=payload.fullname,
            mobile=payload.mobile,
            email=payload.email,
            address=payload.address,
            reg_date=payload.reg_date,
            notes=[
                    {
                        "date": note.date.strftime("%Y-%m-%d") if isinstance(note.date, (datetime, date)) else note.date,
                        "note": note.note
                    }
                    for note in payload.notes
                ] if payload.notes else [],

            status="ACTIVE",
            assigned_to=assigned_to  # Use the determined assigned_to value
        )

        db.add(customer)
        db.commit()
        db.refresh(customer)
        return add_user_name(db,customer)

    except HTTPException:
        raise
    except Exception as e:
        try:
            db.rollback()
        except Exception:
            pass
        raise HTTPException(status_code=500, detail="Failed to create customer")


# -------------------------------
# Get list of customers (paginated)
# -------------------------------
@router.get("/customers", response_model=list[CustomerReadSchema], status_code=status.HTTP_200_OK)
def get_customers(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_session),
    filter_stmt=Depends(filter_customers_by_user)
):
    try:
        stmt = filter_stmt(select(CustomerModel)).order_by(CustomerModel.customer_id.desc())
        stmt = stmt.offset(offset).limit(limit)
        customers = db.exec(stmt).all()

        return [add_user_name(db, c) for c in customers]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch customers: {str(e)}")


# -------------------------------
# Search customer by ID or mobile
# -------------------------------
@router.get("/customer/{search_data}", response_model=list[CustomerReadSchema], status_code=status.HTTP_200_OK)
def search_customer_by_id_or_mobile(
    search_data: str,
    db: Session = Depends(get_session),
    filter_stmt=Depends(filter_customers_by_user)
):
    try:
        code = search_data.strip().upper()
        digits = re.sub(r"\D", "", search_data)

        stmt = filter_stmt(select(CustomerModel))

        if re.fullmatch(r"ARC\d+", code):
            stmt = stmt.where(CustomerModel.customer_id == code).order_by(CustomerModel.id.desc())
            customers = db.exec(stmt).all()
            return [add_user_name(db, c) for c in customers]

        if len(digits) == 10:
            stmt = stmt.where(CustomerModel.mobile == digits).order_by(CustomerModel.id.desc())
            customers = db.exec(stmt).all()
            return [add_user_name(db, c) for c in customers]

        return []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


# -------------------------------
# Filter customers
# -------------------------------
@router.get("/customers/filter", response_model=list[CustomerReadSchema], status_code=status.HTTP_200_OK)
def filter_customers(
    date_from: Optional[date] = Query(None, description="YYYY-MM-DD"),
    date_to: Optional[date] = Query(None, description="YYYY-MM-DD"),
    status_: Optional[str] = Query(None, alias="status", description="ACTIVE | HOLD | CLOSED"),
    assigned_to_name: Optional[str] = Query(None, description="Filter by assigned user name"),  # ✅ new
    db: Session = Depends(get_session),
    filter_stmt=Depends(filter_customers_by_user),
    current_user: User = Depends(get_current_user),  # ✅ required for role check
):
    try:
        stmt = filter_stmt(select(CustomerModel))

        # Apply status/date filters
        if status_:
            stmt = stmt.where(CustomerModel.status == status_)
        if date_from:
            stmt = stmt.where(CustomerModel.reg_date >= date_from)
        if date_to:
            stmt = stmt.where(CustomerModel.reg_date <= date_to)

        # ✅ Only admins can use assigned_to_name
        if assigned_to_name:
            if current_user.role != "admin":
                raise HTTPException(
                    status_code=403,
                    detail="You are not authorized to filter by assigned user"
                )
            # Search user by name
            assigned_user = db.exec(
                select(User).where(User.name.ilike(f"%{assigned_to_name.strip()}%"))
            ).first()

            if not assigned_user:
                raise HTTPException(status_code=404, detail="Assigned user not found")

            stmt = stmt.where(CustomerModel.assigned_to == assigned_user.id)

        stmt = stmt.order_by(CustomerModel.id.desc())

        if not date_from and not date_to and not status_ and not assigned_to_name:
            stmt = stmt.limit(100)

        customers = db.exec(stmt).all()
        return [add_user_name(db, c) for c in customers]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to filter customers: {str(e)}")


# -------------------------------
# Update customer
# -------------------------------
@router.patch("/customer/{customer_id}", response_model=CustomerReadSchema, status_code=status.HTTP_200_OK)
def update_customer_partial(
    customer_id: str = Path(..., description="Human-friendly ID like ARC001"),
    payload: CustomerUpdateSchema = ...,
    db: Session = Depends(get_session),
    filter_stmt=Depends(filter_customers_by_user),
    current_user: User = Depends(get_current_user),
):
    try:
        # 1️⃣ Find customer owned by current user or accessible to admin
        stmt = filter_stmt(select(CustomerModel)).where(CustomerModel.customer_id == customer_id)
        customer = db.exec(stmt).one_or_none()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found or access denied")

        update_data = payload.model_dump(exclude_unset=True)

        # 2️⃣ Restrict non-admin users to limited fields
        if current_user.role != "admin":
            allowed_fields = {"notes", "status", "hold_since"}
            update_data = {k: v for k, v in update_data.items() if k in allowed_fields}

        # 3️⃣ Handle status change logic
        new_status = update_data.get("status")
        if new_status in {"ACTIVE", "CLOSED"}:
            update_data["hold_since"] = None

        # 4️⃣ Restrict assignment updates — only admins can change assigned_to
        if "assigned_to" in update_data and current_user.role != "admin":
            update_data.pop("assigned_to")

        # 5️⃣ Apply updates
        for key, value in update_data.items():
            if key == "notes":
                # ✅ Ensure all note dates are strings (JSON serializable)
                sanitized_notes = [
                    {
                        "date": n["date"].strftime("%Y-%m-%d") if hasattr(n["date"], "strftime") else n["date"],
                        "note": n["note"],
                    }
                    for n in value
                ]

                if current_user.role != "admin":
                    # Non-admin: append to existing notes only
                    existing = getattr(customer, "notes") or []
                    customer.notes = existing + sanitized_notes
                else:
                    # Admin: can overwrite notes fully
                    customer.notes = sanitized_notes
            else:
                setattr(customer, key, value)

        db.add(customer)
        db.commit()
        db.refresh(customer)

        # 6️⃣ Return with assigned_to_name resolved
        return add_user_name(db, customer)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update customer: {str(e)}")


# -------------------------------
# Find customer by ID
# -------------------------------
@router.get("/find/{customer_id}", response_model=CustomerReadSchema, status_code=status.HTTP_200_OK)
def find_customer_by_id(
    customer_id: str = Path(..., description="Customer ID like ARC001"),
    db: Session = Depends(get_session),
    filter_stmt=Depends(filter_customers_by_user)
):
    try:
        code = customer_id.strip().upper()
        stmt = filter_stmt(select(CustomerModel)).where(CustomerModel.customer_id == code)

        result = db.exec(stmt).one_or_none()
        if not result:
            raise HTTPException(status_code=404, detail="Customer not found or access denied")

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to find customer: {str(e)}")
    

    

@router.get("/customers/count_and_graph", status_code=status.HTTP_200_OK)
def customers_count_and_graph(db: Session = Depends(get_session)):
    try:
        # Today’s date string in YYYY-MM-DD format (for date fields)
        today_date = datetime.now().date()

        # --- Today counts ---
        # 1) ACTIVE today -> based on reg_date
        active_today_stmt = select(func.count()).where(
            CustomerModel.status == "ACTIVE",
            CustomerModel.reg_date == today_date
        )
        active_today = db.exec(active_today_stmt).one()

        # 2) OnHold today -> based on hold_since
        onhold_today_stmt = select(func.count()).where(
            CustomerModel.status == "HOLD",
            CustomerModel.hold_since == today_date
        )
        onhold_today = db.exec(onhold_today_stmt).one()

        # --- Last 30 days graph ---
        # Initialize structures
        graph = {
            "ACTIVE": {"dates_x_axis": [], "dates_y_axis": []},
            "OnHold": {"dates_x_axis": [], "dates_y_axis": []},
        }

        # Iterate last 30 days (oldest to newest)
        start_day = today_date - timedelta(days=29)
        for i in range(30):
            day = start_day + timedelta(days=i)

            # ACTIVE on this day by reg_date
            active_day_stmt = select(func.count()).where(
                CustomerModel.status == "ACTIVE",
                CustomerModel.reg_date == day
            )
            active_count = db.exec(active_day_stmt).one()

            # OnHold on this day by hold_since
            onhold_day_stmt = select(func.count()).where(
                CustomerModel.status == "HOLD",
                CustomerModel.hold_since == day
            )
            onhold_count = db.exec(onhold_day_stmt).one()

            day_str = day.strftime("%Y-%m-%d")
            graph["ACTIVE"]["dates_x_axis"].append(day_str)
            graph["ACTIVE"]["dates_y_axis"].append(active_count)
            graph["OnHold"]["dates_x_axis"].append(day_str)
            graph["OnHold"]["dates_y_axis"].append(onhold_count)

        return {
            "count": {
                "date": today_date.strftime("%Y-%m-%d"),
                "total_active_today": active_today,
                "total_on_hold_today": onhold_today,
            },
            "graph": graph,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to build counts/graph: {str(e)}")
