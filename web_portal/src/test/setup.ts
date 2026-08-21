import '@testing-library/jest-dom';
import { beforeEach } from 'vitest';

// Clean localStorage between tests
beforeEach(() => {
  localStorage.clear();
  sessionStorage.clear();
});
