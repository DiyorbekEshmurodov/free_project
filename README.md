# 🏋️‍♂️ Life GYM — AI-Powered Fitness & Health Ecosystem

[![Django](https://img.shields.io/badge/Django-5.0+-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Aiogram](https://img.shields.io/badge/Aiogram-3.x-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)](https://docs.aiogram.dev/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)

**Life GYM** is an all-in-one digital fitness and health ecosystem that combines web platform capabilities with artificial intelligence (AI) and seamless Telegram Bot integration. It helps users manage their daily workouts, personalize nutrition plans, calculate macronutrients (BJU), and monitor progress effortlessly.

---

## ✨ Key Features

* **🤖 Telegram Bot Integration (`Aiogram 3`)**:
  * Step-by-step user registration directly through Telegram.
  * Automatic account linking with the web dashboard via `OneToOneField` mapping.
  * Direct authentication access links sent straight to Telegram chats.

* **💻 Interactive Web Dashboard (`Django`)**:
  * Personalized user profile management with dynamic avatar upload preview.
  * Secure authentication system with protected routes and CSRF checks.

* **🥗 AI Nutritionist & Fitness Planner**:
  * Custom exercise routine recommendations tailored to user goals (weight loss, muscle gain, maintain physique).
  * Automated daily macronutrient (Protein, Fat, Carbs) and hydration balance calculations.

---

## 🛠 Tech Stack

* **Backend Framework:** Django (Python 3.11+)
* **Telegram Bot Framework:** Aiogram 3.x
* **Database:** PostgreSQL / SQLite
* **Frontend:** HTML5, CSS3, JavaScript
* **Containerization:** Docker & Docker Compose
* **Environment Management:** Python Virtual Environment (`.venv`)

---

## 🚀 Getting Started

### Prerequisites

Ensure you have the following installed on your local system:
* Python 3.10+
* Git
* Docker & Docker Compose (for containerized deployment)

---

### 🐳 Running with Docker Compose (Recommended)

The easiest way to run the entire stack (Django Web App, PostgreSQL Database, and Telegram Bot) is using Docker Compose.

1. **Clone the Repository:**
   ```bash
   git clone [https://github.com/your-username/free-project.git](https://github.com/your-username/free-project.git)
   cd free-project