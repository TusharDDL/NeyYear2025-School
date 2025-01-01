// Import types first
import type { MockResponse, ApiResponse } from '../src/types/test-utils'
import type { Book } from '@/types/book'

// Create QueryClient instance before any imports
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
})

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

// Set up global fetch mock with default implementation
mockFetch.mockImplementation((url: string | URL | Request, init?: RequestInit) => 
  Promise.resolve(new Response(
    JSON.stringify({ data: [], status: 'success' }),
    {
      status: 200,
      statusText: 'OK',
      headers: new Headers({ 'Content-Type': 'application/json' })
    }
  ))
);

global.fetch = mockFetch;

// Import components and testing utilities after mocks
import { render, screen, fireEvent, waitFor, within, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import '@testing-library/jest-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BookCatalog } from '@/components/library/BookCatalog'
import { BookCirculation } from '@/components/library/BookCirculation'

describe('BookCatalog', () => {
  beforeEach(() => {
    mockFetch.mockClear();
    // Setup initial fetch mock response for book catalog
    mockFetch.mockImplementationOnce(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({
          data: [],
          status: 'success'
        }),
        status: 200,
        statusText: 'OK',
        headers: new Headers({ 'Content-Type': 'application/json' })
      } as Response)
    );
  });

  it('renders book catalog', async () => {
    mockFetch.mockImplementation(() => Promise.resolve({
      ok: true,
      json: () =>
        Promise.resolve({
          data: [
            {
              id: 1,
              title: 'Test Book',
              author: 'Test Author',
              isbn: '1234567890',
              publisher: 'Test Publisher',
              category: 'fiction',
              available_copies: 5,
              location: 'Test Location',
            },
          ],
          status: 'success'
        }),
      status: 200,
      statusText: 'OK',
      headers: new Headers(),
      type: 'basic',
      url: 'http://localhost:3000/api/books',
      redirected: false,
      bodyUsed: false
    } as Response))

    render(
      <QueryClientProvider client={queryClient}>
        <BookCatalog />
      </QueryClientProvider>
    )

    // Wait for loading state to complete
    await waitFor(() => {
      expect(screen.queryByRole('progressbar')).not.toBeInTheDocument()
    })

    // Wait for loading state and then data rendering
    await waitFor(
      () => {
        // First verify the data has been loaded
        expect(mockFetch).toHaveBeenCalled()
        const fetchUrl = mockFetch.mock.calls[0][0]
        expect(typeof fetchUrl === 'string' && fetchUrl.includes('/api/books')).toBeTruthy()
      },
      { timeout: 5000 }
    )

    // Now check for rendered content
    const bookTitle = await screen.findByText('Test Book')
    expect(bookTitle).toBeInTheDocument()
    
    const bookAuthor = await screen.findByText('Test Author')
    expect(bookAuthor).toBeInTheDocument()
    
    const bookCategory = await screen.findByText('fiction')
    expect(bookCategory).toBeInTheDocument()
  })

  it('handles book search', async () => {
    mockFetch.mockImplementation((url) => {
      if (typeof url === 'string') {
        const urlObj = new URL(url.startsWith('http') ? url : `http://localhost${url}`);
        
        // Handle book search
        if (urlObj.pathname === '/api/books/search') {
          return Promise.resolve({
            ok: true,
            json: () =>
              Promise.resolve({
                data: [
                  {
                    id: 1,
                    title: 'Physics Book',
                    author: 'Physics Author',
                    isbn: '1234567890',
                    publisher: 'Physics Publisher',
                    category: 'science',
                    available_copies: 5,
                    location: 'Science Section',
                  },
                ],
                status: 'success'
              }),
            status: 200,
            statusText: 'OK',
            headers: new Headers(),
            type: 'basic',
            url: urlObj.toString(),
            redirected: false,
            bodyUsed: false
          } as Response);
        }
      }
      return Promise.reject(new Error('Unhandled mock fetch call'));
    })

    render(
      <QueryClientProvider client={queryClient}>
        <BookCatalog />
      </QueryClientProvider>
    )

    // Wait for loading state to complete and search input to be rendered
    await waitFor(() => {
      expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
      expect(screen.getByRole('textbox', { name: /search books/i })).toBeInTheDocument();
    }, { timeout: 5000 });

    // Find and interact with search input
    const searchInput = screen.getByRole('textbox', { name: /search books/i });
    
    // Use act to handle state updates
    await act(async () => {
      fireEvent.change(searchInput, { target: { value: 'physics' } });
    });

    // Wait for the search API call and verify results
    await waitFor(() => {
      const calls = mockFetch.mock.calls;
      const searchCall = calls.find(call => {
        if (typeof call[0] !== 'string') return false;
        const urlStr = call[0].startsWith('http') ? call[0] : `http://localhost${call[0]}`;
        const url = new URL(urlStr);
        return url.pathname === '/api/books/search' && 
               url.searchParams.get('query') === 'physics';
      });

      expect(searchCall).toBeTruthy();
      if (!searchCall) {
        console.error('Available API calls:', calls.map(call => 
          typeof call[0] === 'string' ? call[0] : 'non-string-url'
        ));
        return;
      }

      // Verify search results are displayed
      expect(screen.getByText('Physics Book')).toBeInTheDocument();
      expect(screen.getByText('Physics Author')).toBeInTheDocument();
    }, { timeout: 5000 })
  })
})

describe('BookCirculation', () => {
  beforeEach(() => {
    mockFetch.mockClear();
    // Setup initial fetch mock response for circulation
    mockFetch.mockImplementationOnce(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({
          data: [],
          status: 'success'
        }),
        status: 200,
        statusText: 'OK',
        headers: new Headers({ 'Content-Type': 'application/json' })
      } as Response)
    );
  });

  it('renders circulation records', async () => {
    // Mock fetch implementation for circulation records
    mockFetch.mockImplementation(() => Promise.resolve({
      ok: true,
      json: () => Promise.resolve({
        data: [
          {
            id: 1,
            book: {
              id: 1,
              title: 'Test Book',
              author: 'Test Author',
              isbn: '1234567890',
            },
            member: {
              id: 1,
              user: {
                id: 1,
                first_name: 'John',
                last_name: 'Smith',
                email: 'john@example.com',
              },
              admission_number: 'ADM001',
            },
            issue_date: '2024-01-15',
            due_date: '2024-01-29',
            return_date: null,
            status: 'issued',
            fine_amount: 0,
          }
        ],
        status: 'success'
      }),
      status: 200,
      statusText: 'OK',
      headers: new Headers({
        'Content-Type': 'application/json'
      }),
      type: 'basic',
      url: '/api/books/circulation',
      redirected: false,
      bodyUsed: false
    } as Response))

    render(
      <QueryClientProvider client={queryClient}>
        <BookCirculation />
      </QueryClientProvider>
    )

    // Wait for loading state to complete
    await waitFor(() => {
      expect(screen.queryByRole('progressbar')).not.toBeInTheDocument()
    })

    // Wait for loading state and then data rendering
    await waitFor(
      () => {
        // First verify the data has been loaded
        expect(mockFetch).toHaveBeenCalled()
        const fetchUrl = mockFetch.mock.calls[0][0]
        expect(typeof fetchUrl === 'string' && fetchUrl.includes('/api/books/circulation')).toBeTruthy()
      },
      { timeout: 5000 }
    )

    // Now check for rendered content
    const bookTitle = await screen.findByText('Test Book')
    expect(bookTitle).toBeInTheDocument()
    
    const memberName = await screen.findByText(/john smith/i)
    expect(memberName).toBeInTheDocument()
    
    const status = await screen.findByText('issued')
    expect(status).toBeInTheDocument()
  })

  it('handles book return', async () => {
    mockFetch
      .mockImplementationOnce(() => Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({
            data: [
              {
                id: 1,
                book: {
                  id: 1,
                  title: 'Test Book',
                  author: 'Test Author',
                  isbn: '1234567890',
                },
                member: {
                  id: 1,
                  user: {
                    id: 1,
                    first_name: 'John',
                    last_name: 'Smith',
                    email: 'john@example.com',
                  },
                  admission_number: 'ADM001',
                },
                issue_date: '2024-01-15',
                due_date: '2024-01-29',
                return_date: null,
                status: 'issued',
                fine_amount: 0,
              },
            ],
            status: 'success'
          }),
        status: 200,
        statusText: 'OK',
        headers: new Headers(),
        type: 'basic',
        url: 'http://localhost:3000/api/books/circulation',
        redirected: false,
        bodyUsed: false
      } as Response))
      .mockImplementationOnce(() => Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({
            data: {
              id: 1,
              book: {
                id: 1,
                title: 'Test Book',
                author: 'Test Author',
                isbn: '1234567890',
              },
              member: {
                id: 1,
                user: {
                  id: 1,
                  first_name: 'John',
                  last_name: 'Smith',
                  email: 'john@example.com',
                },
                admission_number: 'ADM001',
              },
              issue_date: '2024-01-15',
              due_date: '2024-01-29',
              return_date: '2024-01-20',
              status: 'returned',
              fine_amount: 0,
            },
            status: 'success'
          }),
        status: 200,
        statusText: 'OK',
        headers: new Headers({
          'Content-Type': 'application/json'
        }),
        type: 'basic',
        url: 'http://localhost:3000/api/books/circulation/1/return',
        redirected: false,
        bodyUsed: false
      } as Response))

    render(
      <QueryClientProvider client={queryClient}>
        <BookCirculation />
      </QueryClientProvider>
    )

    // Wait for loading state and then data rendering
    await waitFor(
      () => {
        const table = screen.getByRole('table')
        const tbody = table.querySelector('tbody')
        expect(tbody).toBeTruthy()
        
        // Type assertion since we verified tbody exists
        const dataRows = tbody ? within(tbody as HTMLElement).getAllByRole('row') : []
        expect(dataRows).toBeDefined()
        expect(dataRows.length).toBe(1) // One data row
        
        const circulationRow = dataRows[0]
        expect(within(circulationRow).getByText('Test Book')).toBeInTheDocument()
        expect(within(circulationRow).getByText(/john smith/i)).toBeInTheDocument()
        expect(within(circulationRow).getByText('issued')).toBeInTheDocument()
      },
      { timeout: 5000 }
    )

    // Find the table row containing the circulation record
    const row = screen.getByRole('row', { name: /test book.*john smith/i })
    expect(row).toBeInTheDocument()

    // Find and click the return button within the row
    const returnButton = within(row).getByRole('button', { name: /return/i })
    await userEvent.click(returnButton)

    // Verify the API call
    await waitFor(() => {
      const calls = mockFetch.mock.calls
      const returnCall = calls.find(call => 
        call[0] === '/api/books/circulation/1/return' && 
        call[1]?.method === 'POST'
      )
      expect(returnCall).toBeTruthy()
      if (!returnCall) throw new Error('Return API call not found')
      expect(returnCall[1]).toEqual(
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json'
          })
        })
      )
    }, { timeout: 5000 })
  })
})
