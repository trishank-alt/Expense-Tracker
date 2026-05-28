# Expense Tracker API

A lightweight backend-first expense tracking system built with **FastAPI**, **SQLite**, and **bcrypt authentication**.
Designed as a learning-focused backend project exploring API architecture, authentication, CRUD operations, financial summaries, and database design.

---

# Features

## Authentication

* User registration
* Secure password hashing with `bcrypt`
* Login verification system

## Expense Management

* Add expenses
* Edit expenses
* Delete expenses
* Clear all expenses
* Get expense by ID
* Filter expenses by category

## Financial Tracking

* Income tracking
* Savings calculation
* Monthly summaries
* Category-wise spending breakdown

## Backend Engineering

* REST API design
* SQLite relational database
* Indexed queries
* Pydantic validation
* Structured backend layering

---

# Tech Stack

| Technology | Purpose               |
| ---------- | --------------------- |
| FastAPI    | Backend API framework |
| SQLite     | Database              |
| bcrypt     | Password hashing      |
| Pydantic   | Request validation    |
| Python     | Core language         |

---

# Project Structure

```text
expense-tracker/
│
├── expense_tracker/
│   └── expensetracker.py
│
├── templates/
│   └── index.html
│
├── static/
│
├── main.py
├── expenses.db
├── requirements.txt
└── README.md
```

---

# API Endpoints

## Authentication

### Register

```http
POST /register
```

### Login

```http
POST /login
```

---

## Expenses

### Add Expense

```http
POST /users/{user_id}/expenses
```

### Get All Expenses

```http
GET /users/{user_id}/expenses
```

### Get Expense By ID

```http
GET /users/{user_id}/expenses/{expense_id}
```

### Update Expense

```http
PATCH /users/{user_id}/expenses/{expense_id}
```

### Delete Expense

```http
DELETE /users/{user_id}/expenses/{expense_id}
```

### Clear All Expenses

```http
DELETE /users/{user_id}/expenses
```

---

## Income

### Update Income

```http
PUT /users/{user_id}/income
```

### Get Income

```http
GET /users/{user_id}/income
```

### Get Savings

```http
GET /users/{user_id}/savings
```

---

## Summaries

### Overall Summary

```http
GET /users/{user_id}/summary
```

### Monthly Summary

```http
GET /users/{user_id}/summary/monthly
```

---

# Installation

## Clone Repository

```bash
git clone https://github.com/your-username/expense-tracker.git
cd expense-tracker
```

---

## Create Virtual Environment

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Linux / Mac

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Run Server

```bash
uvicorn main:app --reload
```

---

# API Docs

FastAPI automatically generates Swagger documentation.

Open:

```text
http://127.0.0.1:8000/docs
```

---

# Current Limitations

This project is currently a backend-focused learning project and still lacks several production-grade features:

* JWT authentication
* Proper authorization middleware
* Rate limiting
* PostgreSQL migration
* Refresh token flow
* Email verification
* Docker support
* CI/CD pipeline
* Automated tests

---

# Planned Improvements

* JWT-based authentication
* Role-based authorization
* PostgreSQL integration
* Dockerized deployment
* Analytics dashboard
* Budget alerts
* AI-powered expense insights
* Export reports (CSV/PDF)
* Pagination & filtering
* Redis caching

---

# Security Notes

The current version is intentionally simple and still vulnerable to authorization issues such as IDOR because route ownership is based on client-provided `user_id`.

Future versions will move to:

* token-based authentication
* middleware authorization
* server-derived identity

---

# Why This Project Exists

This project was built to explore:

* backend architecture
* database modeling
* authentication systems
* API security concepts
* scalable design thinking

The goal is not just CRUD functionality, but understanding how real backend systems evolve from simple prototypes into secure production services.

---

# Future Vision

The long-term direction is turning this into a more complete personal finance platform with:

* secure authentication
* analytics
* smart budgeting
* financial insights
* scalable infrastructure

---

# License

MIT License
