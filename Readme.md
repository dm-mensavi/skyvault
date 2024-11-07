
---

# 🌌 **SkyVault**

Welcome to **SkyVault**! A Django-based application designed to bring you seamless file management and storage capabilities. SkyVault combines an intuitive interface with powerful backend functionality, making it easy to organize and access your files. 

<br>

## ✨ **Features**

- **📂 File Management:** Upload, organize, and access your files with ease.
- **⭐ Starred Files & Folders:** Mark important files and folders for quick access.
- **🗑️ Trash Bin:** Deleted files and folders are stored safely in the trash until permanently removed.
- **👥 Shared Files:** Easily share files with other users.

<br>

## 🚀 **Getting Started**

You can run SkyVault in two ways:

1. **Locally** using Django’s development server (great for development and testing).
2. **With Docker** for a containerized and reproducible environment (ideal for production-like setups).

<br>

## 🛠️ **Requirements**

Ensure you have the following installed:

- **Python 3.8+** 🐍
- **PostgreSQL** 🐘
- **Docker** (for the Docker setup) 🐳
- **Docker Compose** (for managing multi-container applications)

<br>

---

## ⚙️ **Installation**

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/skyvault.git
cd skyvault
```

### Step 2: Environment Configuration

1. Create a `.env` file in the root directory.
2. Add the following environment variables to it:

```plaintext
SECRET_KEY=your-secret-key
DEBUG=True
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db-skyvault
DB_PORT=5432
ALLOWED_HOSTS=127.0.0.1, localhost
```

<br>

---

## 🐍 **Running Locally**

### 1️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 2️⃣ Make Migrations and Migrate Database

```bash
python manage.py makemigrations
python manage.py migrate
```

### 3️⃣ Run the Development Server

```bash
python manage.py runserver
```

Your application should now be live at **`http://127.0.0.1:8000`**!

---

<br>

## 🐳 **Running with Docker**

This option allows you to run SkyVault as a Docker container.

### 1️⃣ Build and Start the Containers

Run the following command to build and start the Docker containers:

```bash
docker-compose up --build
```

### 2️⃣ Initial Setup (First-Time Run)

Once the containers are running, open a new terminal and run the following command to create migrations and a superuser:

```bash
docker-compose exec web-skyvault python manage.py migrate
docker-compose exec web-skyvault python manage.py createsuperuser
```

Your application will be live at **`http://localhost:8000`**.

---

<br>

## 📂 **File Structure**

- **`/vault`** - Core app handling file management and storage functionalities.
- **`/accounts`** - Handles user registration, authentication, and profiles.
- **`/settings`** - Manages application configurations for users.
- **`/dashboard`** - Displays storage summary and analytics.
  
<br>

---

## 🔗 **Accessing the Admin Panel**

To manage users and files directly, access the Django admin panel:

1. Go to **`http://127.0.0.1:8000/admin/`** for local or **`http://localhost:8000/admin/`** for Docker.
2. Use the superuser credentials created during setup.

<br>

---

## 🙌 **Contributing**

1. **Fork** the repository.
2. **Clone** your fork and create a branch.
3. Submit a **pull request** detailing your changes.

<br>

## 📜 **License**

This project is licensed under the MIT License. 

Happy coding! ✨

--- 

