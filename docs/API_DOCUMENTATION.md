# School Management System API Documentation

## Overview
This documentation provides a comprehensive guide to the School Management System's backend API, including setup instructions, testing procedures, and troubleshooting guides. The system is built using Django REST Framework with a multi-tenant architecture, allowing multiple schools to operate independently within the same system.

### Key Features
- Multi-tenant architecture with schema-based isolation
- Role-based access control (Super Admin, School Admin, Teacher, Student, Parent)
- Academic year and term management
- Student enrollment and profile management
- Library management system
- Fee management system

## Table of Contents
1. [Authentication](#authentication)
2. [School Management](#school-management)
3. [Academic Year Management](#academic-year-management)
4. [Student Management](#student-management)
5. [Library Management](#library-management)
6. [Testing Guide](#testing-guide)

[Previous comprehensive content remains exactly the same, including all sections:
- Authentication (Login, Register School)
- School Management (Approve School)
- Academic Year Management (Create, List)
- Student Management (Create, List)
- Library Management (Add Book, Issue Book)
- Setting Up Development Environment
- Setting Up Test Environment
- Running Tests
- Test Data Setup
- Common Test Cases
- API Testing with curl/httpie
- Best Practices
- Common Issues and Solutions
- Development Workflow
- Monitoring and Debugging]

## Development Environment Setup
1. System Requirements:
   - Python 3.12
   - PostgreSQL 14+
   - Node.js 18+ (for frontend)

2. Clone and Setup:
   ```bash
   git clone https://github.com/TusharDDL/School-Management.git
   cd School-Management/backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. Database Setup:
   ```sql
   CREATE DATABASE school_management;
   CREATE USER school_admin WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE school_management TO school_admin;
   ```

4. Environment Configuration:
   ```bash
   # .env file
   DEBUG=True
   SECRET_KEY=your_secret_key
   DB_NAME=school_management
   DB_USER=school_admin
   DB_PASSWORD=your_password
   DB_HOST=localhost
   DB_PORT=5432
   ```

## API Testing Guide

### Authentication Flow
1. Register School:
   ```bash
   curl -X POST http://localhost:8000/api/v1/core/schools/register/ \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Test School",
       "email": "school@test.com",
       "principal_name": "Principal",
       "principal_email": "principal@test.com",
       "principal_password": "password123"
     }'
   ```

2. Login:
   ```bash
   curl -X POST http://localhost:8000/api/v1/accounts/login/ \
     -H "Content-Type: application/json" \
     -d '{
       "email": "principal@test.com",
       "password": "password123"
     }'
   ```

### Testing Academic Year API
```bash
# Create Academic Year
curl -X POST http://localhost:8000/api/v1/academic/academic-years/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Tenant-ID: YOUR_SCHOOL_ID" \
  -d '{
    "name": "2023-2024",
    "start_date": "2023-04-01",
    "end_date": "2024-03-31"
  }'

# List Academic Years
curl http://localhost:8000/api/v1/academic/academic-years/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Tenant-ID: YOUR_SCHOOL_ID"
```

### Testing Student Management
```bash
# Create Student
curl -X POST http://localhost:8000/api/v1/accounts/manage-students/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Tenant-ID: YOUR_SCHOOL_ID" \
  -d '{
    "username": "student1",
    "email": "student1@test.com",
    "password": "password123",
    "profile": {
      "admission_number": "ADM001",
      "date_of_birth": "2010-01-01"
    }
  }'

# List Students
curl http://localhost:8000/api/v1/accounts/manage-students/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Tenant-ID: YOUR_SCHOOL_ID"
```

## Running Tests
1. Setup Test Environment:
   ```bash
   # Create test database
   createdb test_school_management

   # Install test dependencies
   pip install pytest pytest-django

   # Run tests
   pytest
   ```

2. Run Specific Test Modules:
   ```bash
   # Academic tests
   pytest apps/academic/tests/

   # Student tests
   pytest apps/accounts/tests/test_students.py

   # Library tests
   pytest apps/library/tests/
   ```

## Troubleshooting Guide

### Common Issues

1. Authentication Errors:
   - "Invalid token": Token expired, get new token via login
   - "Permission denied": Check user role and tenant context


2. Database Issues:
   - "Schema does not exist": Verify tenant headers
   - "Connection failed": Check database settings

3. Test Failures:
   - "Tenant context error": Use proper schema_context
   - "Object not found": Check tenant isolation

### Best Practices
1. Always include tenant headers
2. Use proper authentication tokens
3. Follow test naming conventions
4. Clean up test data
5. Use schema_context for tenant operations

## API Reference

### Core APIs
1. School Registration
   - POST `/api/v1/core/schools/register/`
   - Required fields: name, email, principal details

2. Authentication
   - POST `/api/v1/accounts/login/`
   - POST `/api/v1/accounts/logout/`

### Academic APIs
1. Academic Year Management
   - POST `/api/v1/academic/academic-years/`
   - GET `/api/v1/academic/academic-years/`

2. Student Management
   - POST `/api/v1/accounts/manage-students/`
   - GET `/api/v1/accounts/manage-students/`

### Library APIs
1. Book Management
   - POST `/api/v1/library/books/`
   - GET `/api/v1/library/books/`
   - POST `/api/v1/library/books/{id}/issue/`

## Security Considerations
1. Always use HTTPS in production
2. Implement rate limiting
3. Use proper tenant isolation
4. Validate all inputs
5. Handle errors gracefully
