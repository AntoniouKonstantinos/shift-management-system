# Shift Management System

A staff shift scheduling application built for restaurant and hospitality
businesses. Managers can create shifts, track employee availability, assign
staff based on real-time eligibility checks, and manage time-off requests,
while employees sign in to view the schedule, set their availability, and
request time off, all through a single-page web dashboard.

Built as a portfolio project with an emphasis on correct relational database
design and CRUD logic on top of real business rules, drawing on direct
industry experience in hospitality.

## Version History

The frontend was originally built with Jinja2 templates and vanilla
JavaScript served by Flask, then rewritten as an Angular single-page app on
top of the same backend. The original version is preserved under the
[`v1-vanilla-js`](https://github.com/AntoniouKonstantinos/shift-management-system/tree/v1-vanilla-js)
tag. Flask is now a pure JSON API and serves no HTML pages.

Since the Angular rewrite the project gained authentication with manager and
employee roles, an availability screen, support for shifts that cross
midnight, an automated test suite, and account security features (password
change and login rate limiting).

## Features

- **Authentication and roles** — JWT-based login with two access levels:
  managers run the schedule, employees see it and manage their own data.
- **Employee management** — managers create, edit, deactivate, and remove
  staff records, each linked to a job role (waiter, chef, bartender, etc.),
  and give staff login accounts.
- **Shift scheduling** — define shifts by department, date, and time range,
  with a required headcount per shift. Shifts can run past midnight.
- **Availability** — employees declare their recurring weekly availability
  (including windows that run past midnight); managers can view and edit
  anyone's.
- **Smart assignment** — a candidates endpoint filters staff down to those
  who are actually eligible for a given shift, checking:
  - declared weekly availability, including overnight windows
  - conflicting assignments, including shifts that overlap across midnight
  - approved time-off periods (checked against the shift's start date)
- **Time-off requests** — employees submit requests for themselves; managers
  approve or reject them through a dedicated workflow (not a generic field
  update).
- **Weekly calendar dashboard** — everyone can browse shifts week by week,
  and managers assign staff directly from the grid.
- **My Account** — every user can see their profile and change their own
  password.

### Overnight shifts

A shift or availability slot whose end time is earlier than its start time
ends on the following day (for example `22:00` to `02:00`), and the interface
marks it with a **+1**. Equal start and end times are rejected because they
are ambiguous. Internally every time range is converted to absolute
date-times before it is compared, so a Friday-night slot correctly covers an
early-Saturday shift and a Friday-night shift correctly conflicts with an
early-Saturday one.

## Authentication and Roles

There is no public sign-up. The seed script creates the first manager, and
managers create accounts for staff from the Staff page.

| Action | Manager | Employee |
|---|---|---|
| View the schedule | Yes | Yes |
| Create, edit, delete shifts | Yes | No |
| Assign or remove staff, view eligible candidates, change assignment status | Yes | No |
| Check in to a shift (API only) | Any shift | Own shifts only |
| Manage staff records and accounts | Yes | No |
| View and edit availability | Anyone's | Own only |
| Change own password | Yes | Yes |
| Reset someone else's password | Yes | No |
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
- Failed logins are rate limited (5 per minute per IP address). Successful
  logins are not counted, so colleagues sharing a network do not lock each
  other out.
- Changing a password requires the current password, and failed attempts are
  limited (5 per 15 minutes).
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

- **Backend:** Flask, Flask-SQLAlchemy, Flask-JWT-Extended, Flask-Limiter
  (REST API only)
- **Database:** SQLite (swappable via `DATABASE_URL`)
- **Frontend:** Angular (standalone components, signals, `HttpClient` with an
  authentication interceptor, route guards, client-side routing), TypeScript,
  plain CSS
- **Testing:** pytest, with an in-memory SQLite database per test
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
| `Shift` | A schedulable slot: date, time range (may end after midnight), department, required headcount |
| `ShiftAssignment` | Junction between `Employee` and `Shift`, carrying its own status (`assigned` / `confirmed` / `completed` / `no_show`) and check-in/out timestamps |
| `Availability` | Recurring weekly availability per employee (day of week + time range, which may end after midnight) |
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
│   ├── __init__.py               # application factory, JWT and rate-limiter setup, blueprint registration
│   ├── models.py                 # SQLAlchemy models
│   ├── scheduler.py              # eligibility/matching logic
│   ├── timeutils.py              # time-interval logic, including ranges that cross midnight
│   ├── security.py               # login_required / manager_required decorators
│   └── routes/
│       ├── auth.py               # login, current user, change password
│       ├── employees.py
│       ├── shifts.py
│       ├── assignments.py
│       ├── availability.py
│       ├── time_off.py
│       └── roles.py
├── tests/                        # pytest suite
│   ├── conftest.py               # fresh in-memory app per test
│   ├── test_timeutils.py
│   ├── test_scheduler.py
│   ├── test_overnight_routes.py
│   └── test_auth.py
├── angular-frontend/             # Angular single-page app
│   ├── proxy.conf.json           # forwards /api to Flask during development
│   └── src/app/
│       ├── core/
│       │   ├── models/           # TypeScript interfaces matching API responses
│       │   ├── services/         # one HttpClient service per resource, plus AuthService
│       │   ├── interceptors/     # adds the JWT to requests, handles 401
│       │   ├── guards/           # route guards (signed in, manager, guest)
│       │   └── constants.ts
│       ├── features/
│       │   ├── login/
│       │   ├── schedule/         # weekly calendar + assign modal
│       │   ├── staff/            # staff table + create/edit modal
│       │   ├── availability/     # weekly availability editor
│       │   ├── time-off/         # requests table + new-request modal
│       │   └── account/          # profile + change password
│       ├── shared/
│       │   └── navbar/
│       └── app.routes.ts
├── screenshots/
├── config.py
├── run.py
├── seed.py
├── pytest.ini
├── requirements.txt
├── requirements-dev.txt          # requirements.txt plus pytest
└── .gitignore
```

## API Overview

All endpoints except login require a JWT. See the permissions table above for
who may call what.

| Resource | Endpoints |
|---|---|
| Auth | `POST /api/auth/login`, `GET /api/auth/me`, `POST /api/auth/change-password` |
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
# Create a virtual environment
python -m venv .venv
```

Activate it:

- macOS / Linux: `source .venv/bin/activate`
- Windows (Git Bash): `source .venv/Scripts/activate`
- Windows (Command Prompt or PowerShell): `.venv\Scripts\activate`

Then:

```bash
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
`DATABASE_URL`. The built-in defaults are for development only. The login
rate limiter keeps its counters in memory by default; point
`RATELIMIT_STORAGE_URI` at a shared store such as Redis if the API runs in
more than one process.

**2. Frontend** (in a second terminal)

```bash
cd angular-frontend
npm install
ng serve
```

Open `http://localhost:4200` and sign in with one of the demo accounts above.
The Angular dev server forwards every `/api` request to the Flask server on
port 5000, so both must be running.

## Running the Tests

With the virtual environment active:

```bash
pip install -r requirements-dev.txt
python -m pytest
```

The suite covers the time-interval logic (including the midnight and
Sunday-to-Monday edge cases), the scheduler against a real database, the API
routes with authentication and permissions, password changes, and the rate
limiter. Every test runs against its own in-memory database, so the
development database is never touched.

## Known Limitations

- Access tokens last 8 hours, there is no refresh token, and the token is
  kept in the browser's `localStorage`. Tokens issued before a password
  change stay valid until they expire.
- Login rate limiting is per IP address and kept in memory by default, so
  counters reset when the server restarts and are not shared between server
  processes.
- Production deployment is not configured: the `/api` proxy only works under
  `ng serve`, and Flask runs on its development server.
- The manager override for assignments (`force`) and shift check-in exist in
  the API but have no screen yet.
- A shift is blocked by approved time off only when its start date falls
  inside the time-off period.
- The Angular frontend has no automated tests yet.

## Author

Konstantinos Antoniou
[GitHub](https://github.com/AntoniouKonstantinos)
