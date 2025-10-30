# 🍱 Waste Food Management & Donation System

A web-based **Flask application** designed to reduce food wastage by connecting **Donors**, **NGOs**, and **Admins** through a centralized donation platform.  
Donors can list surplus food, NGOs can claim available donations, and Admins oversee user verification and donation tracking.

---

## 🚀 Features

### 👥 User Management
- **Register** as Donor, NGO, or Admin  
- **Login / Logout** system with password hashing  
- **Admin verification** for new users before access  

### 🍽️ Donation Flow
- **Donors** can:
  - Add food donations with quantity, location, and expiry date  
  - View donation history  

- **NGOs** can:
  - View available donations  
  - Claim donations  
  - Mark donations as completed after pickup  

- **Admins** can:
  - Verify or reject new users  
  - View all donations (filter by status)  
  - Manually mark donations as completed  

---

## 🛠️ Technologies Used

| Component | Technology |
|------------|-------------|
| Backend | Python, Flask |
| Database | SQLite |
| Frontend | HTML, CSS, Bootstrap (via templates) |
| Security | Werkzeug Password Hashing |
| Hosting (optional) | Render / Heroku / Localhost |

---
