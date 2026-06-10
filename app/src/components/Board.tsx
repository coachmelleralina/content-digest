// Render-only board component (feature 005, issue #2).
// Grouping/sorting/merging all happens in the pure groupByCategory module
// (feature 003); the only conditional here is the empty state, driven
// directly by that module's output.

import type { CSSProperties } from 'react';
import type { Card as CardModel } from '../types';
import { groupByCategory } from '../lib/groupByCategory';
import { Section } from './Section';

const container: CSSProperties = {
  maxWidth: '720px',
  margin: '0 auto',
  padding: '0 1rem 3rem',
};

const emptyState: CSSProperties = {
  margin: '3rem 0',
  fontStyle: 'italic',
  opacity: 0.7,
};

export function Board({ cards }: { cards: CardModel[] }) {
  const sections = groupByCategory(cards);
  return (
    <div style={container}>
      {sections.length === 0 ? (
        <p style={emptyState}>paste a link to start</p>
      ) : (
        sections.map((section) => <Section key={section.category} section={section} />)
      )}
    </div>
  );
}
