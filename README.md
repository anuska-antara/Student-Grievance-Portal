# Student-Grievance-Portal

A full-stack **Flask + MySQL** web application designed to streamline the grievance redressal process for students, administrators, and super admins.  
This system allows students to submit complaints, track progress, and view activity logs, while admins can manage grievances, update statuses, and view department-level reports.

---

## Features
   
---

## Student Features

- Submit new grievances  
- View grievance status and full details  
- Track activity logs and updates  
- View department information  
- Simple, responsive dashboard  

---

## Admin Features

- Admin dashboard showing department grievances  
- Update grievance status (New → In Progress → Resolved → Closed)  
- View analytics and department-level reports  
- Role-based sidebar and access control  

---

## Super Admin Features

- View all departments and units  
- Track open grievance count per department  
- Monitor average resolution time  
- High-level management dashboard  

---

## Tech Stack

| Layer        | Technology |
|--------------|------------|
| Backend      | Flask (Python) |
| Database     | MySQL (with Stored Procedures, Triggers, Functions) |
| Frontend     | HTML, CSS, Bootstrap, Jinja2 |
| Auth         | Flask Session-Based Authentication |
| UX Features  | Role-Based Sidebar, Responsive Dashboard |

---

##  Project Structure
```
Student-Grievance-Portal/
│
├── app.py                 # main flask application
├── db.py                  # database connection
├── static/                
├── templates/             # all HTML templates
│   ├── base.html
│   ├── login.html
│   ├── student_dashboard.html
│   ├── admin_dashboard.html
│   ├── superadmin_dashboard.html
│   ├── profile.html
│   ├── grievance_detail.html
│   ├── reports.html
│   └── activity_log.html
│
└── README.md
```

---

##  Setup & Installation

### **1️⃣ Clone the repository**
```bash
git clone https://github.com/your-username/Student-Grievance-Portal.git
cd Student-Grievance-Portal
```
### **2️⃣ Create virtual environment
```bash
python -m venv venv
source venv/bin/activate   # macOS / Linux
venv\Scripts\activate      # Windows
```
### **3️⃣ Install dependencies
```bash
pip install -r requirements.txt
```
### **4️⃣ Configure database
Edit db.py with your MySQL credentials:
```bash
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="yourpassword",
        database="cgrs_db"
    )
```
### **5️⃣ Import SQL
Run the provided SQL file to create:
- Tables
- Stored Procedures
- Triggers
- Dummy Data
### **6️⃣ Run the server
```bash
python app.py
```
Now visit:
```cpp
http://127.0.0.1:5000
```
