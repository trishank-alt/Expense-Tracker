from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from expense_tracker.expensetracker import ExpenseTracker
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI(title="Expense Tracker API", version="1.0.0")
expense_tracker = ExpenseTracker()
app.mount("/static", StaticFiles(directory="static"), name="static")
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

# ==================== BASIC ====================

@app.get("/")
def serve_home():
    return FileResponse("templates/index.html")

# ==================== AUTH ====================

@app.post("/register")
def register(user: UserRegister):
    success = expense_tracker.create_user(user.email, user.password)

    if not success:
        raise HTTPException(400, "Email already exists")

    return {"status": "registered"}

@app.post("/login")
def login(user: UserLogin):
    # Later replace with JWT authentication
    user_id = expense_tracker.verify_user(user.email, user.password)

    if not user_id:
        raise HTTPException(401, "Invalid credentials")

    return {
        "status": "success",
        "user_id": user_id
    }

# ==================== EXPENSES ====================

@app.post("/users/{user_id}/expenses")
def add_expense(user_id: int, expense: ExpenseCreate):
    expense_tracker.add_expense(
        user_id,
        expense.amount,
        expense.category,
        expense.notes or ""
    )

    return {"status": "expense created"}

@app.get(
    "/users/{user_id}/expenses",
    response_model=list[ExpenseResponse]
)
def get_expenses(user_id: int):
    return expense_tracker.get_expenses(user_id)

@app.get(
    "/users/{user_id}/expenses/{expense_id}",
    response_model=ExpenseResponse
)
def get_expense_by_id(user_id: int, expense_id: int):
    expense = expense_tracker.get_expense_by_id(user_id, expense_id)

    if not expense:
        raise HTTPException(404, "Expense not found")

    return expense

@app.get(
    "/users/{user_id}/expenses/category/{category}",
    response_model=list[ExpenseResponse]
)
def get_expenses_by_category(user_id: int, category: str):
    return expense_tracker.get_expenses_by_category(user_id, category)

@app.patch("/users/{user_id}/expenses/{expense_id}")
def update_expense(
    user_id: int,
    expense_id: int,
    expense: ExpenseUpdate
):
    updated = expense_tracker.edit_expense(
        user_id,
        expense_id,
        new_amount=expense.amount,
        new_category=expense.category,
        new_notes=expense.notes
    )

    if not updated:
        raise HTTPException(404, "Expense not found")

    return {"status": "expense updated"}

@app.delete("/users/{user_id}/expenses/{expense_id}")
def delete_expense(user_id: int, expense_id: int):
    deleted = expense_tracker.delete_expense(user_id, expense_id)

    if not deleted:
        raise HTTPException(404, "Expense not found")

    return {"status": "expense deleted"}

@app.delete("/users/{user_id}/expenses")
def clear_all_expenses(user_id: int):
    expense_tracker.clear_expenses(user_id)
    return {"status": "all expenses cleared"}

# ==================== INCOME ====================

@app.put("/users/{user_id}/income")
def update_income(user_id: int, data: IncomeUpdate):
    expense_tracker.update_income(user_id, data.income)

    return {
        "status": "income updated",
        "income": data.income
    }

@app.get("/users/{user_id}/income")
def get_income(user_id: int):
    return {
        "income": expense_tracker.get_income(user_id)
    }

@app.get("/users/{user_id}/savings")
def get_savings(user_id: int):
    return {
        "savings": expense_tracker.get_savings(user_id)
    }

# ==================== SUMMARY ====================

@app.get("/users/{user_id}/summary")
def get_summary(user_id: int):
    return {
        "total_expenses": expense_tracker.total_expenses(user_id),
        "category_summary": expense_tracker.category_summary(user_id),
        "savings": expense_tracker.get_savings(user_id)
    }

@app.get("/users/{user_id}/summary/monthly")
def get_monthly_summary(user_id: int, year: int, month: int):
    total = expense_tracker.monthly_summary(user_id, year, month)

    return {
        "year": year,
        "month": month,
        "total": total
    }

# ==================== CLEANUP ====================

@app.delete("/users/{user_id}")
def delete_user_data(user_id: int):
    expense_tracker.clear_expenses(user_id)
    expense_tracker.update_income(user_id, 0)

    return {"status": "user financial data cleared"}