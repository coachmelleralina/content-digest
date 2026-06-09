import { describe, it, expect } from 'vitest';
import { greeting } from './greeting';

describe('greeting', () => {
  it('returns a welcome line containing the project name', () => {
    expect(greeting('content-digest')).toContain('content-digest');
  });
});
