// Spec for feature 019 — resolveSimilar: refs → display matches.

import { describe, it, expect } from 'vitest';
import { resolveSimilar } from './resolveSimilar';
import type { Card, SimilarRef } from '../types';

const card = (id: string, title: string): Card => ({
  id,
  url: `https://example.com/${id}`,
  title,
  summary: 's',
  keyPoints: [],
  tags: [],
  category: 'C',
  language: 'uk',
  createdAt: '2026-06-11T10:00:00+00:00',
});

const cards = [card('a', 'Alpha'), card('b', 'Beta'), card('c', 'Gamma')];

describe('resolveSimilar', () => {
  it('maps each ref to {id, title, reason} using the cards list', () => {
    const refs: SimilarRef[] = [{ id: 'b', reason: 'related to b' }];
    expect(resolveSimilar(refs, cards)).toEqual([{ id: 'b', title: 'Beta', reason: 'related to b' }]);
  });

  it('preserves ref order', () => {
    const refs: SimilarRef[] = [
      { id: 'c', reason: 'r1' },
      { id: 'a', reason: 'r2' },
    ];
    expect(resolveSimilar(refs, cards).map((m) => m.id)).toEqual(['c', 'a']);
  });

  it('drops refs whose id is not on the board (defensive — server already filters)', () => {
    const refs: SimilarRef[] = [
      { id: 'a', reason: 'ok' },
      { id: 'gone', reason: 'stale' },
    ];
    expect(resolveSimilar(refs, cards).map((m) => m.id)).toEqual(['a']);
  });

  it('returns an empty array for no refs', () => {
    expect(resolveSimilar([], cards)).toEqual([]);
  });
});
