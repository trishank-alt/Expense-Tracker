// =====================================================================
//  DarkPulse Expense Tracker — Frontend Script
//  Covers: Auth, Expenses CRUD, Income, Savings, Summary, Monthly
// =====================================================================

"use strict";

// ─── CONSTANTS ───────────────────────────────────────────────────────
const TOKEN_KEY = "dp_token";
const EMAIL_KEY = "dp_email";

// ─── TOKEN STORE ─────────────────────────────────────────────────────
const Auth = {
    getToken()          { return localStorage.getItem(TOKEN_KEY); },
    getEmail()          { return localStorage.getItem(EMAIL_KEY); },
    save(token, email)  { localStorage.setItem(TOKEN_KEY, token); localStorage.setItem(EMAIL_KEY, email); },
    clear()             { localStorage.removeItem(TOKEN_KEY); localStorage.removeItem(EMAIL_KEY); },
    isLoggedIn()        { return !!this.getToken(); },
};

// ─── GENERIC API HELPER ───────────────────────────────────────────────
async function api(method, path, body = null) {
    const headers = { "Content-Type": "application/json" };
    const token = Auth.getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;

    const opts = { method, headers };
    if (body !== null) opts.body = JSON.stringify(body);

    const res = await fetch(path, opts);

    if (res.status === 401) {
        // Token expired or invalid — force logout
        Auth.clear();
        showAuth();
        toast("Session expired. Please sign in again.", "error");
        throw new Error("Unauthorized");
    }

    return res;
}

// ─── TOAST ────────────────────────────────────────────────────────────
function toast(message, type = "info") {
    const container = document.getElementById("toast-container");
    const el = document.createElement("div");
    el.className = `toast ${type}`;

    const icon = type === "success" ? "✓" : type === "error" ? "✕" : "ℹ";
    el.innerHTML = `<span>${icon}</span> ${message}`;

    container.appendChild(el);
    setTimeout(() => el.remove(), 3100);
}

// ─── AUTH UI ─────────────────────────────────────────────────────────
function showAuth() {
    document.getElementById("auth-overlay").classList.add("visible");
    document.getElementById("app-dashboard").classList.remove("visible");
    document.getElementById("btn-open-auth").style.display = "inline-block";
    document.getElementById("btn-logout").style.display = "none";
    document.getElementById("nav-user-email").textContent = "";
}

function showDashboard() {
    document.getElementById("auth-overlay").classList.remove("visible");
    document.getElementById("app-dashboard").classList.add("visible");
    document.getElementById("btn-open-auth").style.display = "none";
    document.getElementById("btn-logout").style.display = "inline-block";
    document.getElementById("nav-user-email").textContent = Auth.getEmail() || "";
    loadDashboard();
}

// Auth tabs
document.querySelectorAll(".auth-tab").forEach(tab => {
    tab.addEventListener("click", () => {
        document.querySelectorAll(".auth-tab").forEach(t => t.classList.remove("active"));
        document.querySelectorAll(".auth-form").forEach(f => f.classList.remove("active"));
        tab.classList.add("active");
        document.getElementById(`form-${tab.dataset.tab}`).classList.add("active");

        // Update header copy
        const box = document.querySelector(".auth-box h2");
        const sub = document.querySelector(".auth-box .auth-subtitle");
        if (tab.dataset.tab === "login") {
            box.textContent = "Welcome back";
            sub.textContent = "Sign in to access your dashboard";
        } else {
            box.textContent = "Create account";
            sub.textContent = "Join DarkPulse — it's free";
        }
    });
});

// Open auth button (when not logged in and user clicks Sign In)
document.getElementById("btn-open-auth").addEventListener("click", () => {
    document.getElementById("auth-overlay").classList.add("visible");
});

// Login
document.getElementById("form-login").addEventListener("submit", async (e) => {
    e.preventDefault();
    const errEl = document.getElementById("login-error");
    errEl.classList.remove("visible");

    const email    = document.getElementById("login-email").value.trim();
    const password = document.getElementById("login-password").value;

    try {
        const res = await fetch("/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password }),
        });

        if (!res.ok) {
            const data = await res.json().catch(() => ({}));
            errEl.textContent = data.detail || "Invalid credentials";
            errEl.classList.add("visible");
            return;
        }

        const data = await res.json();
        Auth.save(data.access_token, email);
        toast("Signed in successfully!", "success");
        showDashboard();
    } catch {
        errEl.textContent = "Network error. Try again.";
        errEl.classList.add("visible");
    }
});

// Register
document.getElementById("form-register").addEventListener("submit", async (e) => {
    e.preventDefault();
    const errEl = document.getElementById("register-error");
    errEl.classList.remove("visible");

    const email    = document.getElementById("reg-email").value.trim();
    const password = document.getElementById("reg-password").value;

    try {
        const res = await fetch("/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password }),
        });

        if (!res.ok) {
            const data = await res.json().catch(() => ({}));
            errEl.textContent = data.detail || "Registration failed";
            errEl.classList.add("visible");
            return;
        }

        toast("Account created! Signing you in…", "success");

        // Auto-login after register
        const loginRes = await fetch("/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password }),
        });

        if (loginRes.ok) {
            const loginData = await loginRes.json();
            Auth.save(loginData.access_token, email);
            showDashboard();
        }
    } catch {
        errEl.textContent = "Network error. Try again.";
        errEl.classList.add("visible");
    }
});

// Logout
document.getElementById("btn-logout").addEventListener("click", () => {
    Auth.clear();
    toast("Signed out.", "info");
    showAuth();
});

// ─── DASHBOARD LOADER ─────────────────────────────────────────────────
async function loadDashboard() {
    await Promise.all([
        loadStatsBar(),
        loadExpenses(),
        loadSummary(),
    ]);
    prefillMonthYear();
}

// ─── STATS BAR ────────────────────────────────────────────────────────
async function loadStatsBar() {
    try {
        const [incomeRes, savingsRes, summaryRes] = await Promise.all([
            api("GET", "/me/income"),
            api("GET", "/me/savings"),
            api("GET", "/me/summary"),
        ]);

        if (incomeRes.ok) {
            const { income } = await incomeRes.json();
            document.getElementById("stat-income").textContent = formatCurrency(income);
            // Pre-fill income input
            document.getElementById("income-input").value = income > 0 ? income : "";
        }

        if (savingsRes.ok) {
            const { savings } = await savingsRes.json();
            const el = document.getElementById("stat-savings");
            el.textContent = formatCurrency(savings);
            el.classList.toggle("negative", savings < 0);
        }

        if (summaryRes.ok) {
            const { total_expenses } = await summaryRes.json();
            document.getElementById("stat-spent").textContent = formatCurrency(total_expenses);
        }
    } catch { /* silently handled by api() */ }
}

// ─── EXPENSES ─────────────────────────────────────────────────────────
let activeFilter = null;

async function loadExpenses(category = null) {
    try {
        const url = category
            ? `/me/expenses?category=${encodeURIComponent(category)}`
            : "/me/expenses";
        const res = await api("GET", url);
        if (!res.ok) return;
        const expenses = await res.json();
        renderExpenses(expenses);
    } catch { /* handled */ }
}

function renderExpenses(expenses) {
    const list = document.getElementById("expense-list");
    list.innerHTML = "";

    if (!expenses.length) {
        list.innerHTML = `
          <div class="expense-empty">
            <span>🧾</span>
            No expenses found. Add one above!
          </div>`;
        return;
    }

    for (const exp of expenses) {
        const li = document.createElement("li");

        const dateStr = exp.date ? new Date(exp.date).toLocaleDateString("en-IN", {
            day: "numeric", month: "short", year: "numeric"
        }) : "";

        li.innerHTML = `
          <div class="expense-info">
            <div class="expense-category">
              <span class="category-pill">${escHtml(exp.category)}</span>
            </div>
            ${exp.notes ? `<div class="expense-notes">📝 ${escHtml(exp.notes)}</div>` : ""}
            <div class="expense-date">${dateStr}</div>
          </div>
          <div class="expense-amount">₹${formatNum(exp.amount)}</div>
          <div class="expense-actions">
            <button class="btn-edit" data-id="${exp.id}">Edit</button>
            <button class="btn-del"  data-id="${exp.id}">Delete</button>
          </div>`;

        li.querySelector(".btn-edit").addEventListener("click", () => openEditModal(exp));
        li.querySelector(".btn-del").addEventListener("click", () => deleteExpense(exp.id));

        list.appendChild(li);
    }
}

// ─── ADD EXPENSE ──────────────────────────────────────────────────────
document.getElementById("expense-form").addEventListener("submit", async (e) => {
    e.preventDefault();

    const amount   = parseFloat(document.getElementById("exp-amount").value);
    const category = document.getElementById("exp-category").value.trim();
    const notes    = document.getElementById("exp-notes").value.trim();

    try {
        const res = await api("POST", "/me/expenses", { amount, category, notes: notes || null });
        if (!res.ok) { toast("Failed to add expense.", "error"); return; }

        document.getElementById("expense-form").reset();
        toast("Expense added!", "success");
        await Promise.all([loadExpenses(activeFilter), loadStatsBar(), loadSummary()]);
    } catch { /* handled */ }
});

// ─── DELETE EXPENSE ───────────────────────────────────────────────────
async function deleteExpense(id) {
    if (!confirm("Delete this expense?")) return;
    try {
        const res = await api("DELETE", `/me/expenses/${id}`);
        if (!res.ok) { toast("Failed to delete.", "error"); return; }
        toast("Expense deleted.", "success");
        await Promise.all([loadExpenses(activeFilter), loadStatsBar(), loadSummary()]);
    } catch { /* handled */ }
}

// ─── CLEAR ALL EXPENSES ───────────────────────────────────────────────
document.getElementById("btn-clear-all").addEventListener("click", async () => {
    if (!confirm("Delete ALL expenses? This cannot be undone.")) return;
    try {
        const res = await api("DELETE", "/me/expenses");
        if (!res.ok) { toast("Failed to clear expenses.", "error"); return; }
        toast("All expenses cleared.", "success");
        activeFilter = null;
        updateFilterBadge();
        await Promise.all([loadExpenses(), loadStatsBar(), loadSummary()]);
    } catch { /* handled */ }
});

// ─── EDIT EXPENSE ─────────────────────────────────────────────────────
function openEditModal(exp) {
    document.getElementById("edit-id").value       = exp.id;
    document.getElementById("edit-amount").value   = exp.amount;
    document.getElementById("edit-category").value = exp.category;
    document.getElementById("edit-notes").value    = exp.notes || "";
    document.getElementById("edit-modal").classList.add("visible");
}

document.getElementById("btn-cancel-edit").addEventListener("click", () => {
    document.getElementById("edit-modal").classList.remove("visible");
});

// Close modal on backdrop click
document.getElementById("edit-modal").addEventListener("click", (e) => {
    if (e.target === e.currentTarget) {
        document.getElementById("edit-modal").classList.remove("visible");
    }
});

document.getElementById("edit-form").addEventListener("submit", async (e) => {
    e.preventDefault();

    const id       = parseInt(document.getElementById("edit-id").value);
    const amount   = parseFloat(document.getElementById("edit-amount").value);
    const category = document.getElementById("edit-category").value.trim();
    const notes    = document.getElementById("edit-notes").value.trim();

    try {
        const res = await api("PATCH", `/me/expenses/${id}`, {
            amount,
            category,
            notes: notes || null,
        });

        if (!res.ok) { toast("Failed to update expense.", "error"); return; }

        document.getElementById("edit-modal").classList.remove("visible");
        toast("Expense updated!", "success");
        await Promise.all([loadExpenses(activeFilter), loadStatsBar(), loadSummary()]);
    } catch { /* handled */ }
});

// ─── CATEGORY FILTER ─────────────────────────────────────────────────
document.getElementById("btn-filter").addEventListener("click", applyFilter);
document.getElementById("filter-input").addEventListener("keydown", (e) => {
    if (e.key === "Enter") applyFilter();
});

function applyFilter() {
    const val = document.getElementById("filter-input").value.trim();
    if (!val) {
        toast("Enter a category to filter.", "info");
        return;
    }
    activeFilter = val;
    updateFilterBadge();
    loadExpenses(activeFilter);
}

document.getElementById("btn-clear-filter").addEventListener("click", () => {
    activeFilter = null;
    document.getElementById("filter-input").value = "";
    updateFilterBadge();
    loadExpenses();
});

function updateFilterBadge() {
    const badge = document.getElementById("filter-badge");
    const label = document.getElementById("filter-label");
    if (activeFilter) {
        label.textContent = activeFilter;
        badge.classList.add("visible");
    } else {
        badge.classList.remove("visible");
    }
}

// ─── INCOME ───────────────────────────────────────────────────────────
document.getElementById("income-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const income = parseFloat(document.getElementById("income-input").value);
    try {
        const res = await api("PUT", "/me/income", { income });
        if (!res.ok) { toast("Failed to update income.", "error"); return; }
        toast("Income updated!", "success");
        await loadStatsBar();
    } catch { /* handled */ }
});

// ─── SUMMARY (Category Breakdown) ────────────────────────────────────
async function loadSummary() {
    try {
        const res = await api("GET", "/me/summary");
        if (!res.ok) return;
        const { category_summary, total_expenses } = await res.json();
        renderCategoryTable(category_summary, total_expenses);
    } catch { /* handled */ }
}

function renderCategoryTable(summary, total) {
    const tbody = document.querySelector("#category-table tbody");
    tbody.innerHTML = "";

    if (!summary || !summary.length) {
        tbody.innerHTML = `<tr><td colspan="2" style="color:var(--muted);padding:1rem 0;text-align:center">No data yet</td></tr>`;
        return;
    }

    for (const row of summary) {
        const pct = total > 0 ? Math.round((row.total / total) * 100) : 0;
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td>
            <div>${escHtml(row.category)}</div>
            <div class="category-bar-wrap">
              <div class="category-bar" style="width:${pct}%"></div>
            </div>
          </td>
          <td>₹${formatNum(row.total)} <span style="color:var(--muted);font-size:0.78rem">${pct}%</span></td>`;
        tbody.appendChild(tr);
    }
}

// ─── MONTHLY SUMMARY ──────────────────────────────────────────────────
function prefillMonthYear() {
    const now = new Date();
    document.getElementById("monthly-month").value = now.getMonth() + 1;
    document.getElementById("monthly-year").value  = now.getFullYear();
}

document.getElementById("btn-monthly").addEventListener("click", async () => {
    const month = parseInt(document.getElementById("monthly-month").value);
    const year  = parseInt(document.getElementById("monthly-year").value);

    if (!year || year < 2000 || year > 2100) {
        toast("Enter a valid year (2000–2100).", "error");
        return;
    }

    try {
        const res = await api("GET", `/me/summary/monthly?year=${year}&month=${month}`);
        if (!res.ok) { toast("Failed to load monthly summary.", "error"); return; }
        const data = await res.json();

        const monthName = new Date(year, month - 1).toLocaleString("en-IN", { month: "long" });
        document.getElementById("monthly-label").textContent = `${monthName} ${year}`;
        document.getElementById("monthly-total").textContent = `₹${formatNum(data.total)}`;
        document.getElementById("monthly-result").classList.add("visible");
    } catch { /* handled */ }
});

// ─── DELETE ALL USER DATA ─────────────────────────────────────────────
document.getElementById("btn-delete-data").addEventListener("click", async () => {
    if (!confirm("This will permanently delete ALL your expenses and reset your income to ₹0. Are you absolutely sure?")) return;
    try {
        const res = await api("DELETE", "/me");
        if (!res.ok) { toast("Failed to delete data.", "error"); return; }
        toast("All financial data cleared.", "success");
        await loadDashboard();
    } catch { /* handled */ }
});

// ─── FORMATTING HELPERS ───────────────────────────────────────────────
function formatCurrency(val) {
    if (val === null || val === undefined) return "—";
    return `₹${formatNum(val)}`;
}

function formatNum(val) {
    return Number(val).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function escHtml(str) {
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}

// ─── INIT ─────────────────────────────────────────────────────────────
(function init() {
    if (Auth.isLoggedIn()) {
        showDashboard();
    } else {
        showAuth();
        // Make hero CTA open auth instead of scrolling to empty dashboard
        document.getElementById("hero-cta").addEventListener("click", (e) => {
            e.preventDefault();
            document.getElementById("auth-overlay").classList.add("visible");
        });
    }
})();
