# 📌 Mimic -- Agentic IT Assistant

A role-based IT assistant built with **Django REST Framework (backend)**
and **Streamlit (frontend)**.\
It supports role-based logins, chatbot-based app installation/download,
file access, ticket management, and logs export.

------------------------------------------------------------------------

## 🚀 Features

### 🔑 Authentication

-   Role-based login:
    -   **Admin** → Full access (apps, files, logs, tickets).\
    -   **Manager** → Manage Excel + Zoom, view finance files, update
        tickets.\
    -   **User** → Limited apps (Zoom), only general files, own logs and
        tickets.

### 🤖 Chatbot Assistant

-   Detects `install` / `download` commands:
    -   `Install Zoom 5.0` → Installs Zoom version 5.0.\
    -   Dropdowns for **app** and **version**.\
-   Generic chatbot for normal queries.\
-   Logs every action to backend.

### 📁 Files

-   Role-based access to files:
    -   **General files** visible to all.\
    -   **Finance files** visible to Managers & Admin.\
    -   **Sensitive files** only visible to Admin.\
-   Search files.\
-   Export visible files to Excel.

### 📑 Logs

-   Stores structured logs (install, download, chat).\
-   Users see **only their logs**, managers/admin see all.\
-   Export logs to Excel.

### 🎫 Tickets

-   Tickets created automatically for installs/downloads.\
-   Users: view their own tickets.\
-   Managers/Admin: update ticket status (Open/In Progress/Closed).\
-   Export tickets to Excel.

------------------------------------------------------------------------

## 🛠️ Tech Stack

-   **Backend**: Django, Django REST Framework\
-   **Frontend**: Streamlit\
-   **Database**: SQLite (default)\
-   **Other**: Pandas, XlsxWriter

------------------------------------------------------------------------

## ⚡ Installation

### 1. Clone repo

``` bash
git clone https://github.com/your-repo/mimic-agentic.git
cd mimic-agentic
```

### 2. Create virtual environment

``` bash
python -m venv venv
source venv/bin/activate   # (Linux/Mac)
venv\Scripts\activate      # (Windows)
```

### 3. Install dependencies

``` bash
pip install -r requirements.txt
```

### 4. Configure `.env`

Create a `.env` file in the root:

``` env
DEBUG=True
SECRET_KEY=change-me
ALLOWED_HOSTS=*
SERVICE_NOW_EXCEL=servicenow_requests.xlsx
BACKEND_URL=http://127.0.0.1:8000/api
```

### 5. Run backend

``` bash
cd backend
python manage.py migrate
python manage.py runserver
```

➡️ Backend runs at: `http://127.0.0.1:8000/api/`

### 6. Run frontend

``` bash
cd ..
streamlit run app.py
```

➡️ Frontend runs at: `http://localhost:8501`

------------------------------------------------------------------------

## 🧪 Default Logins

  Username   Password   Role
  ---------- ---------- ---------
  admin      admin      Admin
  bob        pass       Manager
  alice      pass       User

------------------------------------------------------------------------

## 📊 API Endpoints

-   `GET /api/tasks/` → Task list\
-   `GET /api/logs/` → All logs\
-   `GET /api/logs/<id>/` → Log by ID\
-   `POST /api/agent/` → Chatbot / command endpoint

------------------------------------------------------------------------

## 📂 Project Structure

    .
    ├── backend/
    │   ├── main/            # Django app
    │   ├── mimic_backend/   # Django project
    │   └── manage.py
    ├── app.py               # Streamlit frontend
    ├── tickets.xlsx         # Ticket store (auto-created)
    ├── requirements.txt
    └── README.md

------------------------------------------------------------------------

## 📦 Exports

-   **Files** → Excel download\
-   **Logs** → Excel download\
-   **Tickets** → Excel download

------------------------------------------------------------------------

## 🛡️ Notes

-   Don't keep `DEBUG=True` in production.\
-   Replace `SECRET_KEY` with a secure random string.\
-   Configure `ALLOWED_HOSTS` properly for deployment.
