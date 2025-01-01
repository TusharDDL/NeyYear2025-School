# Frontend Testing Documentation

## Quick Start Guide

### Running Tests
```bash
# Install test dependencies (if not already installed)
npm install --save-dev jest @testing-library/react @testing-library/jest-dom jest-environment-jsdom @testing-library/user-event

# Run all tests
npm test

# Run tests with verbose output
npm test -- --verbose

# Run specific test file
npm test __tests__/auth.test.tsx
```

## Test Files Overview

1. Authentication Tests (`__tests__/auth.test.tsx`)
   - Login form validation
   - Registration form submission
   - Authentication error handling

2. Library Management Tests (`__tests__/library.test.tsx`)
   - Book catalog search
   - Book circulation management
   - Library record updates

3. Student Management Tests (`__tests__/students.test.tsx`)
   - Student list display
   - Student form submission
   - Student data management

## Testing API Endpoints

### Authentication APIs

1. Test Login API:
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123"
  }'
```

2. Test Registration API:
```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "password": "newpass123",
    "first_name": "John",
    "last_name": "Doe",
    "role": "TEACHER"
  }'
```

### Student Management APIs

1. Test Get Students List:
```bash
# First get auth token from login API
TOKEN="your_auth_token"

curl -X GET http://localhost:8000/api/students/ \
  -H "Authorization: Bearer $TOKEN"
```

2. Test Create Student:
```bash
curl -X POST http://localhost:8000/api/students/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Jane",
    "last_name": "Doe",
    "admission_number": "2024001",
    "class_name": "10A"
  }'
```

### Library Management APIs

1. Test Book Search:
```bash
curl -X GET "http://localhost:8000/api/library/books/search/?query=physics" \
  -H "Authorization: Bearer $TOKEN"
```

2. Test Book Issue:
```bash
curl -X POST http://localhost:8000/api/library/circulation/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "book_id": 1,
    "student_id": 1,
    "due_date": "2024-02-15"
  }'
```

## Common Test Issues & Solutions

1. Test Failures
   - Ensure all test dependencies are installed
   - Check mock implementations match API responses
   - Verify test environment setup in jest.config.js

2. API Testing Issues
   - Verify backend server is running
   - Check authentication token expiration
   - Ensure correct API endpoint URLs

3. Component Test Issues
   - Use act() for state updates:
     ```typescript
     await act(async () => {
       fireEvent.change(element, { target: { value: 'new value' } });
     });
     ```
   - Wait for async operations:
     ```typescript
     await waitFor(() => {
       expect(screen.getByText('Success')).toBeInTheDocument();
     });
     ```

## Test Configuration Files

1. Jest Configuration (jest.config.js):
```javascript
module.exports = {
  testEnvironment: 'jest-environment-jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy'
  }
};
```

2. Jest Setup (jest.setup.js):
```javascript
import '@testing-library/jest-dom';

global.fetch = jest.fn();
```

## Running Individual Test Suites

1. Authentication Tests:
```bash
npm test __tests__/auth.test.tsx
```

2. Library Tests:
```bash
npm test __tests__/library.test.tsx
```

3. Student Tests:
```bash
npm test __tests__/students.test.tsx
```

## Test Development Guidelines

1. Mock API Calls:
```typescript
const mockFetch = jest.fn();
global.fetch = mockFetch;

mockFetch.mockImplementation((url) => {
  if (url.includes('/api/auth/login')) {
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve({ token: 'test-token' })
    });
  }
});
```

2. Component Testing:
```typescript
test('handles form submission', async () => {
  render(<YourComponent />);
  
  fireEvent.change(screen.getByLabelText(/email/i), {
    target: { value: 'test@example.com' }
  });
  
  await act(async () => {
    fireEvent.click(screen.getByRole('button', { name: /submit/i }));
  });
  
  await waitFor(() => {
    expect(mockFetch).toHaveBeenCalled();
  });
});
```

## Troubleshooting Guide

1. Test Setup Issues:
   - Verify all dependencies in package.json
   - Check Jest configuration files
   - Ensure correct test environment

2. Test Execution Issues:
   - Clear Jest cache: `npm test -- --clearCache`
   - Run tests in isolation
   - Check for timing issues with async operations

3. API Testing Issues:
   - Verify API endpoint URLs
   - Check authentication token format
   - Ensure proper request headers
