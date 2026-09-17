# Inventory Management System

## Overview

Role-based inventory, billing, purchasing and reporting desktop application for small retail businesses.

## Project Timeline

Development period: Approximately 2025-2026 (source files dated 2025-08 through 2026-08; timeline approximate, no Git history).

## Key Features

- Admin and employee dashboards with role-based access
- Product, category and supplier management
- Billing with PDF invoice generation
- Purchase orders, sales tracking and settings

## Technologies

Python, CustomTkinter, MySQL (PyMySQL), ReportLab, Matplotlib

## Development

Development: AI-assisted. Requirements, database schema, UI direction, customization, debugging, testing and integration were done by the author; AI tooling assisted with scaffolding and boilerplate.

## Screenshots

![Dashboard](screenshots/01-dashboard.png)

## Requirements

Python 3.10 or newer (as stated in the in-app Settings screen).

## Installation

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Environment Variables

Copy `.env.example` to `.env` and fill in your local MySQL values.

## Database Setup

Create the MySQL database and run `db.py` once to initialize tables.

## Running the Application

```
python main.py
```

## Demo Credentials

Use fictional demo accounts only (for example `admin` / `demo1234`). No real credentials are shipped.

## Limitations

- Requires a local MySQL server.
- Desktop-only UI.

## Future Improvements

- Web dashboard and REST API.
- Barcode scanning and stock alerts.
