// Import Jest's expect first
const { expect } = require("@jest/globals");
global.expect = expect;

// Then extend with jest-dom
require("@testing-library/jest-dom");

// Import and configure testing library
const { configure } = require("@testing-library/react");

// Configure testing-library
configure({ asyncUtilTimeout: 5000 });

// Increase timeout for async operations
jest.setTimeout(10000);

// Mock Next.js router and navigation
jest.mock("next/router", () => ({
  useRouter() {
    return {
      route: "/",
      pathname: "",
      query: {},
      asPath: "",
      push: jest.fn(),
      replace: jest.fn(),
      reload: jest.fn(),
      back: jest.fn(),
      prefetch: jest.fn(),
      beforePopState: jest.fn(),
      events: {
        on: jest.fn(),
        off: jest.fn(),
        emit: jest.fn(),
      },
    };
  },
}));

jest.mock("next/navigation", () => ({
  useRouter() {
    return {
      push: jest.fn(),
      replace: jest.fn(),
      back: jest.fn(),
    };
  },
  usePathname() {
    return "";
  },
  useSearchParams() {
    return new URLSearchParams();
  },
}));

// Setup test environment
beforeAll(() => {
  // Mock localStorage
  const mockLocalStorage = {
    getItem: jest.fn(),
    setItem: jest.fn(),
    clear: jest.fn(),
    removeItem: jest.fn(),
    length: 0,
    key: jest.fn(),
  };
  Object.defineProperty(window, "localStorage", {
    value: mockLocalStorage,
    writable: true,
  });

  // Mock ResizeObserver
  class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
  window.ResizeObserver = ResizeObserver;

  // Mock IntersectionObserver
  class IntersectionObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
  window.IntersectionObserver = IntersectionObserver;

  // Mock window.matchMedia
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: jest.fn().mockImplementation((query) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: jest.fn(),
      removeListener: jest.fn(),
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      dispatchEvent: jest.fn(),
    })),
  });

  // Mock Event
  class MockEvent {
    constructor(type, props = {}) {
      this.type = type;
      Object.assign(this, props);
    }
    preventDefault() {}
    stopPropagation() {}
  }
  global.Event = MockEvent;

  // Mock PointerEvent
  class MockPointerEvent extends MockEvent {
    constructor(type, props = {}) {
      super(type, props);
      this.pointerType = props?.pointerType || "mouse";
      this.pointerId = props?.pointerId || 1;
      this.clientX = props?.clientX || 0;
      this.clientY = props?.clientY || 0;
      this.pressure = props?.pressure || 0;
      this.width = props?.width || 1;
      this.height = props?.height || 1;
      this.isPrimary = props?.isPrimary || true;
      this.buttons = props?.buttons || 0;
    }
  }
  global.PointerEvent = MockPointerEvent;

  // Mock pointer capture methods
  Element.prototype.setPointerCapture = function () {};
  Element.prototype.releasePointerCapture = function () {};
  Element.prototype.hasPointerCapture = function () {
    return false;
  };

  // Mock scrollIntoView
  Element.prototype.scrollIntoView = jest.fn();
  window.HTMLElement.prototype.scrollIntoView = function () {};

  // Configure testing environment
  global.IS_REACT_ACT_ENVIRONMENT = true;

  // Mock fetch
  global.fetch = jest.fn();
});

// Setup for Radix UI portals and cleanup
beforeEach(() => {
  const portalRoot = document.createElement("div");
  portalRoot.setAttribute("id", "radix-portal");
  document.body.appendChild(portalRoot);
});

afterEach(() => {
  jest.clearAllMocks();
  const portalRoot = document.getElementById("radix-portal");
  if (portalRoot) {
    document.body.removeChild(portalRoot);
  }
});
