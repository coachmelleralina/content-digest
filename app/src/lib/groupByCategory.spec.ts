import { describe, it, expect } from 'vitest';
import type { Card } from '../types';
import { groupByCategory } from './groupByCategory';
import { mockCards } from '../mocks/cards';

const card = (overrides: Partial<Card> & Pick<Card, 'id' | 'category' | 'createdAt'>): Card => ({
  url: `https://example.com/${overrides.id}`,
  title: `Title ${overrides.id}`,
  summary: `Summary ${overrides.id}`,
  keyPoints: ['a point'],
  tags: ['a-tag'],
  ...overrides,
});

describe('groupByCategory', () => {
  it('returns [] for no cards', () => {
    expect(groupByCategory([])).toEqual([]);
  });

  it('groups cards sharing a category into one section', () => {
    const sections = groupByCategory([
      card({ id: '1', category: 'AI', createdAt: '2026-06-01T10:00:00Z' }),
      card({ id: '2', category: 'Health', createdAt: '2026-06-02T10:00:00Z' }),
      card({ id: '3', category: 'AI', createdAt: '2026-06-03T10:00:00Z' }),
    ]);
    expect(sections).toHaveLength(2);
    expect(sections.find((s) => s.category === 'AI')?.cards.map((c) => c.id)).toEqual(['3', '1']);
  });

  it('sorts sections alphabetically by category regardless of input order', () => {
    const sections = groupByCategory([
      card({ id: '1', category: 'Startups', createdAt: '2026-06-01T10:00:00Z' }),
      card({ id: '2', category: 'AI', createdAt: '2026-06-02T10:00:00Z' }),
      card({ id: '3', category: 'Health', createdAt: '2026-06-03T10:00:00Z' }),
    ]);
    expect(sections.map((s) => s.category)).toEqual(['AI', 'Health', 'Startups']);
  });

  it('sorts cards within a section newest-first by createdAt', () => {
    const sections = groupByCategory([
      card({ id: 'old', category: 'AI', createdAt: '2026-05-01T08:00:00Z' }),
      card({ id: 'newest', category: 'AI', createdAt: '2026-06-10T09:30:00Z' }),
      card({ id: 'mid', category: 'AI', createdAt: '2026-05-20T18:00:00Z' }),
    ]);
    expect(sections[0]?.cards.map((c) => c.id)).toEqual(['newest', 'mid', 'old']);
  });

  it('merges near-duplicate category labels into the first-seen section (feature 002 rules)', () => {
    const sections = groupByCategory([
      card({ id: '1', category: 'Startup', createdAt: '2026-06-01T10:00:00Z' }),
      card({ id: '2', category: 'startups', createdAt: '2026-06-02T10:00:00Z' }),
      card({ id: '3', category: 'Artificial Intelligence', createdAt: '2026-06-03T10:00:00Z' }),
      card({ id: '4', category: 'AI', createdAt: '2026-06-04T10:00:00Z' }),
    ]);
    expect(sections.map((s) => s.category)).toEqual(['Artificial Intelligence', 'Startup']);
    expect(sections[0]?.cards.map((c) => c.id)).toEqual(['4', '3']);
    expect(sections[1]?.cards.map((c) => c.id)).toEqual(['2', '1']);
  });

  it('does not mutate the input array or its cards', () => {
    const input = [
      card({ id: 'b', category: 'Health', createdAt: '2026-06-02T10:00:00Z' }),
      card({ id: 'a', category: 'AI', createdAt: '2026-06-01T10:00:00Z' }),
    ];
    const snapshot = structuredClone(input);
    groupByCategory(input);
    expect(input).toEqual(snapshot);
  });
});

describe('mock fixtures', () => {
  it('provides 6-8 fully populated cards', () => {
    expect(mockCards.length).toBeGreaterThanOrEqual(6);
    expect(mockCards.length).toBeLessThanOrEqual(8);
    for (const c of mockCards) {
      expect(c.id).not.toBe('');
      expect(c.url).toMatch(/^https?:\/\//);
      expect(c.title.length).toBeGreaterThan(10);
      expect(c.summary.length).toBeGreaterThan(40);
      expect(c.keyPoints.length).toBeGreaterThanOrEqual(2);
      expect(c.tags.length).toBeGreaterThanOrEqual(2);
      expect(c.category).not.toBe('');
      expect(Number.isNaN(Date.parse(c.createdAt))).toBe(false);
    }
  });

  it('has unique ids and spans at least 3 resolved categories', () => {
    expect(new Set(mockCards.map((c) => c.id)).size).toBe(mockCards.length);
    expect(groupByCategory(mockCards).length).toBeGreaterThanOrEqual(3);
  });
});
