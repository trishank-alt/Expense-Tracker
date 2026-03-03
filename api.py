from flask import Flask, jsonify, request, render_template  
from expense_tracker.expensetracker import ExpenseTracker
app = Flask(__name__)
expensetracker = ExpenseTracker()
@app.get("/expenses")
def get_expenses():
    category = request.args.get("category")
    if not category:
        expenses = expensetracker.get_expenses()
    else:
        expenses = expensetracker.get_expenses_by_category(category)
    if expenses is None:
        return jsonify([]), 200
    return jsonify(expenses)
@app.post("/expenses")
def add_expense():
    data = request.get_json()

    if not data:
        return jsonify({"error": {
            "message" : "JSON body required"
            }}), 400
    amount = data.get("amount")
    category = data.get("category")
    notes = data.get("notes", "")
    if amount is None or category is None:
        return jsonify({"error": {
            "message" : "amount and category are required"
            }}), 400

    try:
        amount = float(amount)
    except ValueError:
        return jsonify({"error": {
            "message" : "amount must be a number"
            }}), 4000
    expense = expensetracker.add_expense(amount, category, notes)

    return jsonify(expense), 201

@app.delete("/expenses/<int:expense_id>")
def delete_expense(expense_id):
    success = expensetracker.delete_expense(expense_id)
    if not success:
        return jsonify({
            "error": {
                "message": "expense not found"
            }
        }), 404
    return jsonify({"status": "deleted"}), 200

@app.get("/expenses/<int:expense_id>")
def get_expense(expense_id):
    expense = expensetracker.get_expense_by_id(expense_id)
    if not expense:
        return jsonify({
            "error": {
                "message": "expense not found"
            }
        }), 404
    return jsonify(expense), 200

@app.put("/income")
def update_income():
    data = request.get_json()
    if not data or "income" not in data:
        return jsonify({"error": {
            "message" : "income is required"
            }}), 400    
    try:
        income = float(data.get("income"))
    except ValueError:
        return jsonify({"error": {
            "message" : "income must be a number"
            }}), 400
    expensetracker.update_income(income)
    return jsonify({"status": "income updated"}), 200

@app.get("/savings")
def get_savings():
    savings = expensetracker.get_savings()
    return jsonify({"savings": savings}), 200

@app.get("/")
def index():
    return render_template("index.html")

@app.delete("/expenses")
def clear_expenses():
    expensetracker.clear_expenses()
    return jsonify({"status": "all expenses cleared"}), 200


if __name__ == "__main__":
    app.run(debug=True)
