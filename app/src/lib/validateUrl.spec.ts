// Spec for feature 006 (issue #3) — see docs/requirements/feature-006-url-input.md
import { describe, expect, it } from 'vitest';
import { toErrorMessage, validateUrl } from './validateUrl';

describe('validateUrl', () => {
  describe('valid input → normalized URL', () => {
    it('accepts a plain https URL', () => {
      expect(validateUrl('https://example.com/article')).toEqual({
        ok: true,
        url: 'https://example.com/article',
      });
    });

    it('accepts a plain http URL', () => {
      expect(validateUrl('http://example.com/article')).toEqual({
        ok: true,
        url: 'http://example.com/article',
      });
    });

    it('trims surrounding whitespace', () => {
      expect(validateUrl('  https://example.com/article \n')).toEqual({
        ok: true,
        url: 'https://example.com/article',
      });
    });

    it('prepends https:// when the scheme is missing but the host looks valid', () => {
      expect(validateUrl('example.com/article')).toEqual({
        ok: true,
        url: 'https://example.com/article',
      });
    });

    it('handles schemeless www hosts', () => {
      expect(validateUrl('www.example.com')).toEqual({
        ok: true,
        url: 'https://www.example.com/',
      });
    });

    it('treats host:port without a scheme as a host, not a scheme', () => {
      expect(validateUrl('example.com:8080/feed')).toEqual({
        ok: true,
        url: 'https://example.com:8080/feed',
      });
    });

    it('is case-insensitive about the scheme and normalizes via URL.href', () => {
      expect(validateUrl('HTTPS://Example.COM')).toEqual({
        ok: true,
        url: 'https://example.com/',
      });
    });

    it('preserves query strings and fragments', () => {
      expect(validateUrl('example.com/a?b=1&c=2#sec')).toEqual({
        ok: true,
        url: 'https://example.com/a?b=1&c=2#sec',
      });
    });

    it('accepts localhost with an explicit scheme (dev convenience)', () => {
      expect(validateUrl('http://localhost:8000/api/health')).toEqual({
        ok: true,
        url: 'http://localhost:8000/api/health',
      });
    });
  });

  describe('empty input', () => {
    it.each(['', '   ', '\n\t '])('rejects %j', (input) => {
      expect(validateUrl(input)).toEqual({ ok: false, reason: 'Enter a URL.' });
    });
  });

  describe('non-http(s) schemes', () => {
    it.each([
      'ftp://example.com/file.txt',
      'mailto:someone@example.com',
      'javascript:alert(1)',
      'file:///etc/passwd',
      'data:text/html,<h1>hi</h1>',
    ])('rejects %s', (input) => {
      expect(validateUrl(input)).toEqual({
        ok: false,
        reason: 'Only http(s) URLs are supported.',
      });
    });
  });

  describe('garbage / implausible input', () => {
    it.each([
      'hello world',
      'foo', // no dot — not a plausible public host
      'https://foo', // explicit scheme but still no dot
      'http://', // scheme with nothing behind it
      '!!!',
      'https://exa mple.com',
    ])('rejects %j', (input) => {
      expect(validateUrl(input)).toEqual({
        ok: false,
        reason: "That doesn't look like a valid URL.",
      });
    });

    it('rejects schemeless localhost (documented out of scope)', () => {
      const result = validateUrl('localhost:8000');
      expect(result.ok).toBe(false);
    });
  });

  describe('purity', () => {
    it('returns a fresh result object each call', () => {
      const a = validateUrl('example.com');
      const b = validateUrl('example.com');
      expect(a).toEqual(b);
      expect(a).not.toBe(b);
    });
  });
});

describe('toErrorMessage', () => {
  it('returns the message of an Error instance', () => {
    expect(toErrorMessage(new Error('Digest failed: 502'))).toBe('Digest failed: 502');
  });

  it('falls back when an Error has an empty message', () => {
    expect(toErrorMessage(new Error(''))).toBe('Something went wrong.');
  });

  it.each([['plain string'], [undefined], [null], [{ message: 'not an Error' }]])(
    'falls back for non-Error throwable %j',
    (thrown) => {
      expect(toErrorMessage(thrown)).toBe('Something went wrong.');
    },
  );
});
