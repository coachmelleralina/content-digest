// Pure board-grouping module (feature 003, issue #1).
// Files cards into sections by category, reusing resolveCategory (feature 002)
// so near-duplicate labels ("startups"/"Startup", "AI"/"Artificial Intelligence")
// land in a single section named after the first-seen label.

import type { Card, Section } from '../types';
import { resolveCategory } from './categories';

/**
 * Groups cards into board sections. Sections are sorted alphabetically by
 * category (case-insensitive); cards within a section are newest-first by
 * `createdAt`. Pure: never mutates the input.
 */
export const groupByCategory = (cards: Card[]): Section[] => {
  const byLabel = new Map<string, Card[]>();

  for (const card of cards) {
    const label = resolveCategory(card.category, [...byLabel.keys()]);
    const bucket = byLabel.get(label);
    if (bucket === undefined) {
      byLabel.set(label, [card]);
    } else {
      bucket.push(card);
    }
  }

  return [...byLabel.entries()]
    .map(([category, sectionCards]) => ({
      category,
      cards: [...sectionCards].sort((a, b) => Date.parse(b.createdAt) - Date.parse(a.createdAt)),
    }))
    .sort((a, b) => a.category.localeCompare(b.category, undefined, { sensitivity: 'base' }));
};
