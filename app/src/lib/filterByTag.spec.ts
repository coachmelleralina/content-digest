// Spec for feature 016 (issue #15) — pure tag filtering for the board.

import { describe, it, expect } from 'vitest';
import type { Card } from '../types';
import { filterByTag, isSameTag } from './filterByTag';

const card = (id: string, tags: string[]): Card => ({
  id,
  url: `https://example.com/${id}`,
  title: `Title ${id}`,
  summary: `Summary ${id}`,
  keyPoints: [{ takeaway: 'a point', quote: null }],
  tags,
  category: 'AI',
  language: 'uk',
  createdAt: '2026-06-01T10:00:00Z',
});

describe('filterByTag', () => {
  const cards = [
    card('1', ['ai-agents', 'strategy']),
    card('2', ['research', 'AI-Agents']),
    card('3', ['fitness', 'training']),
  ];

  it('returns all cards for a null tag (no active filter)', () => {
    expect(filterByTag(cards, null)).toEqual(cards);
  });

  it('keeps only cards whose tags contain the given tag', () => {
    expect(filterByTag(cards, 'strategy').map((c) => c.id)).toEqual(['1']);
  });

  it('matches case-insensitively', () => {
    expect(filterByTag(cards, 'ai-agents').map((c) => c.id)).toEqual(['1', '2']);
    expect(filterByTag(cards, 'AI-AGENTS').map((c) => c.id)).toEqual(['1', '2']);
  });

  it('returns [] when no card has the tag', () => {
    expect(filterByTag(cards, 'no-such-tag')).toEqual([]);
  });

  it('does not mutate the input array', () => {
    const snapshot = structuredClone(cards);
    filterByTag(cards, 'fitness');
    expect(cards).toEqual(snapshot);
  });
});

describe('isSameTag', () => {
  it('compares tags case-insensitively', () => {
    expect(isSameTag('ai-agents', 'AI-Agents')).toBe(true);
    expect(isSameTag('strategy', 'strategy')).toBe(true);
    expect(isSameTag('strategy', 'research')).toBe(false);
  });

  it('never matches a null active tag', () => {
    expect(isSameTag('strategy', null)).toBe(false);
  });
});
