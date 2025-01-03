const nextJest = require('next/jest');

const createJestConfig = nextJest({
  // Provide the path to your Next.js app to load next.config.js and .env files in your test environment
  dir: './',
});

// Add any custom config to be passed to Jest
const customJestConfig = {
  testEnvironment: 'jest-environment-jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  moduleNameMapper: {
    // Handle module aliases
    '^@/(.*)$': '<rootDir>/src/$1',
    '^@/components/(.*)$': '<rootDir>/src/components/$1',
    '^@/pages/(.*)$': '<rootDir>/src/pages/$1',
    '^@/lib/(.*)$': '<rootDir>/src/lib/$1',
    '^@/services/(.*)$': '<rootDir>/src/services/$1',
    // Handle CSS imports
    '^.+\\.module\\.(css|sass|scss)$': 'identity-obj-proxy',
    '^.+\\.(css|sass|scss)$': '<rootDir>/__mocks__/styleMock.js',
  },
  transform: {
    // Use babel-jest to transpile tests with the next/babel preset
    '^.+\\.(js|jsx|ts|tsx)$': ['babel-jest', { presets: ['next/babel'] }],
  },
  testMatch: ['**/__tests__/**/*.test.[jt]s?(x)'],
  testPathIgnorePatterns: ['<rootDir>/node_modules/', '<rootDir>/.next/'],
  coveragePathIgnorePatterns: ['/node_modules/', '/.next/', '/coverage/'],
  transformIgnorePatterns: [
    '/node_modules/(?!(@radix-ui|@hookform|class-variance-authority|cmdk|@shadcn|next/dist/client/router)/)',
  ],
  moduleDirectories: ['node_modules', '<rootDir>'],
  testEnvironmentOptions: {
    customExportConditions: [''],
  },
  testTimeout: 10000,
  verbose: true,
  collectCoverage: false,
};

// createJestConfig is exported this way to ensure that next/jest can load the Next.js config which is async
module.exports = createJestConfig(customJestConfig);
