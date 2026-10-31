# Nawatech Platform

AI-powered digital business incubator platform built to support entrepreneurs through incubation programs, training, mentoring, evaluation, funding workflows, and an intelligent AI assistant.

**Live product:** https://nawatech.org/

> Public portfolio snapshot. Production databases, user uploads, credentials, private documents, and large training media are intentionally excluded.

## My Role

I worked across the product as a **Full-Stack / Backend & AI Developer**, including:

- UI design and implementation for the platform's public pages and role-based dashboards.
- Backend architecture and business workflows using Flask and SQLAlchemy.
- Authentication, role-based access, verification workflows, and dashboard logic.
- Database models for users, startups, programs, applications, courses, mentoring, funding, certificates, and purchases.
- AI integration with **Google Gemini** for the Nawatech AI assistant and AI-assisted training workflows.
- Payment integration using **Stripe** and transactional email notifications.
- File uploads, reporting, certificates, learning progress, and multi-role operational flows.
- Production deployment and server-side operations.

## Platform Roles

- Entrepreneur / Founder
- Trainer
- Business Advisor
- Investor / Funding Entity
- Administrator
- Public Visitor

## Key Features

### Nawatech AI
An intelligent assistant integrated into the platform to answer entrepreneurship questions and provide context-aware help for visitors and registered users. Registered founders can receive guidance based on their applications, programs, and progress.

### Incubation & Application Workflow
Entrepreneurs can create startup profiles, apply to programs, submit business information, track application status, and progress through the incubation journey.

### Training & Learning Hub
Training workflows include trainer-managed courses and lessons, learning progress, AI-assisted lesson/quiz generation, assessments, and certificates.

### Mentoring & Advisory
Advisors and trainers have dedicated dashboards for reviewing projects, evaluating ideas, sending requests, scheduling mentoring sessions, and managing startup progress.

### Investor Portal
Funding entities can browse eligible projects, review project details, express interest, and communicate through the platform workflow.

### Administration & Analytics
Administrative capabilities cover users, programs, applications, services, purchases, startups, verification, reporting, and operational analytics.

### Payments
Stripe checkout and webhook processing support paid platform services, with email notifications after successful transactions.

## Tech Stack

**Backend:** Python, Flask, Flask-SQLAlchemy, Flask-Login, Flask-Migrate  
**AI:** Google Gemini API  
**Database:** SQLAlchemy / SQLite in development  
**Payments:** Stripe API & Webhooks  
**Frontend:** Jinja2, HTML, CSS, JavaScript  
**Other:** Flask-Mail, Flask-Babel, ReportLab, QRCode, Pillow, bcrypt

## Project Structure

```text
.
├── app.py                  # Application factory, public routes, payments, mail
├── config.py               # Environment-based configuration
├── models/                 # SQLAlchemy data models
├── routes/
│   ├── auth.py             # Authentication and registration
│   ├── dashboard.py        # Founder/admin dashboards and AI chat
│   ├── advisor.py          # Advisor workflow
│   ├── trainer.py          # Trainer workflow and AI content generation
│   └── investor.py         # Investor/funding workflow
├── services/
│   └── ai_engine.py        # Internal scoring/training/certificate services
├── templates/              # Public site and role-based UI templates
├── static/                 # Public assets
├── .env.example            # Safe environment variable template
└── requirements.txt
```

## Security & Public Repository Notes

This repository is a sanitized portfolio version of the project. It intentionally does **not** include:

- Production databases or user records
- Identity documents and user-uploaded files
- API keys, payment secrets, email credentials, or session secrets
- Internal test-account credential files
- Client/project submissions
- Large proprietary training videos and documents
- Original production brand/media binaries (lightweight SVG placeholders are included)

All external credentials are loaded from environment variables.

## Local Setup

```bash
git clone https://github.com/hassanA176/nawatech-platform.git
cd nawatech-platform
python -m venv .venv
```

Activate the virtual environment, then install dependencies:

```bash
pip install -r requirements.txt
```

Copy the environment template and add your own development credentials:

```bash
cp .env.example .env
```

Run the application:

```bash
python app.py
```

## Screenshots

Screenshots and an architecture overview can be added here as the portfolio presentation is expanded.

## Author

**Hassan Ali Hassan**  
AI Engineer & Data Analyst — Backend, API Integration, AI Systems & Automation
