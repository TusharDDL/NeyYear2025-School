/// <reference types="@testing-library/jest-dom" />

import '@testing-library/jest-dom';

declare global {
  namespace jest {
    interface Matchers<R, T = any> {
      toBeInTheDocument(): R;
      toHaveTextContent(text: string | RegExp, options?: { normalizeWhitespace: boolean }): R;
      toBeVisible(): R;
      toHaveAttribute(attr: string, value?: string | RegExp): R;
      toHaveClass(...classNames: string[]): R;
      toHaveValue(value: string | number | string[]): R;
      toBeDisabled(): R;
      toBeEnabled(): R;
      toHaveStyle(css: string | Record<string, any>): R;
      toBeChecked(): R;
      toBePartiallyChecked(): R;
      toHaveFocus(): R;
      toHaveRole(role: string): R;
      toHaveDisplayValue(value: string | RegExp | Array<string | RegExp>): R;
      toBeEmpty(): R;
      toBeEmptyDOMElement(): R;
      toBeInvalid(): R;
      toBeRequired(): R;
      toBeValid(): R;
      toContainElement(element: HTMLElement | null): R;
      toContainHTML(html: string): R;
      toHaveAccessibleDescription(description?: string | RegExp): R;
      toHaveAccessibleName(name?: string | RegExp): R;
      toHaveErrorMessage(message?: string | RegExp): R;
      toHaveFormValues(values: { [name: string]: any }): R;
    }
  }
}
