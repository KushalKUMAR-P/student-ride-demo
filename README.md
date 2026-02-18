# RideLess 🚗  
A Peer-to-Peer Ride Marketplace for Students

## 📌 Overview

RideLess is a full-stack marketplace application that allows students to post ride requests with a defined budget and match with drivers traveling the same route.

Unlike traditional ride-hailing platforms, RideLess enables price-driven matching where riders set their own budget and drivers choose whether to accept.

This project demonstrates full lifecycle state management, role-based access control, server-side filtering, pagination, and production deployment.

Live Demo: https://your-live-url-here

---

## 🏗 Architecture Overview

**Backend**
- Flask (Python)
- SQLite
- Server-side rendering (Jinja2)

**Core Concepts Implemented**
- User authentication & session management
- Marketplace lifecycle states:
  - Pending → Accepted → Completed
- Role-based permissions (rider vs driver)
- Stateful search and filtering
- Budget sorting
- Pagination with OFFSET/LIMIT
- Platform analytics
- Production deployment via Render

---

## 🔄 Ride Lifecycle

1. User registers and logs in.
2. Rider posts a ride request with origin, destination, and budget.
3. Drivers browse and accept ride requests.
4. Either party can mark ride as completed.
5. Riders can cancel pending rides.

This models a real marketplace state transition system.

---

## 🔍 Features

- Authentication (Register/Login/Logout)
- Role-aware action controls
- Ride posting
- Accept ride functionality
- Cancel ride functionality
- Mark ride as completed
- Driver visibility after acceptance
- Search by origin/destination
- Sort by budget
- Pagination (6 rides per page)
- Persistent filter state across pages
- Analytics dashboard (users, rides, completions)

---

## 📊 Analytics

The homepage displays:

- Total registered users
- Total ride requests
- Completed rides

This simulates basic marketplace health metrics.

---

## 🧠 Engineering Highlights

- Composed dynamic SQL queries with conditional filtering
- Implemented LIMIT/OFFSET pagination
- Preserved query state across requests
- Enforced backend permission checks
- Structured lifecycle state transitions
- Designed clean UI with Bootstrap
- Deployed production-ready version with Gunicorn

---

## 🚀 Future Improvements

- Rating system
- Ride expiration logic
- Payment integration
- Real-time notifications
- REST API version
- Migration to PostgreSQL
- Containerization (Docker)
- Microservice split (auth, ride-service)

---

## 🛠 Tech Stack

- Python 3
- Flask
- SQLite
- Bootstrap 5
- Gunicorn
- Render (Deployment)

---

## 📚 What I Learned

- Marketplace lifecycle modeling
- Stateful server-side filtering
- Role-based permission control
- Query optimization basics
- Deployment workflows
- Product thinking beyond CRUD apps

---

## 📈 Why This Project Matters

RideLess is not just a CRUD demo.

It models:
- Marketplace architecture
- Lifecycle state transitions
- Query-driven filtering systems
- Platform metrics
- Role-based access control

This project demonstrates the ability to build and deploy a structured, scalable web application.
