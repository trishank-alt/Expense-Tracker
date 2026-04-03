# from flask import Flask, jsonify, request, render_template  
# from expense_tracker.expensetracker import ExpenseTracker
# app = Flask(__name__)
# expensetracker = ExpenseTracker()
# @app.get("/expenses")
# def get_expenses():
#     category = request.args.get("category")
#     if not category:
#         expenses = expensetracker.get_expenses()
#     else:
#         expenses = expensetracker.get_expenses_by_category(category)
#     if expenses is None:
#         return jsonify([]), 200
#     return jsonify(expenses)
# @app.post("/expenses")
# def add_expense():
#     data = request.get_json()

#     if not data:
#         return jsonify({"error": {
#             "message" : "JSON body required"
#             }}), 400
#     amount = data.get("amount")
#     category = data.get("category")
#     notes = data.get("notes", "")
#     if amount is None or category is None:
#         return jsonify({"error": {
#             "message" : "amount and category are required"
#             }}), 400

#     try:
#         amount = float(amount)
#     except ValueError:
#         return jsonify({"error": {
#             "message" : "amount must be a number"
#             }}), 4000
#     expense = expensetracker.add_expense(amount, category, notes)

#     return jsonify(expense), 201

# @app.delete("/expenses/<int:expense_id>")
# def delete_expense(expense_id):
#     success = expensetracker.delete_expense(expense_id)
#     if not success:
#         return jsonify({
#             "error": {
#                 "message": "expense not found"
#             }
#         }), 404
#     return jsonify({"status": "deleted"}), 200

# @app.get("/expenses/<int:expense_id>")
# def get_expense(expense_id):
#     expense = expensetracker.get_expense_by_id(expense_id)
#     if not expense:
#         return jsonify({
#             "error": {
#                 "message": "expense not found"
#             }
#         }), 404
#     return jsonify(expense), 200

# @app.put("/income")
# def update_income():
#     data = request.get_json()
#     if not data or "income" not in data:
#         return jsonify({"error": {
#             "message" : "income is required"
#             }}), 400    
#     try:
#         income = float(data.get("income"))
#     except ValueError:
#         return jsonify({"error": {
#             "message" : "income must be a number"
#             }}), 400
#     expensetracker.update_income(income)
#     return jsonify({"status": "income updated"}), 200

# @app.get("/savings")
# def get_savings():
#     savings = expensetracker.get_savings()
#     return jsonify({"savings": savings}), 200

# @app.get("/")
# def index():
#     return render_template("index.html")

# @app.delete("/expenses")
# def clear_expenses():
#     expensetracker.clear_expenses()
#     return jsonify({"status": "all expenses cleared"}), 200


# if __name__ == "__main__":
#     app.run(debug=True)


from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from expense_tracker.expensetracker import ExpenseTracker

app = FastAPI()
expensetracker = ExpenseTracker()

class Expense(BaseModel):
    amount: float = Field(gt=0)
    category: str
    notes: str = ""

@app.get("/")
def home():
    return {"message": "Welcome to the Expense Tracker API"}

@app.post("/users/{user_id}/expenses")
def add_expense(user_id: int, expense: Expense):
    return expensetracker.add_expense(user_id, expense.amount, expense.category, expense.notes)

# @app.get("/users/{user_id}/expenses")
# def get_expenses(user_id: int, category: str = None):
#     if category:
#         return expensetracker.get_expenses_by_category(user_id, category)
#     return expensetracker.get_expenses(user_id) or []

@app.get("/users/{user_id}/expenses/{expense_id}")
def get_expense_by_id(user_id: int, expense_id: int):
    expense = expensetracker.get_expense_by_id(user_id, expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense

@app.delete("/users/{user_id}/expenses/{expense_id}")
def delete_expense(user_id: int, expense_id: int):
    success = expensetracker.delete_expense(user_id, expense_id)
    if not success:
        raise HTTPException(status_code=404, detail="Expense not found")
    return {"status": "deleted"}

@app.put("/users/{user_id}/income")
def update_income(user_id: int, income: float = Field(gt=0)):
    expensetracker.update_income(user_id, income)
    return {"status": "income updated"}

@app.get("/users/{user_id}/savings")
def get_savings(user_id: int):
    savings = expensetracker.get_savings(user_id)
    if savings is None:
        raise HTTPException(status_code=404, detail="Savings not found")
    return {"savings": savings}

@app.delete("/users/{user_id}/expenses")
def clear_all_expenses(user_id: int):
    expensetracker.clear_expenses(user_id)
    return {"status": "all expenses cleared"}