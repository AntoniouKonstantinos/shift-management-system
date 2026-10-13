# Shift Management System

A staff shift scheduling application built for restaurant and hospitality
businesses. Managers can create shifts, track employee availability, assign
staff based on real-time eligibility checks, and manage time-off requests —
all through a single-page web dashboard.

Built as a portfolio project with an emphasis on correct relational database
design and CRUD logic on top of real business rules, drawing on direct
industry experience in hospitality.

## Branches

| Branch | Frontend |
|---|---|
| `main` | Original version: Jinja2 templates + vanilla JavaScript, served by Flask |
| `angular-frontend` | This version: Angular single-page app consuming the Flask REST API |

The backend is identical in both branches. In this branch Flask is a pure
JSON API and serves no HTML pages.

## Features

- **Employee management** — create, edit, deactivate, and remove staff
  records, each linked to a role (waiter, chef, bartender, etc.).
- **Shift scheduling** — define shifts by department, date, and time range,
  with a required headcount per shift.
- **Smart assignment** — a candidates endpoint filters staff down to those
  who are actually eligible for a given shift, checking:
  - declared weekly availability
  - conflicting assignments on the same day
  - approved time-off periods
- **Time-off requests** — employees submit requests; managers approve or
  reject them through a dedicated workflow (not a generic field update).
- **Weekly calendar dashboard** — browse shifts week by week and assign
  staff directly from the grid.

## Screenshots

**Weekly calendar with staff assignment**
![Dashboard](screenshots/dashboard.png)

**Staff management**
![Employees](screenshots/employees.png)

**Time-off approval workflow**
![Time off](screenshots/time_off.png)

## Tech Stack

- **Backend:** Flask, Flask-SQLAlchemy (REST API only)
- **Database:** SQLite (swappable via `DATABASE_URL`)
- **Frontend:** Angular (standalone components, signals, `HttpClient`,
  client-side routing), TypeScript, plain CSS
- **Architecture:** Flask application factory pattern with resource-based
  blueprints; Angular feature folders with a typed service layer; the
  Angular dev server proxies `/api` requests to Flask

## Database Design

Seven related tables model the domain:

| Table | Purpose |
|---|---|
| `Role` | Job role (waiter, chef, bartender...), optional hourly rate |
| `Department` | Where a shift takes place (kitchen, bar, floor...) |
| `Employee` | Staff member, linked to a `Role` |
| `Shift` | A schedulable slot: date, time range, department, required headcount |
| `ShiftAssignment` | Junction between `Employee` and `Shift`, carrying its own status (`assigned` / `confirmed` / `completed` / `no_show`) and check-in/out timestamps |
| `Availability` | Recurring weekly availability per employee (day of week + time range) |
| `TimeOffRequest` | Date-range leave request with an approval workflow |

The core design decision is the `ShiftAssignment` table: rather than a plain
many-to-many association, it's a full entity that tracks the lifecycle of an
assignment and enables real business logic (conflict detection, check-in
tracking) beyond simple linking.

## Project Structure

```
shift-management-system/
├── app/                          # Flask backend (API only)
│   ├── __init__.py               # application factory, blueprint registration
│   ├── models.py                 # SQLAlchemy models
│   ├── scheduler.py              # eligibility/matching logic
│   └── routes/
│       ├── employees.py
│       ├── shifts.py
│       ├── assignments.py
│       ├── availability.py
│       ├── time_off.py
│       └── roles.py
├── angular-frontend/             # Angular single-page app
│   ├── proxy.conf.json           # forwards /api to Flask during development
│   └── src/app/
│       ├── core/
│       │   ├── models/           # TypeScript interfaces matching API responses
│       │   └── services/         # one HttpClient service per resource
│       ├── features/
│       │   ├── schedule/         # weekly calendar + assign modal
│       │   ├── staff/            # staff table + create/edit modal
│       │   └── time-off/         # requests table + new-request modal
│       ├── shared/
│       │   └── navbar/
│       └── app.routes.ts
├── screenshots/
├── config.py
├── run.py
├── seed.py
├── requirements.txt
└── .gitignore
```

## API Overview

| Resource | Endpoints |
|---|---|
| Employees | `GET/POST /api/employees`, `GET/PUT/DELETE /api/employees/<id>` |
| Shifts | `GET/POST /api/shifts`, `GET/PUT/DELETE /api/shifts/<id>` |
| Assignments | `GET /api/shifts/<id>/candidates`, `POST /api/shifts/<id>/assign`, `PATCH /api/assignments/<id>`, `PATCH /api/assignments/<id>/check-in` |
| Availability | `GET/POST /api/employees/<id>/availability`, `PUT/DELETE .../availability/<id>` |
| Time off | `GET/POST /api/time-off`, `PATCH /api/time-off/<id>/approve`, `PATCH /api/time-off/<id>/reject` |
| Roles | `GET /api/roles` |

## Getting Started

**Prerequisites:** Python 3, Node.js, and the Angular CLI
(`npm install -g @angular/cli`).

**1. Backend**

```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# (Optional) Populate the database with sample data
python seed.py

# Run the API (http://127.0.0.1:5000)
python run.py
```

**2. Frontend** (in a second terminal)

```bash
cd angular-frontend
npm install
ng serve
```

Open `http://localhost:4200`. The Angular dev server forwards every `/api`
request to the Flask server on port 5000, so both must be running.

## Known Limitations

- Shifts and availability windows that cross midnight (e.g. 22:00–03:00)
  are not supported by the current time-comparison logic.

## Author

Konstantinos Antoniou
[GitHub](https://github.com/AntoniouKonstantinos)
