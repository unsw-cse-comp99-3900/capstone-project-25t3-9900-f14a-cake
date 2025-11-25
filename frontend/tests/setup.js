// Jest setup file
// Note: Vue Test Utils configuration is done in jest.config.js or individual test files

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
global.localStorage = localStorageMock;

// Mock window.location
delete window.location;
window.location = { 
  href: 'http://localhost',
  origin: 'http://localhost',
  pathname: '/',
  search: '',
  hash: ''
};

// Note: Do not mock URL constructor - axios needs the real URL constructor
// Only mock URL.createObjectURL and URL.revokeObjectURL if needed for specific tests

