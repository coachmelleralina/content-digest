import { describe, it, expect } from 'vitest';
import { resolveCategory } from './categories';

describe('resolveCategory', () => {
  it('returns the trimmed raw label when there is no existing match', () => {
    expect(resolveCategory('  Web3 ', [])).toBe('Web3');
  });

  it('collapses inner whitespace in a new label', () => {
    expect(resolveCategory('Machine  Learning', [])).toBe('Machine Learning');
  });

  it('matches an existing label case-insensitively and returns the existing casing', () => {
    expect(resolveCategory(' machine learning ', ['Machine Learning'])).toBe('Machine Learning');
  });

  it('treats hyphens as spaces when matching', () => {
    expect(resolveCategory('Machine-Learning', ['Machine Learning'])).toBe('Machine Learning');
  });

  it('merges singular/plural variants', () => {
    expect(resolveCategory('Startups', ['Startup'])).toBe('Startup');
    expect(resolveCategory('Startup', ['Startups'])).toBe('Startups');
  });

  it('matches an acronym to its spelled-out existing label', () => {
    expect(resolveCategory('AI', ['Artificial Intelligence'])).toBe('Artificial Intelligence');
  });

  it('matches a spelled-out label to an existing acronym', () => {
    expect(resolveCategory('Artificial Intelligence', ['AI'])).toBe('AI');
  });

  it('tolerates a single typo in longer labels', () => {
    expect(resolveCategory('Artifical Intelligence', ['Artificial Intelligence'])).toBe(
      'Artificial Intelligence',
    );
  });

  it('does not over-merge short distinct labels', () => {
    expect(resolveCategory('Art', ['AI'])).toBe('Art');
  });

  it('does not merge unrelated topics', () => {
    expect(resolveCategory('Health', ['Crypto', 'AI'])).toBe('Health');
  });

  it('prefers the exact fold match over weaker rules and earlier list entries win', () => {
    expect(resolveCategory('ai', ['Artificial Intelligence', 'AI'])).toBe('AI');
  });

  it('returns "Uncategorized" for empty or whitespace-only input', () => {
    expect(resolveCategory('   ', ['AI'])).toBe('Uncategorized');
  });
});
