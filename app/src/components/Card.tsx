// Render-only card component (feature 005, issue #2).
// Pure presentation of one Card — no branching or data transforms here.

import type { CSSProperties } from 'react';
import type { Card as CardModel } from '../types';

const box: CSSProperties = {
  border: '1px solid var(--border, #ddd)',
  borderRadius: '10px',
  padding: '1rem 1.25rem',
  marginBottom: '1rem',
  textAlign: 'left',
};

const titleLink: CSSProperties = {
  fontSize: '1.05rem',
  fontWeight: 600,
  textDecoration: 'none',
  color: 'var(--accent, #6b21a8)',
};

const badge: CSSProperties = {
  fontSize: '0.7rem',
  fontWeight: 600,
  textTransform: 'uppercase',
  letterSpacing: '0.05em',
  border: '1px solid var(--accent-border, #c4b5fd)',
  background: 'var(--accent-bg, #f3e8ff)',
  borderRadius: '999px',
  padding: '0.15rem 0.6rem',
  marginLeft: '0.75rem',
  whiteSpace: 'nowrap',
};

const summaryText: CSSProperties = {
  margin: '0.5rem 0 0',
  fontSize: '0.9rem',
  lineHeight: 1.5,
};

const pointsList: CSSProperties = {
  margin: '0.5rem 0 0',
  paddingLeft: '1.25rem',
  fontSize: '0.85rem',
  lineHeight: 1.5,
};

const tagsRow: CSSProperties = {
  display: 'flex',
  flexWrap: 'wrap',
  gap: '0.4rem',
  marginTop: '0.75rem',
};

const tagChip: CSSProperties = {
  fontSize: '0.75rem',
  background: 'var(--code-bg, #f4f4f5)',
  border: '1px solid var(--border, #ddd)',
  borderRadius: '999px',
  padding: '0.1rem 0.55rem',
};

const deleteButton: CSSProperties = {
  fontSize: '0.75rem',
  border: '1px solid var(--border, #ddd)',
  background: 'transparent',
  borderRadius: '6px',
  padding: '0.1rem 0.5rem',
  cursor: 'pointer',
  opacity: 0.6,
  marginLeft: '0.5rem',
  whiteSpace: 'nowrap',
};

export function Card({
  card,
  onDelete,
}: {
  card: CardModel;
  onDelete: (id: string) => void;
}) {
  return (
    <article style={box}>
      <header style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between' }}>
        <a href={card.url} target="_blank" rel="noopener noreferrer" style={titleLink}>
          {card.title}
        </a>
        <span style={{ display: 'flex', alignItems: 'baseline' }}>
          <span style={badge}>{card.category}</span>
          <button type="button" style={deleteButton} onClick={() => onDelete(card.id)}>
            ✕
          </button>
        </span>
      </header>
      <p style={summaryText}>{card.summary}</p>
      <ul style={pointsList}>
        {card.keyPoints.map((point) => (
          <li key={point}>{point}</li>
        ))}
      </ul>
      <div style={tagsRow}>
        {card.tags.map((tag) => (
          <span key={tag} style={tagChip}>
            {tag}
          </span>
        ))}
      </div>
    </article>
  );
}
