// Import types first
import type { MockResponse } from '../src/types/test-utils'

// Define mock functions with proper types
const mockPush = jest.fn();
const mockReplace = jest.fn();
const mockFetch: jest.MockedFunction<typeof fetch> = jest.fn();

// Mock modules
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    replace: mockReplace,
  }),
}));

// Set up portal root for Select component
beforeAll(() => {
  const portalRoot = document.createElement('div')
  portalRoot.setAttribute('id', 'radix-portal')
  document.body.appendChild(portalRoot)
})

afterAll(() => {
  const portalRoot = document.getElementById('radix-portal')
  if (portalRoot) {
    document.body.removeChild(portalRoot)
  }
})

// Import components and testing utilities after mocks
import { render, screen, fireEvent, waitFor, within, act } from '@testing-library/react'
import '@testing-library/jest-dom'
import userEvent from '@testing-library/user-event'
import { StudentList } from '@/components/students/StudentList'
import { StudentForm } from '@/components/students/StudentForm'

// Helper to create Response objects
const createMockResponse = (data: any) => {
  return new Response(
    JSON.stringify(data),
    {
      status: 200,
      statusText: 'OK',
      headers: new Headers({
        'Content-Type': 'application/json',
      }),
    }
  );
};

// Set up global fetch mock
global.fetch = mockFetch;

describe('StudentList', () => {
  beforeEach(() => {
    mockFetch.mockClear();
    // Setup default mock implementation
    mockFetch.mockImplementation((url: string | URL | Request, init?: RequestInit) => {
      if (typeof url === 'string') {
        const urlObj = new URL(url.startsWith('http') ? url : `http://localhost${url}`);
        
        // Handle student list/filter API calls
        if (urlObj.pathname === '/api/students') {
          const classParam = urlObj.searchParams.get('class');
          const sectionParam = urlObj.searchParams.get('section');
          
          // Return filtered data if class and section are provided
          if (classParam === '10' && sectionParam === 'A') {
            return Promise.resolve(createMockResponse({
              data: [{
                id: 1,
                first_name: 'John',
                last_name: 'Smith',
                admission_number: '2024001',
                class_name: 'Class 10',
                section: 'A',
              }],
              status: 'success'
            }));
          }
          
          // Default response for unfiltered list
          return Promise.resolve(createMockResponse({
            data: [],
            status: 'success'
          }));
        }
      }
      return Promise.reject(new Error(`Unhandled mock fetch call to ${url}`));
    });
  })

  it('renders student list', async () => {
    // Mock initial data load
    mockFetch.mockImplementation((url: string | URL | Request, init?: RequestInit) => {
      if (typeof url === 'string' && url.startsWith('/api/students')) {
        return Promise.resolve(createMockResponse({
          data: [
            {
              id: 1,
              first_name: 'John',
              last_name: 'Smith',
              admission_number: '2024001',
              class_name: 'Class 10',
              section: 'A',
            },
          ],
          status: 'success'
        }));
      }
      return Promise.reject(new Error('Unhandled mock fetch call'));
    })

    render(<StudentList />)

    // Wait for the API call to complete and data to be rendered
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalled()
    }, { timeout: 2000 })

    // Wait for the table to be populated
    const table = screen.getByRole('table')
    const rows = within(table).getAllByRole('row')
    expect(rows.length).toBeGreaterThan(1) // Header row + data row

    // Check if student data is rendered correctly
    const studentRow = rows[1] // First row after header
    expect(within(studentRow).getByText('John Smith')).toBeInTheDocument()
    expect(within(studentRow).getByText('2024001')).toBeInTheDocument()
    expect(within(studentRow).getByText('Class 10 - A')).toBeInTheDocument()
  })

  it('filters students by class and section', async () => {
    // Mock initial data load and filter
    mockFetch.mockImplementation((url: string | URL | Request, init?: RequestInit) => {
      if (typeof url === 'string') {
        const urlObj = new URL(url.startsWith('http') ? url : `http://localhost${url}`);
        if (urlObj.pathname === '/api/students') {
          const classParam = urlObj.searchParams.get('class');
          const sectionParam = urlObj.searchParams.get('section');
          
          return Promise.resolve(createMockResponse({
            data: [{
              id: 1,
              first_name: 'John',
              last_name: 'Smith',
              admission_number: '2024001',
              class_name: classParam ? `Class ${classParam}` : 'Class 10',
              section: sectionParam || 'A',
            }],
            status: 'success'
          }));
        }
      }
      return Promise.reject(new Error('Unhandled mock fetch call'));
    })

    render(<StudentList />)

    // Wait for loading state to complete
    await waitFor(() => {
      expect(screen.queryByRole('progressbar')).not.toBeInTheDocument()
    })

    // Get the select buttons (shadcn/ui Select components)
    const classSelect = await screen.findByLabelText(/class/i)
    const sectionSelect = await screen.findByLabelText(/section/i)

    // Open class select and wait for options
    fireEvent.click(classSelect)
    await waitFor(() => {
      expect(screen.getByRole('listbox')).toBeInTheDocument()
    })

    // Find and click the Class 10 option
    const classOption = screen.getByRole('option', { name: /class 10/i })
    fireEvent.click(classOption)

    // Open section select and wait for options
    fireEvent.click(sectionSelect)
    await waitFor(() => {
      expect(screen.getByRole('listbox')).toBeInTheDocument()
    })

    // Find and click the Section A option
    const sectionOption = screen.getByRole('option', { name: /section a/i })
    fireEvent.click(sectionOption)

    // Wait for the API call to be made after filter selection
    // Wait for the API call to be made after filter selection
    await waitFor(() => {
      const calls = mockFetch.mock.calls;
      
      // Find the GET request with class and section filters
      const filterCall = calls.find(call => {
        if (typeof call[0] !== 'string') return false;
        const urlStr = call[0].startsWith('http') ? call[0] : `http://localhost${call[0]}`;
        const url = new URL(urlStr);
        return url.pathname === '/api/students' && 
               url.searchParams.get('class') === '10' &&
               url.searchParams.get('section') === 'A';
      });

      // Verify the API call was made with correct parameters
      expect(filterCall).toBeTruthy();
      if (!filterCall) {
        console.error('Available API calls:', calls.map(call => 
          typeof call[0] === 'string' ? call[0] : 'non-string-url'
        ));
        return;
      }
      expect(filterCall[1]).toEqual(expect.any(Object));
    }, { timeout: 5000 });
  })
})

describe('StudentForm', () => {
  beforeEach(() => {
    mockFetch.mockClear();
    // Setup mock implementation for student creation and filtering
    mockFetch.mockImplementation((url, options) => {
      if (typeof url === 'string') {
        const urlObj = new URL(url.startsWith('http') ? url : `http://localhost${url}`);
        
        // Handle student list and filtering
        if (urlObj.pathname === '/api/students') {
          if (!options || options.method === 'GET') {
            const classParam = urlObj.searchParams.get('class');
            const sectionParam = urlObj.searchParams.get('section');
            
            // Return filtered data based on class and section
            if (classParam === '10' && sectionParam === 'A') {
              return createMockResponse({
                data: [{
                  id: 1,
                  first_name: 'John',
                  last_name: 'Smith',
                  admission_number: '2024001',
                  class_name: 'Class 10',
                  section: 'A',
                }],
                status: 'success'
              });
            }
            
            // Default response for unfiltered list
            return createMockResponse({
              data: [],
              status: 'success'
            });
          } else if (options.method === 'POST') {
            // Handle student creation
            return createMockResponse({
              data: {
                id: 1,
                admission_number: '2024001',
                first_name: 'John',
                last_name: 'Smith',
                class_name: 'Class 10',
                section: 'A',
              },
              status: 'success'
            });
          }
        }
      }
      return Promise.reject(new Error(`Unhandled mock fetch call to ${url}`));
    });
  })

  it('renders student form', () => {
    render(<StudentForm />)

    // Check for form fields using shadcn/ui selectors
    expect(screen.getByRole('textbox', { name: /first name/i })).toBeInTheDocument()
    expect(screen.getByRole('textbox', { name: /last name/i })).toBeInTheDocument()
    expect(screen.getByRole('textbox', { name: /admission number/i })).toBeInTheDocument()
    expect(screen.getByRole('textbox', { name: /roll number/i })).toBeInTheDocument()
    expect(screen.getByRole('combobox', { name: /class/i })).toBeInTheDocument()
    expect(screen.getByRole('combobox', { name: /section/i })).toBeInTheDocument()
    expect(screen.getByRole('textbox', { name: /parent name/i })).toBeInTheDocument()
    expect(screen.getByRole('textbox', { name: /parent phone/i })).toBeInTheDocument()
    expect(screen.getByRole('textbox', { name: /parent email/i })).toBeInTheDocument()
  })

  it('handles student creation', async () => {
    const user = userEvent.setup()
    // Mock student creation
    mockFetch.mockImplementation((input: string | URL | Request, init?: RequestInit): Promise<Response> => {
      const url = typeof input === 'string' ? input : input instanceof URL ? input.toString() : input.url;
      const urlObj = new URL(url.startsWith('http') ? url : `http://localhost${url}`);
      
      if (urlObj.pathname === '/api/students' && init?.method === 'POST') {
        return Promise.resolve(createMockResponse({
          data: {
            id: 1,
            admission_number: '2024001',
            first_name: 'John',
            last_name: 'Smith',
            class_name: 'Class 10',
            section: 'A',
          },
          status: 'success'
        }));
      }
      return Promise.reject(new Error('Unhandled mock fetch call'));
    })

    render(<StudentForm />)

    // Wait for form to be ready
    await waitFor(() => {
      expect(screen.queryByRole('progressbar')).not.toBeInTheDocument()
    })

    // Fill in form fields using shadcn/ui components
    const admissionInput = screen.getByRole('textbox', { name: /admission number/i })
    const rollInput = screen.getByRole('textbox', { name: /roll number/i })
    
    // Create and dispatch proper change events
    const admissionEvent = new Event('change', { bubbles: true })
    Object.defineProperty(admissionEvent, 'target', { value: { value: '2024001' } })
    admissionInput.dispatchEvent(admissionEvent)
    
    const rollEvent = new Event('change', { bubbles: true })
    Object.defineProperty(rollEvent, 'target', { value: { value: '101' } })
    rollInput.dispatchEvent(rollEvent)

    // Handle class select using fireEvent for Radix UI compatibility
    const classSelect = screen.getByLabelText(/class/i)
    fireEvent.mouseDown(classSelect)
    await waitFor(() => {
      expect(screen.getByRole('listbox')).toBeInTheDocument()
    })
    fireEvent.click(screen.getByRole('option', { name: /class 10/i }))
    fireEvent.mouseUp(classSelect)

    // Handle section select using fireEvent for Radix UI compatibility
    const sectionSelect = screen.getByLabelText(/section/i)
    fireEvent.mouseDown(sectionSelect)
    await waitFor(() => {
      expect(screen.getByRole('listbox')).toBeInTheDocument()
    })
    fireEvent.click(screen.getByRole('option', { name: /section a/i }))
    fireEvent.mouseUp(sectionSelect)

    // Fill in remaining form fields
    const firstNameInput = screen.getByRole('textbox', { name: /first name/i })
    const lastNameInput = screen.getByRole('textbox', { name: /last name/i })
    const parentNameInput = screen.getByRole('textbox', { name: /parent name/i })
    const parentPhoneInput = screen.getByRole('textbox', { name: /parent phone/i })
    const parentEmailInput = screen.getByRole('textbox', { name: /parent email/i })
    
    fireEvent.change(firstNameInput, { target: { value: 'John' } })
    fireEvent.change(lastNameInput, { target: { value: 'Smith' } })
    fireEvent.change(parentNameInput, { target: { value: 'Parent Name' } })
    fireEvent.change(parentPhoneInput, { target: { value: '1234567890' } })
    fireEvent.change(parentEmailInput, { target: { value: 'parent@example.com' } })

    // Submit form
    const submitButton = screen.getByRole('button', { name: /save/i })
    await user.click(submitButton)

    // Wait for the form submission to be processed
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/students'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      );
    });

    // Wait for form submission and API call
    await waitFor(() => {
      const calls = mockFetch.mock.calls;
      
      // Find the POST request to create a student
      const createCall = calls.find(call => {
        if (typeof call[0] !== 'string') return false;
        const urlStr = call[0].startsWith('http') ? call[0] : `http://localhost${call[0]}`;
        const url = new URL(urlStr);
        return url.pathname === '/api/students' && 
               call[1]?.method === 'POST';
      });

      // Verify the API call was made
      expect(createCall).toBeTruthy();
      if (!createCall) {
        console.error('Available API calls:', calls.map(call => 
          typeof call[0] === 'string' ? call[0] : 'non-string-url'
        ));
        return;
      }
      expect(createCall[1]).toEqual(
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
          body: expect.any(String),
        })
      )
    }, { timeout: 5000 })
  })

  it('handles validation errors', async () => {
    render(<StudentForm />)

    // Wait for form to be ready
    await waitFor(() => {
      expect(screen.queryByRole('progressbar')).not.toBeInTheDocument()
    })

    // Submit form without filling required fields
    const submitButton = screen.getByRole('button', { name: /save/i })
    fireEvent.click(submitButton)

    // Check for validation error messages
    await waitFor(() => {
      expect(screen.getByText(/first name is required/i)).toBeInTheDocument()
      expect(screen.getByText(/last name is required/i)).toBeInTheDocument()
      expect(screen.getByText(/admission number is required/i)).toBeInTheDocument()
      expect(screen.getByText(/roll number is required/i)).toBeInTheDocument()
      expect(screen.getByText(/class is required/i)).toBeInTheDocument()
      expect(screen.getByText(/section is required/i)).toBeInTheDocument()
      expect(screen.getByText(/parent name is required/i)).toBeInTheDocument()
      expect(screen.getByText(/parent phone is required/i)).toBeInTheDocument()
      expect(screen.getByText(/date of birth is required/i)).toBeInTheDocument()
    }, { timeout: 5000 })
  })
})
