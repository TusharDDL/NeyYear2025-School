# Local Setup Guide for School Management System

## Prerequisites
- Python 3.8+
- Node.js 16+
- PostgreSQL 12+
- Git

## Clone the Repository
```bash
git clone https://github.com/TusharDDL/School-Management.git
cd School-Management
```

## Backend Setup

### 1. Database Setup
1. Start PostgreSQL service:
```bash
sudo service postgresql start
```

2. Create database and user:
```sql
psql -U postgres
CREATE DATABASE school_management;
CREATE USER admin WITH PASSWORD 'password';
ALTER ROLE admin SET client_encoding TO 'utf8';
ALTER ROLE admin SET default_transaction_isolation TO 'read committed';
ALTER ROLE admin SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE school_management TO admin;
\q
```

### 2. Environment Configuration
1. Create `.env` file in the backend directory:
```bash
cd backend
cp .env.example .env  # If .env.example exists, otherwise create new .env
```

2. Add the following environment variables to `.env`:
```
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration
DB_NAME=school_management
DB_USER=admin
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=5432

# Email Configuration (optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### 3. Python Environment Setup
1. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### 4. Database Migrations
```bash
python manage.py migrate
```

### 5. Create Superuser
```bash
python manage.py createsuperuser
```

### 6. Run Backend Server
```bash
python manage.py runserver
```
The backend server will start at http://localhost:8000

## Frontend Setup

### 1. Install Dependencies
```bash
cd ../frontend
npm install
```

### 2. Environment Configuration
1. Create `.env` file in the frontend directory:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Run Development Server
```bash
npm run dev
```
The frontend development server will start at http://localhost:3000

## Testing

### Backend Tests
```bash
# From the backend directory
python manage.py test
# or
pytest
```

### Frontend Tests
```bash
# From the frontend directory
npm test
```

Run tests with verbose output:
```bash
npm test -- --verbose
```

Run specific test file:
```bash
npm test __tests__/auth.test.tsx
```

## Common Issues and Solutions

### Backend Issues

1. Database Connection Error
- Verify PostgreSQL service is running
- Check database credentials in `.env`
- Ensure database exists and user has proper permissions

2. Migration Issues
```bash
# Reset migrations if needed
python manage.py migrate --fake
python manage.py makemigrations
python manage.py migrate
```

3. Dependencies Issues
```bash
# Update pip
pip install --upgrade pip
# Reinstall requirements
pip install -r requirements.txt --force-reinstall
```

### Frontend Issues

1. Node Modules Issues
```bash
# Clear npm cache
npm cache clean --force
# Remove node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

2. TypeScript Errors
```bash
# Check TypeScript version
npm list typescript
# Install missing type definitions
npm install --save-dev @types/jest @types/testing-library__jest-dom
```

3. Test Environment Issues
```bash
# Clear Jest cache
npm test -- --clearCache
```

## Development Workflow

1. Start both servers:
```bash
# Terminal 1 (Backend)
cd backend
source venv/bin/activate
python manage.py runserver

# Terminal 2 (Frontend)
cd frontend
npm run dev
```

2. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Admin Interface: http://localhost:8000/admin

3. API Documentation:
- Swagger UI: http://localhost:8000/api/docs/
- ReDoc: http://localhost:8000/api/redoc/

## Additional Resources
- Frontend Documentation: [FRONTEND.md](./FRONTEND.md)
- API Documentation: [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)
- Project Overview: [PROJECT_OVERVIEW.md](./PROJECT_OVERVIEW.md)
