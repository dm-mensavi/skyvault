
---

# 🌌 **SkyVault**

SkyVault is a robust file management and storage application that offers cloud-like functionalities right on your server. Designed for efficiency and ease of use, SkyVault lets you manage, organize, and securely store files and folders. Key features include uploading, restoring, starring, and navigating files with an intuitive dashboard overview.

---

## 🚀 **Features**

- **File Management**: Upload, delete, and organize files and folders with ease.
- **Context Menu**: Access quick actions (e.g., delete, rename, star) via a right-click menu.
- **Dashboard Insights**: View storage usage, quota details, and recent activity in one glance.
- **Trash Bin & Restore**: Recover accidentally deleted files from the Trash folder.
- **Starred Items**: Mark and prioritize important files and folders for quick access.
- **Enhanced Sharing**: Share files and folders seamlessly with others.

---

## 🛠️ **Getting Started**

SkyVault supports two ways to run the application: using Docker or directly in a local development environment.

---

### Option 1: **Run with Docker**

1. **Install Docker**:
   Ensure Docker is installed on your machine. [Download Docker here](https://www.docker.com/get-started).

2. **Set Up Docker Environment**:
   - Build and run the Docker containers:
     ```bash
     docker-compose up --build
     ```

3. **Access the Application**:
   - Visit [http://localhost:8000](http://localhost:8000) or [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

---

### Option 2: **Run Locally (Development Mode)**

1. **Install Prerequisites**:
   - Python 3.10 or higher
   - Pip (Python package manager)

2. **Set Up a Virtual Environment**:
   ```bash
   python -m venv .venv
   ```

   - **Activate the environment**:
     - **Windows**:
       ```bash
       .venv\Scripts\activate
       ```
     - **Mac/Linux**:
       ```bash
       source .venv/bin/activate
       ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up the Database**:
   - For local development, the default SQLite database is preconfigured.
   - Update `.env` if you are connecting to an external database.

5. **Run Migrations**:
   ```bash
   python manage.py migrate
   ```

6. **Create an Admin Account (Optional)**:
   ```bash
   python manage.py createsuperuser
   ```

7. **Start the Application**:
   ```bash
   python manage.py runserver
   ```

8. **Access the App**:
   Open your browser and navigate to [http://127.0.0.1:8000](http://127.0.0.1:8000).

---

## 🛠️ **Project Architecture**

SkyVault is modular and organized for scalability:
- **`accounts`**: Handles user authentication, signup, and login.
- **`dashboard`**: Provides insights into storage usage and file statistics.
- **`settings`**: Manages user profiles, data updates, and profile picture uploads.
- **`vault`**: Core functionality for file and folder operations, including upload, sharing, and deletion.
- **`notifications`**: Displays user alerts for various events (e.g., successful uploads).

---

## 📜 **Environment Variables**

SkyVault uses environment variables for configuration. Create a `.env` file in the root directory with the following format:

```env
SECRET_KEY=your_secret_key
DEBUG=True
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_HOST=your_database_host
DB_PORT=your_database_port
ALLOWED_HOSTS=localhost,127.0.0.1
```

---

## 📊 **Key Screens**

### **Dashboard Overview**
> See your storage usage and recent activities in a clean interface.
![Dashboard](static/images/Dashboard.png)

---

### **File Management**
> Manage files and folders with an intuitive interface.
![File Management](static/images/Home.png)

---

### **Context Menu**
> Right-click for quick actions like delete, rename, and share.
![Context Menu](static/images/Context-menu.png)

---

### **Trash Bin**
> Restore or permanently delete files with ease.
![Trash](static/images/Trash.png)

---

### **Info Panel**
> View detailed statistics about your account and storage usage.
![Info](static/images/Info.png)

---

## 🛠️ **Docker Configuration**

SkyVault includes both a `docker-compose.yml` and `Dockerrun.aws.json` for flexible deployment:

- **`docker-compose.yml`**: Used for local development and testing.
- **`Dockerrun.aws.json`**: Designed for deployment to AWS Elastic Beanstalk.

### Running in Docker
```bash
docker-compose up --build
```

### Deploying to AWS
Use the `Dockerrun.aws.json` file to deploy to AWS Elastic Beanstalk. The file is already configured to use your Docker Hub image.

---

## 📜 **License**

SkyVault is licensed under the MIT License.

---
