// ---------- BOOTSTRAP ----------
console.log("Script loaded successfully.");

// ---------- LOAD & RENDER EXPENSES ----------
async function loadExpenses() {
    try {
        const res = await fetch("/expenses");
        if (!res.ok) {
            console.error("Failed to load expenses");
            return;
        }
        const expenses = await res.json();
        renderExpenses(expenses);
    } catch (err) {
        console.error("Error fetching expenses:", err);
    }
}

function renderExpenses(expenses) {
    const expenseList = document.getElementById("expense-list");
    expenseList.innerHTML = "";

    for (const exp of expenses) {
        const li = document.createElement("li");
        li.textContent = `${exp.category} • ₹${exp.amount}`;

        const delBtn = document.createElement("button");
        delBtn.textContent = "Delete";
        delBtn.onclick = () => deleteExpense(exp.id);

        li.appendChild(delBtn);
        expenseList.appendChild(li);
    }
}

// ---------- ADD EXPENSE ----------
const form = document.getElementById("expense-form");

if (form) {
    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const amount = document.getElementById("amount").value;
        const category = document.getElementById("category").value;

        try {
            const res = await fetch("/expenses", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ amount, category })
            });

            if (!res.ok) {
                console.error("Failed to add expense");
                return;
            }

            form.reset();
            loadExpenses();
            loadSavings();
        } catch (err) {
            console.error("Error adding expense:", err);
        }
    });
}

const incomeForm = document.getElementById("income-form");

if (incomeForm) {
    incomeForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        const income = document.getElementById("income").value;

        try {
            const res = await fetch("/income", {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ income })
            });

            if (!res.ok) {
                console.error("Failed to update income");
                return;
            }

            incomeForm.reset();
            loadSavings();
        } catch (err) {
            console.error("Error updating income:", err);
        }
    });
}


// ---------- DELETE EXPENSE ----------
async function deleteExpense(id) {
    try {
        const res = await fetch(`/expenses/${id}`, {
            method: "DELETE"
        });

        if (!res.ok) {
            console.error("Failed to delete expense");
            return;
        }

        loadExpenses();
        loadSavings();
    } catch (err) {
        console.error("Error deleting expense:", err);
    }
}

// ---------- LOAD SAVINGS ----------
async function loadSavings() {
    const savingsEl = document.getElementById("savings");
    if (!savingsEl) return;

    try {
        const res = await fetch("/savings");
        if (!res.ok) return;

        const data = await res.json();
        savingsEl.textContent = `Savings: ₹${data.savings}`;
    } catch (err) {
        console.error("Error loading savings:", err);
    }
}

const clearBtn = document.getElementById("clear-all");

clearBtn.addEventListener("click", async function () {
    const confirmClear = confirm("Are you sure you want to delete all expenses?");
    if (!confirmClear) return;

    await fetch("/expenses", { method: "DELETE" });
    loadExpenses();
});

// ---------- INITIAL LOAD ----------
loadExpenses();
loadSavings();
