# School Management System - Comprehensive Guide

## Project Overview

### Purpose and Core Functionality
The School Management System is a multi-tenant application designed to manage educational institutions. It provides comprehensive features for:
- Academic management (classes, subjects, attendance)
- Student and staff management
- Library operations
- Financial tracking
- Communication systems

### Tech Stack
#### Frontend
- Next.js 14 with TypeScript
- React Query for data fetching
- Zustand for state management
- TailwindCSS with shadcn/ui components
- Jest and React Testing Library for testing

#### Backend
- Django 4.2 with Django REST Framework
- PostgreSQL with multi-tenant architecture
- JWT Authentication
- Celery for background tasks
- pytest for testing

## File Structure

### Frontend Structure
```
frontend/
├── src/
│   ├── app/                    # Next.js app router pages
│   │   ├── (auth)/            # Authentication routes
│   │   ├── (dashboard)/       # Dashboard routes
│   │   └── page.tsx           # Landing page
│   ├── components/            # Reusable components
│   ├── lib/                   # Utilities and hooks
│   └── types/                 # TypeScript definitions
├── __tests__/                 # Test files
└── jest.config.js             # Test configuration
```

### Backend Structure
```
backend/
├── apps/
│   ├── accounts/              # User management
│   ├── academic/              # Academic operations
│   ├── library/              # Library management
│   ├── finance/              # Financial operations
│   ├── communication/        # Messaging system
│   └── core/                 # Core functionality
├── config/                   # Project settings
└── alembic/                 # Database migrations
```

## Modules and Features

### Frontend Routes/Components
1. Authentication Module
   - Login (/auth/login)
   - Registration (/auth/register)
   - Password Reset (/auth/forgot-password)

2. Dashboard Module
   - Academic Management
   - Student Directory
   - Library Management
   - Financial Reports
   - Communication Center

### Backend Apps
1. Accounts App
   - User authentication and authorization
   - Role-based access control
   - Profile management

2. Academic App
   - Class and section management
   - Attendance tracking
   - Assessment management

3. Library App
   - Book catalog management
   - Circulation tracking
   - Fine calculation

4. Finance App
   - Fee structure management
   - Payment tracking
   - Financial reporting

5. Communication App
   - Announcements
   - Messaging system
   - Email/SMS notifications

## API Documentation

### Authentication Endpoints
```
POST /api/auth/login/
Request:
{
  "username": "string",
  "password": "string"
}
Response:
{
  "access": "string",
  "refresh": "string",
  "user": {
    "id": number,
    "username": "string",
    "role": "string"
  }
}
```

### Student Management Endpoints
```
GET /api/students/
Headers: Authorization: Bearer <token>
Query Parameters:
- class_name: string
- section: string
- search: string

POST /api/students/
Headers: Authorization: Bearer <token>
Request:
{
  "first_name": "string",
  "last_name": "string",
  "admission_number": "string",
  "class_name": "string",
  "section": "string"
}
```

### Library Management Endpoints
```
GET /api/books/
POST /api/books/issue/
GET /api/books/circulation/
POST /api/books/return/
```

## Database Schema

### Core Models
```python
class School(TenantMixin):
    name = models.CharField(max_length=100)
    board_affiliation = models.CharField(choices=[...])
    student_strength = models.PositiveIntegerField()

class User(AbstractUser):
    role = models.CharField(choices=['SUPER_ADMIN', 'SCHOOL_ADMIN', 'TEACHER', 'STUDENT', 'PARENT'])
    school = models.ForeignKey(School)
```

### Academic Models
```python
class AcademicYear(models.Model):
    name = models.CharField()
    start_date = models.DateField()
    end_date = models.DateField()

class Class(models.Model):
    name = models.CharField()
    academic_year = models.ForeignKey(AcademicYear)
```

## Common Issues and Solutions

### Frontend Issues
1. Routing Conflicts
   - Issue: Next.js app router conflicts
   - Solution: Check route group organization in app directory

2. Test Setup Errors
   - Issue: Jest configuration for Next.js
   - Solution: Verify jest.config.js and necessary mock files

### Backend Issues
1. Migration Issues
   ```bash
   python manage.py makemigrations
   python manage.py migrate_schemas
   ```

2. Tenant Context Errors
   ```python
   from django_tenants.utils import schema_context
   with schema_context(tenant.schema_name):
       # Perform operations
   ```

## Testing and Debugging

### Frontend Testing
```bash
# Run all tests
npm test

# Run specific test file
npm test -- __tests__/auth.test.tsx

# Run tests in watch mode
npm test -- --watch
```

### Backend Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest apps/accounts/tests/test_auth.py

# Run with coverage
pytest --cov=apps
```

## Environment Configuration

### Frontend Environment
```
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

### Backend Environment
```
DATABASE_URL=postgresql://user:password@localhost:5432/school_db
SECRET_KEY=your-secret-key
DEBUG=True
```

## Development Commands

### Frontend Development
```bash
# Start development server
npm run dev

# Build production
npm run build

# Type checking
npm run type-check
```

### Backend Development
```bash
# Start development server
python manage.py runserver

# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate_schemas

# Create superuser
python manage.py createsuperuser
```
