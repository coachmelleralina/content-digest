import { describe, it, expect, beforeEach } from 'vitest';
import type { Card, SimilarRef } from '../types';
import { mockCards } from '../mocks/cards';
import { resolveCategory } from './categories';
import { ApiError } from './apiError';
import {
  digestUrl,
  listCards,
  deleteCard,
  translateCard,
  findSimilar,
  resetApiMock,
} from './api';
import type { Language } from './languages';

// The exact key set of the Card type (feature 003; feature 017 adds
// `language`). If Card gains/loses a field, this list — and the API
// contract — must change consciously.
const CARD_KEYS = [
  'category',
  'createdAt',
  'id',
  'keyPoints',
  'language',
  'summary',
  'tags',
  'title',
  'url',
] as const;

const expectApiError = async (
  promise: Promise<unknown>,
  message: string,
  status: number,
): Promise<void> => {
  let caught: unknown;
  try {
    await promise;
  } catch (e) {
    caught = e;
  }
  expect(caught).toBeInstanceOf(ApiError);
  expect(caught).toBeInstanceOf(Error);
  const err = caught as ApiError;
  expect(err.name).toBe('ApiError');
  expect(err.message).toBe(message);
  expect(err.status).toBe(status);
};

beforeEach(() => {
  resetApiMock();
});

describe('ApiError', () => {
  it('is an Error with a user-displayable message and optional status', () => {
    const withStatus = new ApiError('Could not extract this article', 422);
    expect(withStatus).toBeInstanceOf(Error);
    expect(withStatus.message).toBe('Could not extract this article');
    expect(withStatus.status).toBe(422);

    const withoutStatus = new ApiError('Something went wrong');
    expect(withoutStatus.status).toBeUndefined();
  });
});

describe('listCards', () => {
  it('resolves with the seeded mock cards', async () => {
    const cards = await listCards();
    expect(cards).toHaveLength(mockCards.length);
    expect(cards.map((c) => c.id).sort()).toEqual(mockCards.map((c) => c.id).sort());
  });

  it('returns a copy: mutating the result does not affect the store', async () => {
    const first = await listCards();
    first.pop();
    first[0]!.title = 'mutated';
    const second = await listCards();
    expect(second).toHaveLength(mockCards.length);
    expect(second.find((c) => c.id === mockCards[0]!.id)?.title).toBe(mockCards[0]!.title);
  });
});

describe('digestUrl', () => {
  const url = 'https://example.com/posts/why-deep-work-still-wins';

  it('resolves with a Card whose keys match the Card type shape exactly', async () => {
    const card = await digestUrl(url);
    expect(Object.keys(card).sort()).toEqual([...CARD_KEYS]);
  });

  it('generates a plausible card for the url', async () => {
    const before = await listCards();
    const card = await digestUrl(url);

    expect(card.id).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/);
    expect(card.url).toBe(url);
    expect(card.title.length).toBeGreaterThan(0);
    expect(card.summary.length).toBeGreaterThan(0);
    expect(card.keyPoints.length).toBeGreaterThanOrEqual(2);
    expect(card.tags.length).toBeGreaterThanOrEqual(1);
    expect(Number.isNaN(Date.parse(card.createdAt))).toBe(false);
    expect(Math.abs(Date.now() - Date.parse(card.createdAt))).toBeLessThan(10_000);

    // Category went through resolveCategory against the pre-call board
    // categories: re-resolving it is a no-op (it is already a board label).
    const existing = [...new Set(before.map((c) => c.category))];
    expect(card.category.length).toBeGreaterThan(0);
    expect(resolveCategory(card.category, existing)).toBe(card.category);
  });

  it('simulates ~300ms latency', async () => {
    const started = Date.now();
    await digestUrl(url);
    expect(Date.now() - started).toBeGreaterThanOrEqual(250);
  });

  it('adds the digested card to the store (visible via listCards)', async () => {
    const card = await digestUrl(url);
    const cards = await listCards();
    expect(cards).toHaveLength(mockCards.length + 1);
    expect(cards.find((c) => c.id === card.id)?.url).toBe(url);
  });

  it('rejects with ApiError 422 for the fail.example.com hostname', async () => {
    await expectApiError(
      digestUrl('https://fail.example.com/some-article'),
      'Could not extract this article',
      422,
    );
    expect(await listCards()).toHaveLength(mockCards.length);
  });

  it('rejects with ApiError 422 for an unparseable url', async () => {
    await expectApiError(digestUrl('not a url'), 'Could not extract this article', 422);
  });
});

describe('deleteCard', () => {
  it('removes exactly the card with the given id', async () => {
    const victim = mockCards[0]!;
    await deleteCard(victim.id);
    const cards = await listCards();
    expect(cards).toHaveLength(mockCards.length - 1);
    expect(cards.some((c) => c.id === victim.id)).toBe(false);
  });

  it('rejects with ApiError 404 for an unknown id and leaves the store unchanged', async () => {
    await expectApiError(deleteCard('no-such-id'), 'Card not found', 404);
    expect(await listCards()).toHaveLength(mockCards.length);
  });
});

describe('translateCard (feature 017, issue #16)', () => {
  it('replaces the card language and returns the updated card', async () => {
    const victim = mockCards[0]!;
    expect(victim.language).toBe('uk');

    const updated = await translateCard(victim.id, 'en');

    expect(updated.id).toBe(victim.id);
    expect(updated.language).toBe('en');
    // Mock stand-in for real translation: summary visibly changes.
    expect(updated.summary).toBe(`[en] ${victim.summary}`);
    // Everything else survives untouched.
    expect(updated.url).toBe(victim.url);
    expect(updated.keyPoints).toEqual(victim.keyPoints);
    expect(updated.tags).toEqual(victim.tags);
    expect(updated.category).toBe(victim.category);
    expect(Object.keys(updated).sort()).toEqual([...CARD_KEYS]);
  });

  it('persists the translated card in the store (visible via listCards)', async () => {
    const victim = mockCards[1]!;
    await translateCard(victim.id, 'ru');
    const cards = await listCards();
    expect(cards).toHaveLength(mockCards.length);
    expect(cards.find((c) => c.id === victim.id)?.language).toBe('ru');
  });

  it('rejects with ApiError 404 for an unknown id and leaves the store unchanged', async () => {
    await expectApiError(translateCard('no-such-id', 'en'), 'Card not found', 404);
    const cards = await listCards();
    expect(cards.every((c) => c.language === 'uk')).toBe(true);
  });
});

describe('findSimilar', () => {
  it('returns up to 3 other cards as {id, reason} refs', async () => {
    const target = mockCards[0]!;
    const refs = await findSimilar(target.id);
    expect(refs.length).toBeLessThanOrEqual(3);
    expect(refs.every((r) => r.id !== target.id)).toBe(true);
    expect(refs.every((r) => typeof r.reason === 'string' && r.reason.length > 0)).toBe(true);
    const ids = new Set(mockCards.map((c) => c.id));
    expect(refs.every((r) => ids.has(r.id))).toBe(true);
  });

  it('rejects with ApiError 404 for an unknown id', async () => {
    await expectApiError(findSimilar('no-such-id'), 'Card not found', 404);
  });
});

describe('resetApiMock', () => {
  it('reseeds the store to the original mock cards', async () => {
    await deleteCard(mockCards[0]!.id);
    resetApiMock();
    expect(await listCards()).toHaveLength(mockCards.length);
  });
});

// Compile-time check that the exported signatures match the contract.
const _digest: (url: string) => Promise<Card> = digestUrl;
const _list: () => Promise<Card[]> = listCards;
const _del: (id: string) => Promise<void> = deleteCard;
const _translate: (id: string, language: Language) => Promise<Card> = translateCard;
const _similar: (id: string) => Promise<SimilarRef[]> = findSimilar;
void _digest;
void _list;
void _del;
void _translate;
void _similar;
