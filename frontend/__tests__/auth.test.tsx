// Import testing utilities first
import {
  render,
  screen,
  waitFor,
  within,
  fireEvent,
  act,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";

// Import components
import { LoginForm } from "@/components/auth/LoginForm";
import { RegisterForm } from "@/components/auth/RegisterForm";

// Import types
import type {
  LoginData,
  RegisterData,
  LoginResponse,
  RegisterResponse,
  ApiError,
} from "@/types/api";
import type { ApiClient } from "@/lib/api";
import type { RenderResult } from "@testing-library/react";

// Create mock functions
const mockPush = jest.fn();
const mockReplace = jest.fn();
const mockLogin = jest.fn<Promise<LoginResponse>, [LoginData]>();
const mockRegister = jest.fn<Promise<RegisterResponse>, [RegisterData]>();

// Mock modules before any test code
jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
    replace: mockReplace,
  }),
}));
jest.mock("@/lib/api");

const mockApi = jest.mocked(require("@/lib/api").default);
Object.defineProperty(mockApi, "login", { value: mockLogin });
Object.defineProperty(mockApi, "register", { value: mockRegister });

// Set up default mock implementations
mockLogin.mockImplementation((data: LoginData) =>
  Promise.resolve({
    data: {
      access_token: "test-token",
      user: { id: 1, username: data.username },
    },
  }),
);

mockRegister.mockImplementation((data: RegisterData) =>
  Promise.resolve({
    data: {
      id: 1,
      email: data.email,
      username: data.username,
      first_name: data.first_name,
      last_name: data.last_name,
      role: data.role || "student",
    },
  }),
);

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  clear: jest.fn(),
};
global.localStorage = localStorageMock as any;

// Mock axios
jest.mock("axios", () => ({
  create: jest.fn(() => ({
    post: jest.fn(),
    interceptors: {
      request: { use: jest.fn(), eject: jest.fn() },
      response: { use: jest.fn(), eject: jest.fn() },
    },
  })),
}));

// Set up mock implementations before each test
beforeEach(() => {
  jest.clearAllMocks();
  localStorage.clear();

  // Reset mocks
  mockLogin.mockReset();
  mockRegister.mockReset();
  mockPush.mockReset();
  mockReplace.mockReset();

  // Type the mock functions
  mockLogin.mockImplementation((data: LoginData) =>
    Promise.resolve({
      data: {
        access_token: "test-token",
        user: { id: 1, username: data.username },
      },
    }),
  );

  mockRegister.mockImplementation((data: RegisterData) =>
    Promise.resolve({
      data: {
        id: 1,
        email: data.email,
        username: data.username,
        first_name: data.first_name,
        last_name: data.last_name,
        role: data.role || "student",
      },
    }),
  );
});

describe("LoginForm", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it("renders login form", () => {
    render(<LoginForm />);
    expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /login/i })).toBeInTheDocument();
  });

  it("handles successful login", async () => {
    const mockResponse: LoginResponse = {
      data: {
        access_token: "test-token",
        user: { id: 1, username: "testuser" },
      },
    };
    mockLogin.mockImplementationOnce(() => Promise.resolve(mockResponse));

    render(<LoginForm />);

    // Get form elements using shadcn/ui structure
    const usernameInput = screen.getByPlaceholderText(/enter your username/i);
    const passwordInput = screen.getByPlaceholderText(/enter your password/i);

    const user = userEvent.setup();
    // Fill in form fields using fireEvent
    fireEvent.change(usernameInput, { target: { value: "testuser" } });
    fireEvent.change(passwordInput, { target: { value: "testpass" } });

    // Submit form
    const loginButton = screen.getByRole("button", { name: /login/i });
    await user.click(loginButton);

    // Wait for form submission and verify API call
    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith({
        username: "testuser",
        password: "testpass",
      });

      // Verify localStorage updates
      expect(localStorage.setItem).toHaveBeenCalledWith("token", "test-token");
      expect(localStorage.setItem).toHaveBeenCalledWith(
        "user",
        JSON.stringify({ id: 1, username: "testuser" }),
      );
    });
  });

  it("handles login error", async () => {
    const mockError = {
      response: { data: { detail: "Invalid credentials" } },
    };
    mockLogin.mockRejectedValueOnce(mockError);

    render(<LoginForm />);

    // Get form elements using shadcn/ui structure
    const usernameInput = screen.getByPlaceholderText(/enter your username/i);
    const passwordInput = screen.getByPlaceholderText(/enter your password/i);

    const user = userEvent.setup();
    // Fill in form fields using fireEvent
    fireEvent.change(usernameInput, { target: { value: "wronguser" } });
    fireEvent.change(passwordInput, { target: { value: "wrongpass" } });

    // Submit form and wait for error
    await act(async () => {
      await user.click(screen.getByRole("button", { name: /login/i }));
    });

    // Verify error message
    await waitFor(() => {
      const errorElement = screen.getByRole("alert");
      expect(errorElement).toHaveTextContent(/invalid credentials/i);
    });
  });
});

describe("RegisterForm", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it("renders register form", () => {
    render(<RegisterForm />);

    // Check for form fields using placeholders
    expect(
      screen.getByPlaceholderText(/enter your email/i),
    ).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText(/choose a username/i),
    ).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText(/choose a password/i),
    ).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText(/enter your first name/i),
    ).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText(/enter your last name/i),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /register/i }),
    ).toBeInTheDocument();
    // Check for role select using combobox role
    const roleSelect = screen.getByRole("combobox", { name: /role/i });
    expect(roleSelect).toBeInTheDocument();
  });

  it("handles successful registration", async () => {
    const user = userEvent.setup();
    const mockRegisterResponse: RegisterResponse = {
      data: {
        id: 1,
        email: "test@example.com",
        username: "testuser",
        first_name: "Test",
        last_name: "User",
        role: "student",
      },
    };
    mockRegister.mockImplementationOnce(() =>
      Promise.resolve(mockRegisterResponse),
    );

    console.log("Starting registration test with enhanced logging");
    const { container } = render(<RegisterForm />);
    console.log("Form rendered, DOM structure:", container.innerHTML);

    // Get form elements using shadcn/ui structure
    const emailInput = screen.getByPlaceholderText(/enter your email/i);
    const usernameInput = screen.getByPlaceholderText(/choose a username/i);
    const passwordInput = screen.getByPlaceholderText(/choose a password/i);
    const firstNameInput = screen.getByPlaceholderText(
      /enter your first name/i,
    );
    const lastNameInput = screen.getByPlaceholderText(/enter your last name/i);

    console.log("Form elements found:", {
      emailInput: emailInput.outerHTML,
      usernameInput: usernameInput.outerHTML,
      passwordInput: passwordInput.outerHTML,
      firstNameInput: firstNameInput.outerHTML,
      lastNameInput: lastNameInput.outerHTML,
    });
    // Fill in form fields using fireEvent
    fireEvent.change(emailInput, { target: { value: "test@example.com" } });
    fireEvent.change(usernameInput, { target: { value: "testuser" } });
    fireEvent.change(passwordInput, { target: { value: "testpass123" } }); // Longer password
    fireEvent.change(firstNameInput, { target: { value: "Test" } });
    fireEvent.change(lastNameInput, { target: { value: "User" } });

    console.log("Handling role selection");
    // Handle role selection using combobox
    const roleSelect = screen.getByRole("combobox", { name: /role/i });
    await user.click(roleSelect);

    // Wait for role options to be visible and select student role
    await waitFor(
      async () => {
        const options = screen.getAllByRole("option");
        const studentOption = options.find((option) =>
          option.textContent?.toLowerCase().includes("student"),
        );
        expect(studentOption).toBeTruthy();
        if (studentOption) {
          await user.click(studentOption);
        }
      },
      { timeout: 2000 },
    );

    // Verify role is selected
    await waitFor(
      () => {
        expect(roleSelect).toHaveTextContent(/student/i);
      },
      { timeout: 2000 },
    );

    console.log("Role selected, submitting form");
    // Submit form and wait for API call
    const submitButton = screen.getByRole("button", { name: /register/i });

    // Submit form and wait for validation
    await act(async () => {
      await user.click(submitButton);
      // Wait for form validation and submission
      await new Promise((resolve) => setTimeout(resolve, 2000));
    });

    console.log("Waiting for API call");
    // Wait for API call with increased timeout
    await waitFor(
      () => {
        expect(mockRegister).toHaveBeenCalled();
      },
      { timeout: 5000 },
    );

    console.log("Verifying API call parameters");
    // Wait for the form submission and API call with increased timeout
    await waitFor(
      () => {
        expect(mockRegister).toHaveBeenCalledWith({
          email: "test@example.com",
          username: "testuser",
          password: "testpass123",
          first_name: "Test",
          last_name: "User",
          role: "student",
        });
      },
      { timeout: 5000 },
    );

    // Wait for navigation
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/login");
    });
  });

  it("handles registration error", async () => {
    const user = userEvent.setup();
    const mockError = {
      response: { data: { detail: "Email already exists" } },
    };
    mockRegister.mockRejectedValueOnce(mockError);

    render(<RegisterForm />);

    // Wait for form to be rendered
    await waitFor(() => {
      expect(
        screen.getByPlaceholderText(/enter your email/i),
      ).toBeInTheDocument();
    });

    // Get form elements using shadcn/ui structure
    const emailInput = screen.getByPlaceholderText(/enter your email/i);
    const usernameInput = screen.getByPlaceholderText(/choose a username/i);
    const passwordInput = screen.getByPlaceholderText(/choose a password/i);
    const firstNameInput = screen.getByPlaceholderText(
      /enter your first name/i,
    );
    const lastNameInput = screen.getByPlaceholderText(/enter your last name/i);

    // Fill in form fields using fireEvent
    fireEvent.change(emailInput, { target: { value: "existing@example.com" } });
    fireEvent.change(usernameInput, { target: { value: "existinguser" } });
    fireEvent.change(passwordInput, { target: { value: "testpass" } });
    fireEvent.change(firstNameInput, { target: { value: "Test" } });
    fireEvent.change(lastNameInput, { target: { value: "User" } });

    // Handle role selection using shadcn/ui Select
    const roleSelect = screen.getByRole("combobox", { name: /role/i });
    await user.click(roleSelect);

    // Wait for portal and select student option
    await waitFor(async () => {
      const listbox = await screen.findByRole("listbox");
      expect(listbox).toBeInTheDocument();
    });
    const studentOption = await screen.findByRole("option", {
      name: /student/i,
    });
    await user.click(studentOption);

    // Submit form and wait for error
    const submitButton = screen.getByRole("button", { name: /register/i });

    // Submit form and wait for validation
    await act(async () => {
      await user.click(submitButton);
      // Wait for form validation and submission
      await new Promise((resolve) => setTimeout(resolve, 100));
    });

    // Wait for API call with increased timeout
    await waitFor(
      () => {
        expect(mockRegister).toHaveBeenCalled();
      },
      { timeout: 5000 },
    );

    // Wait for the form submission and error handling with increased timeout
    await waitFor(() => {
      expect(mockRegister).toHaveBeenCalledWith({
        email: "existing@example.com",
        username: "existinguser",
        password: "testpass",
        first_name: "Test",
        last_name: "User",
        role: "student",
      });
    });

    // Wait for error message
    await waitFor(() => {
      const errorElement = screen.getByRole("alert");
      expect(errorElement).toBeInTheDocument();
      expect(errorElement).toHaveTextContent(/email already exists/i);
    });
  });
});
