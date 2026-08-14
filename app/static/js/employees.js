let editingEmployeeId = null;
let rolesCache = [];

document.addEventListener("DOMContentLoaded", async () => {
    await loadRoles();
    await loadEmployees();

    document.getElementById("new-employee-btn").addEventListener("click", () => openModal());
    document.getElementById("cancel-employee").addEventListener("click", closeModal);
    document.getElementById("employee-form").addEventListener("submit", handleSubmit);
});

async function loadRoles() {
    rolesCache = await api.get("/roles");
    const select = document.getElementById("role-select");
    select.innerHTML = rolesCache
        .map((r) => `<option value="${r.id}">${r.name}</option>`)
        .join("");
}

async function loadEmployees() {
    const employees = await api.get("/employees");
    renderTable(employees);
}

function renderTable(employees) {
    const tbody = document.getElementById("employees-body");
    tbody.innerHTML = "";

    for (const emp of employees) {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${emp.full_name}</td>
            <td>${emp.email}</td>
            <td>${emp.role}</td>
            <td>${emp.hire_date}</td>
            <td>${emp.is_active ? "Active" : "Inactive"}</td>
            <td>
                <button class="edit-btn" data-id="${emp.id}">Edit</button>
                <button class="delete-btn" data-id="${emp.id}">Delete</button>
            </td>
        `;
        tbody.appendChild(row);
    }

    document.querySelectorAll(".edit-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            const emp = employees.find((e) => e.id === Number(btn.dataset.id));
            openModal(emp);
        });
    });

    document.querySelectorAll(".delete-btn").forEach((btn) => {
        btn.addEventListener("click", () => handleDelete(Number(btn.dataset.id)));
    });
}

function openModal(employee = null) {
    editingEmployeeId = employee ? employee.id : null;

    document.getElementById("modal-title").textContent =
        employee ? "Employee Edit" : "New Employee";

    document.getElementById("full-name").value = employee ? employee.full_name : "";
    document.getElementById("email").value = employee ? employee.email : "";
    document.getElementById("phone").value = employee ? (employee.phone || "") : "";

    if (employee) {
        const role = rolesCache.find((r) => r.name === employee.role);
        if (role) document.getElementById("role-select").value = role.id;
    }

    document.getElementById("employee-modal").classList.remove("hidden");
}

function closeModal() {
    document.getElementById("employee-modal").classList.add("hidden");
    document.getElementById("employee-form").reset();
    editingEmployeeId = null;
}

async function handleSubmit(event) {
    event.preventDefault();

    const payload = {
        full_name: document.getElementById("full-name").value,
        email: document.getElementById("email").value,
        phone: document.getElementById("phone").value || null,
        role_id: Number(document.getElementById("role-select").value),
    };

    try {
        if (editingEmployeeId) {
            await api.put(`/employees/${editingEmployeeId}`, payload);
        } else {
            await api.post("/employees", payload);
        }
        closeModal();
        await loadEmployees();
    } catch (err) {
        alert(err.message);
    }
}

async function handleDelete(id) {
    if (!confirm("Are you sure you want to delete this employee?")) return;

    try {
        await api.delete(`/employees/${id}`);
        await loadEmployees();
    } catch (err) {
        alert(err.message);
    }
}