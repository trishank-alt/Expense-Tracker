from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Annotated
from expense_tracker.expensetracker import ExpenseTracker
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import jwt
from datetime import datetime, timedelta, timezone
import os

# ==================== CONFIG ====================

SECRET_KEY = os.getenv("JWT_SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY is not configured")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

app = FastAPI(title="Expense Tracker API", version="2.0.0")
expense_tracker = ExpenseTracker()
app.mount("/static", StaticFiles(directory="static"), name="static")

bearer_scheme = HTTPBearer()

# ==================== MODELS ====================

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class ExpenseCreate(BaseModel):
    amount: float = Field(gt=0)
    category: str
    notes: Optional[str] = None

# PATCH semantics → all optional
class ExpenseUpdate(BaseModel):
    amount: Optional[float] = Field(default=None, gt=0)
    category: Optional[str] = None
    notes: Optional[str] = None

class ExpenseResponse(BaseModel):
    id: int
    amount: float
    category: str
    notes: Optional[str]
    date: str

class IncomeUpdate(BaseModel):
    income: float = Field(gt=0)

# ==================== JWT HELPERS ====================

def create_access_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> int:
    """Decode the JWT and return the authenticated user_id."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user_id


# Convenient type alias used in route signatures
CurrentUser = Annotated[int, Depends(get_current_user)]

# ==================== BASIC ====================

@app.get("/")
def serve_home():
    return FileResponse("templates/index.html")

# ==================== AUTH ====================

@app.post("/register", status_code=201)
def register(user: UserRegister):
    success = expense_tracker.create_user(user.email, user.password)

    if not success:
        raise HTTPException(400, "Email already exists")

    return {"status": "registered"}


@app.post("/login")
def login(user: UserLogin):
    user_id = expense_tracker.verify_user(user.email, user.password)

    if not user_id:
        raise HTTPException(401, "Invalid credentials")

    token = create_access_token(user_id)

    return {
        "access_token": token,
        "token_type": "bearer",
    }

# ==================== EXPENSES ====================

@app.post("/me/expenses", response_model=ExpenseResponse, status_code=201)
def add_expense(expense: ExpenseCreate, current_user: CurrentUser):
    new_expense = expense_tracker.add_expense(
        current_user,
        expense.amount,
        expense.category,
        expense.notes or "",
    )
    return new_expense


@app.get("/me/expenses", response_model=list[ExpenseResponse])
def get_expenses(
    current_user: CurrentUser,
    category: Optional[str] = None,
):
    if category:
        return expense_tracker.get_expenses_by_category(current_user, category)
    return expense_tracker.get_expenses(current_user)


@app.get("/me/expenses/{expense_id}", response_model=ExpenseResponse)
def get_expense_by_id(expense_id: int, current_user: CurrentUser):
    expense = expense_tracker.get_expense_by_id(current_user, expense_id)

    if not expense:
        raise HTTPException(404, "Expense not found")

    return expense


@app.patch("/me/expenses/{expense_id}")
def update_expense(
    expense_id: int,
    expense: ExpenseUpdate,
    current_user: CurrentUser,
):
    updated = expense_tracker.edit_expense(
        current_user,
        expense_id,
        new_amount=expense.amount,
        new_category=expense.category,
        new_notes=expense.notes,
    )

    if not updated:
        raise HTTPException(404, "Expense not found")

    return {"status": "expense updated"}


@app.delete("/me/expenses/{expense_id}")
def delete_expense(expense_id: int, current_user: CurrentUser):
    deleted = expense_tracker.delete_expense(current_user, expense_id)

    if not deleted:
        raise HTTPException(404, "Expense not found")

    return {"status": "expense deleted"}


@app.delete("/me/expenses")
def clear_all_expenses(current_user: CurrentUser):
    expense_tracker.clear_expenses(current_user)
    return {"status": "all expenses cleared"}

# ==================== INCOME ====================

@app.put("/me/income")
def update_income(data: IncomeUpdate, current_user: CurrentUser):
    expense_tracker.update_income(current_user, data.income)

    return {
        "status": "income updated",
        "income": data.income,
    }


@app.get("/me/income")
def get_income(current_user: CurrentUser):
    return {"income": expense_tracker.get_income(current_user)}


@app.get("/me/savings")
def get_savings(current_user: CurrentUser):
    return {"savings": expense_tracker.get_savings(current_user)}

# ==================== SUMMARY ====================

@app.get("/me/summary")
def get_summary(current_user: CurrentUser):
    return {
        "total_expenses": expense_tracker.total_expenses(current_user),
        "category_summary": expense_tracker.category_summary(current_user),
        "savings": expense_tracker.get_savings(current_user),
    }


@app.get("/me/summary/monthly")
def get_monthly_summary(
    current_user: CurrentUser,
    year: int,
    month: Annotated[int, Query(ge=1, le=12)],
):
    total = expense_tracker.monthly_summary(current_user, year, month)

    return {
        "year": year,
        "month": month,
        "total": total,
    }

# ==================== CLEANUP ====================

@app.delete("/me")
def delete_user_data(current_user: CurrentUser):
    expense_tracker.clear_expenses(current_user)
    expense_tracker.update_income(current_user, 0)

    return {"status": "user financial data cleared"}