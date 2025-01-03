import "@testing-library/jest-dom";

declare global {
  namespace jest {
    interface Matchers<R> {
      toBeInTheDocument(): R;
      toHaveTextContent(text: string): R;
    }
  }
}

export interface Student {
  id: number;
  first_name: string;
  last_name: string;
  admission_number: string;
  class_name: string;
  section: string;
  roll_number?: string;
  parent_name?: string;
  parent_phone?: string;
  parent_email?: string;
}

export interface ApiResponse<T> {
  data: T;
  status: string;
}

export interface MockResponse<T = any> extends Response {
  ok: boolean;
  json: () => Promise<T>;
  status: number;
  statusText: string;
  headers: Headers;
  type?: ResponseType;
  url?: string;
  redirected?: boolean;
  body?: ReadableStream<Uint8Array> | null;
  bodyUsed?: boolean;
}

declare global {
  let fetch: jest.Mock<
    Promise<MockResponse<ApiResponse<any>>>,
    [input: RequestInfo | URL, init?: RequestInit]
  >;
  interface Window {
    matchMedia: jest.Mock;
  }
}

export {};
