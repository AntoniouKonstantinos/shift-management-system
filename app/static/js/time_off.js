document.addEventListener("DOMContentLoaded", async () => {
    await loadEmployeesDropdown();
    await loadRequests();

    document.getElementById("new-request-btn").addEventListener("click", openModal);
    document.getElementById("cancel-request").addEventListener("click", closeModal);
    document.getElementById("request-form").addEventListener("submit", handleSubmit);
    document.getElementById("status-filter").addEventListener("change", loadRequests);
});

async function loadEmployeesDropdown() {
    const employees = await api.get("/employees");
    const select = document.getElementById("employee-select");
    select.innerHTML = employees
        .map((e) => `<option value="${e.id}">${e.full_name}</option>`)
        .join("");
}

async function loadRequests() {
    const status = document.getElementById("status-filter").value;
    const query = status ? `?status=${status}` : "";
    const requests = await api.get(`/time-off${query}`);
    renderTable(requests);
}

function renderTable(requests) {
    const tbody = document.getElementById("time-off-body");
    tbody.innerHTML = "";

    for (const req of requests) {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${req.employee_name}</td>
            <td>${req.start_date}</td>
            <td>${req.end_date}</td>
            <td>${req.reason || "—"}</td>
            <td><span class="status-badge status-${req.status}">${statusLabel(req.status)}</span></td>
            <td>${renderActions(req)}</td>
        `;
        tbody.appendChild(row);
    }

    document.querySelectorAll(".approve-btn").forEach((btn) => {
        btn.addEventListener("click", () => handleDecision(btn.dataset.id, "approve"));
    });
    document.querySelectorAll(".reject-btn").forEach((btn) => {
        btn.addEventListener("click", () => handleDecision(btn.dataset.id, "reject"));
    });
    document.querySelectorAll(".delete-btn").forEach((btn) => {
        btn.addEventListener("click", () => handleDelete(btn.dataset.id));
    });
}

function statusLabel(status) {
    const labels = { pending: "Εκκρεμεί", approved: "Εγκεκριμένη", rejected: "Απορρίφθηκε" };
    return labels[status] || status;
}

function renderActions(req) {
    if (req.status === "pending") {
        return `
            <button class="approve-btn" data-id="${req.id}">Έγκριση</button>
            <button class="reject-btn" data-id="${req.id}">Απόρριψη</button>
        `;
    }
    return `<button class="delete-btn" data-id="${req.id}">Διαγραφή</button>`;
}

function openModal() {
    document.getElementById("request-modal").classList.remove("hidden");
}

function closeModal() {
    document.getElementById("request-modal").classList.add("hidden");
    document.getElementById("request-form").reset();
}

async function handleSubmit(event) {
    event.preventDefault();

    const startDate = document.getElementById("start-date").value;
    const endDate = document.getElementById("end-date").value;

    const payload = {
        employee_id: Number(document.getElementById("employee-select").value),
        start_date: startDate,
        end_date: endDate,
        reason: document.getElementById("reason").value || null,
    };

    try {
        await api.post("/time-off", payload);
        closeModal();
        await loadRequests();
    } catch (err) {
        alert(err.message);
    }
}

async function handleDecision(id, decision) {
    try {
        await api.patch(`/time-off/${id}/${decision}`, {});
        await loadRequests();
    } catch (err) {
        alert(err.message);
    }
}

async function handleDelete(id) {
    if (!confirm("Διαγραφή αυτού του αιτήματος;")) return;

    try {
        await api.delete(`/time-off/${id}`);
        await loadRequests();
    } catch (err) {
        alert(err.message);
    }
}