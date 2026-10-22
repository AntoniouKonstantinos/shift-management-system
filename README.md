# Shift Management System

A staff shift scheduling application built for restaurant and hospitality
businesses. Managers can create shifts, track employee availability, assign
staff based on real-time eligibility checks, and manage time-off requests,
while employees sign in to view the schedule and request time off, all
through a single-page web dashboard.

Built as a portfolio project with an emphasis on correct relational database
design and CRUD logic on top of real business rules, drawing on direct
industry experience in hospitality.

## Version History

The frontend was originally built with Jinja2 templates and vanilla
JavaScript served by Flask, then rewritten as an Angular single-page app on
top of the same backend. The original version is preserved under the
[`v1-vanilla-js`](https://github.com/AntoniouKonstantinos/shift-management-system/tree/v1-vanilla-js)
tag. Flask is now a pure JSON API and serves no HTML pages. Authentication
with manager and employee roles was added after the Angular rewrite.

## Features

- **Authentication and roles** — JWT-based login with two access levels:
  managers run the schedule, employees see it and manage their own requests.
- **Employee management** — managers create, edit, deactivate, and remove
  staff records, each linked to a job role (waiter, chef, bartender, etc.),
  and give staff login accounts.
- **Shift scheduling** — define shifts by department, date, and time range,
  with a required headcount per shift.
- **Smart assignment** — a candidates endpoint filters staff down to those
  who are actually eligible for a given shift, checking:
  - declared weekly availability
  - conflicting assignments on the same day
  - approved time-off periods
- **Time-off requests** — employees submit requests for themselves; managers
  approve or reject them through a dedicated workflow (not a generic field
  update).
- **Weekly calendar dashboard** — everyone can browse shifts week by week,
  and managers assign staff directly from the grid.

## Authentication and Roles

There is no public sign-up. The seed script creates the first manager, and
managers create accounts for staff from the Staff page.

| Action | Manager | Employee |
|---|---|---|
| View the schedule | Yes | Yes |
| Create, edit, delete shifts | Yes | No |
| Assign or remove staff, view eligible candidates, change assignment status | Yes | No |
| Check in to a shift | Any shift | Own shifts only |
| Manage staff records and accounts | Yes | No |
| View and edit availability | Anyone's | Own only |
| Submit a time-off request | For anyone | For themselves only |
| View time-off requests | All | Own only |
| Approve or reject a request | Yes | No |
| Delete a time-off request | Any | Own pending requests only (withdraw) |

**How it is enforced**

- Every endpoint except `POST /api/auth/login` requires a valid JWT in the
  `Authorization: Bearer` header. Missing or expired tokens return `401`,
  insufficient permissions return `403`.
- Authorization is checked on the server. The Angular route guards and hidden
  buttons only improve the experience; they are not the security boundary.
- An employee's identity always comes from the token, never from the request
  body, so an employee cannot submit or read requests on someone else's behalf.
- The account is re-checked in the database on every request, so a
  deactivated employee or a changed access level takes effect immediately
  instead of when the token expires.
- Passwords are stored only as hashes (Werkzeug), and the login endpoint
  returns the same error for an unknown email and a wrong password.
- A manager cannot delete, deactivate, or demote their own account, so the
  system cannot be left without a manager.

**Demo accounts** (created by `seed.py`, for local development only)

| Access level | Email | Password |
|---|---|---|
| Manager | `manager@example.com` | `manager123` |
| Employee | `maria@example.com` | `employee123` |
| Employee | `nikos@example.com` | `employee123` |
| Employee | `elena@example.com` | `employee123` |

## Screenshots

**Weekly calendar with staff assignment**
![Dashboard](screenshots/dashboard.png)

**Staff management**
![Employees](screenshots/employees.png)

**Time-off approval workflow**
![Time off](screenshots/time_off.png)

## Tech Stack

- **Backend:** Flask, Flask-SQLAlchemy, Flask-JWT-Extended (REST API only)
- **Database:** SQLite (swappable via `DATABASE_URL`)
- **Frontend:** Angular (standalone components, signals, `HttpClient` with an
  authentication interceptor, route guards, client-side routing), TypeScript,
  plain CSS
- **Architecture:** Flask application factory pattern with resource-based
  blueprints; Angular feature folders with a typed service layer; the
  Angular dev server proxies `/api` requests to Flask

## Database Design

Eight related tables model the domain:

| Table | Purpose |
|---|---|
| `Role` | Job role (waiter, chef, bartender, manager...), optional hourly rate |
| `Department` | Where a shift takes place (kitchen, bar, floor...) |
| `Employee` | Staff member, linked to a `Role` |
| `UserAccount` | Login credentials and access level (`manager` or `employee`) for an employee, one-to-one with `Employee` |
| `Shift` | A schedulable slot: date, time range, department, required headcount |
| `ShiftAssignment` | Junction between `Employee` and `Shift`, carrying its own status (`assigned` / `confirmed` / `completed` / `no_show`) and check-in/out timestamps |
| `Availability` | Recurring weekly availability per employee (day of week + time range) |
| `TimeOffRequest` | Date-range leave request with an approval workflow |

Two design decisions are worth calling out:

- `ShiftAssignment` is a full entity rather than a plain many-to-many
  association. It tracks the lifecycle of an assignment and enables real
  business logic (conflict detection, check-in tracking) beyond simple linking.
- `Role` (a job title) and `UserAccount.access_level` (a permission level) are
  deliberately separate concepts. An employee whose job title is "Manager"
  is not automatically an administrator, and credentials live in their own
  table so password hashes never travel with employee data.

## Project Structure

```
shift-management-system/
├── app/                          # Flask backend (API only)
│   ├── __init__.py               # application factory, JWT setup, blueprint registration
│   ├── models.py                 # SQLAlchemy models
│   ├── scheduler.py              # eligibility/matching logic
│   ├── security.py               # login_required / manager_required decorators
│   └── routes/
│       ├── auth.py
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
│       │   ├── services/         # one HttpClient service per resource, plus AuthService
│       │   ├── interceptors/     # adds the JWT to requests, handles 401
│       │   └── guards/           # route guards (signed in, manager, guest)
│       ├── features/
│       │   ├── login/
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

All endpoints except login require a JWT. See the permissions table above for
who may call what.

| Resource | Endpoints |
|---|---|
| Auth | `POST /api/auth/login`, `GET /api/auth/me` |
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

# Create the database with sample data and the demo accounts
# (required to sign in, since there is no public sign-up;
#  this wipes any existing data in the database)
python seed.py

# Run the API (http://127.0.0.1:5000)
python run.py
```

For anything other than local development, set your own secrets through
environment variables: `SECRET_KEY`, `JWT_SECRET_KEY`, and optionally
`DATABASE_URL`. The built-in defaults are for development only.

**2. Frontend** (in a second terminal)

```bash
cd angular-frontend
npm install
ng serve
```

Open `http://localhost:4200` and sign in with one of the demo accounts above.
The Angular dev server forwards every `/api` request to the Flask server on
port 5000, so both must be running.

## Known Limitations

- Shifts and availability windows that cross midnight (e.g. 22:00–03:00)
  are not supported by the current time-comparison logic.
- Availability can be managed through the API only; the Angular app has no
  availability screen yet.
- Employees cannot change their own password. A manager resets it from the
  Staff page.
- Sessions use a single access token that expires after 8 hours, with no
  refresh token, and the token is kept in the browser's `localStorage`.
- The login endpoint has no rate limiting.

## Author

Konstantinos Antoniou
[GitHub](https://github.com/AntoniouKonstantinos)
