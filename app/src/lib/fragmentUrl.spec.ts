// Spec for feature 016 (issue #15) — text-fragment deep links for takeaways.

import { describe, it, expect } from 'vitest';
import { takeawayHref } from './fragmentUrl';

describe('takeawayHref', () => {
  it('returns null when the key point has no grounding quote', () => {
    expect(takeawayHref('https://example.com/article', null)).toBe(null);
  });

  it('appends an encoded #:~:text= fragment to the article url', () => {
    expect(takeawayHref('https://example.com/article', 'plainword')).toBe(
      'https://example.com/article#:~:text=plainword',
    );
  });

  it('strips an existing #fragment from the article url first', () => {
    expect(takeawayHref('https://example.com/article#section-2', 'plainword')).toBe(
      'https://example.com/article#:~:text=plainword',
    );
  });

  it('percent-encodes spaces in the quote', () => {
    expect(takeawayHref('https://example.com/a', 'two words')).toBe(
      'https://example.com/a#:~:text=two%20words',
    );
  });

  it('percent-encodes quote characters', () => {
    expect(takeawayHref('https://example.com/a', 'the "unattended hour" threshold')).toBe(
      'https://example.com/a#:~:text=the%20%22unattended%20hour%22%20threshold',
    );
  });

  it('percent-encodes Cyrillic quotes', () => {
    expect(takeawayHref('https://example.com/a', 'мысль')).toBe(
      'https://example.com/a#:~:text=%D0%BC%D1%8B%D1%81%D0%BB%D1%8C',
    );
  });
});
