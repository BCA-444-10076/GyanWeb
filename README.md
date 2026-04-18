# GyanWeb - AI-Powered Assessment System

GyanWeb is an innovative, AI-powered assessment and interview management system designed to streamline the evaluation process. It leverages modern web technologies to handle user management, question handling, and sophisticated interview result processing using artificial intelligence.

## 🚀 Features

- **User Management**: Secure registration, login, and robust role-based access control.
- **AI-Powered Question Handling**: Intelligent generation and assessment of interview questions using Groq API.
- **Interview Result Processing**: Automated evaluation and detailed feedback generation for candidates.
- **RESTful API**: Flexible and scalable backend powered by Django REST Framework.
- **Cross-Origin Support**: Pre-configured CORS policies for seamless frontend-backend integration.

## 🛠️ Technologies Used

- **Backend Framework**: Django (v6.0.2)
- **API Framework**: Django REST Framework (v3.16.1)
- **AI Integration**: Groq API
- **Database**: SQLite (default, configurable for production)
- **Microservices Support**: Flask (v3.0.0) included for modular service definitions
- **HTTP Client**: Requests 

## 📋 Prerequisites

Before you begin, ensure you have the following installed on your machine:
- [Python 3.10+](https://www.python.org/downloads/)
- `pip` (Python package installer)

## ⚙️ Installation & Local Environment Setup

Follow these steps to set up the Django project locally.

### 1. Clone the repository
Get a copy of the source code onto your local machine.

```bash
git clone <your-repository-url>
cd gyanweb
```

### 2. Set up the Virtual Environment (Env Process)
It is highly recommended to use a virtual environment to manage your project's dependencies and avoid conflicts.

**Using `venv` (Windows):**
```bash
python -m venv env
env\Scripts\activate
```

**Using `venv` (macOS/Linux):**
```bash
python3 -m venv env
source env/bin/activate
```
ok

*(Once activated, you should see `(env)` at the beginning of your terminal prompt)*

### 3. Install Dependencies
Install all required Python packages listed in the `requirements.txt` file.
```bash
pip install -r requirements.txt
```

### 4. Set Environment Variables
If your application uses external services (like the Groq API), set up your environment variables. 
Create a `.env` file in the root directory and add your keys:
```env
# Example .env content
GROQ_API_KEY=your_groq_api_key_here
SECRET_KEY=your_django_secret_key_here
DEBUG=True
```

### 5. Apply Database Migrations
Initialize the SQLite database with Django's built-in schema tables.
```bash
python manage.py migrate
```

### 6. Create a Superuser (Optional)
Create an admin account to access the Django admin panel (`/admin/`).
```bash
python manage.py createsuperuser
```
*(Follow the prompts to set a username, email, and password)*

### 7. Run the Development Server
Start the local server to see your application in action.
```bash
python manage.py runserver
```

The application will now be running at `http://127.0.0.1:8000/`.

---

## 📁 Project Structure

```text
gyanweb/
├── ai_interview/     # Logic handling AI question generation and evaluation
├── core/             # Central configs and apps (if any)
├── student/          # App managing student profiles and interactions
├── head/             # App or settings for administrative aspects 
├── templates/        # HTML templates for rendering views
├── static/           # CSS, JS, Images and other static assets
├── manage.py         # Django execution script
└── requirements.txt  # Python dependency list
```

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! 
Feel free to check out the issues page if you want to contribute.

## 📝 License

This project is licensed under the [MIT License](LICENSE).
