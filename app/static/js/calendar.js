let currentWeekStart = getMonday(new Date());
let activeShiftId = null;

document.addEventListener("DOMContentLoaded", () => {
    renderWeek();
    document.getElementById("prev-week").addEventListener("click", () => shiftWeek(-7));
    document.getElementById("next-week").addEventListener("click", () => shiftWeek(7));
    document.getElementById("cancel-assign").addEventListener("click", closeModal);
    document.getElementById("confirm-assign").addEventListener("click", confirmAssignment);
});

function getMonday(date) {
    const d = new Date(date);
    const day = d.getDay();
    const diff = d.getDate() - day + (day === 0 ? -6 : 1);
    d.setDate(diff);
    d.setHours(0, 0, 0, 0);
    return d;
}

function formatDate(date) {
    return date.toISOString().split("T")[0];
}

function shiftWeek(days) {
    currentWeekStart.setDate(currentWeekStart.getDate() + days);
    renderWeek();
}

async function renderWeek() {
    const weekEnd = new Date(currentWeekStart);
    weekEnd.setDate(weekEnd.getDate() + 6);

    document.getElementById("week-label").textContent =
        `${formatDate(currentWeekStart)} — ${formatDate(weekEnd)}`;

    const shifts = await api.get(
        `/shifts?date_from=${formatDate(currentWeekStart)}&date_to=${formatDate(weekEnd)}`
    );

    renderGrid(shifts);
}

function renderGrid(shifts) {
    const grid = document.getElementById("calendar-grid");
    grid.innerHTML = "";

    const byDate = {};
    for (const shift of shifts) {
        if (!byDate[shift.shift_date]) byDate[shift.shift_date] = [];
        byDate[shift.shift_date].push(shift);
    }

    for (let i = 0; i < 7; i++) {
        const day = new Date(currentWeekStart);
        day.setDate(day.getDate() + i);
        const dateStr = formatDate(day);

        const column = document.createElement("div");
        column.className = "day-column";
        column.innerHTML = `<h4>${dateStr}</h4>`;

        const dayShifts = byDate[dateStr] || [];
        for (const shift of dayShifts) {
            const card = document.createElement("div");
            card.className = "shift-card";
            card.innerHTML = `
                <strong>${shift.department}</strong><br>
                ${shift.start_time}–${shift.end_time}<br>
                ${shift.assigned_count}/${shift.required_staff} Covered
                <button class="assign-btn" data-shift-id="${shift.id}">+ Assign</button>
            `;
            column.appendChild(card);
        }

        grid.appendChild(column);
    }

    document.querySelectorAll(".assign-btn").forEach((btn) => {
        btn.addEventListener("click", () => openModal(btn.dataset.shiftId));
    });
}

async function openModal(shiftId) {
    activeShiftId = shiftId;
    const candidates = await api.get(`/shifts/${shiftId}/candidates`);

    const select = document.getElementById("candidate-select");
    select.innerHTML = candidates
        .map((c) => `<option value="${c.id}">${c.full_name} (${c.role})</option>`)
        .join("");

    document.getElementById("assign-modal").classList.remove("hidden");
}

function closeModal() {
    document.getElementById("assign-modal").classList.add("hidden");
    activeShiftId = null;
}

async function confirmAssignment() {
    const employeeId = document.getElementById("candidate-select").value;
    try {
        await api.post(`/shifts/${activeShiftId}/assign`, { employee_id: Number(employeeId) });
        closeModal();
        renderWeek();
    } catch (err) {
        alert(err.message);
    }
}