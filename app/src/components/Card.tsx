// Render-only card component (feature 005, issue #2; feature 016, issue #15;
// feature 017, issue #16). Pure presentation of one Card — no branching or
// data transforms here: tag-state logic lives in lib/filterByTag, deep links
// in lib/fragmentUrl, languages in lib/languages.

import type { CSSProperties } from 'react';
import type { Card as CardModel, SimilarUiProps } from '../types';
import { isSameTag } from '../lib/filterByTag';
import { takeawayHref } from '../lib/fragmentUrl';
import { SUPPORTED_LANGUAGES, languageLabel, type Language } from '../lib/languages';
import { cardElementId } from '../lib/cardDom';

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

// Subtle but visible: a takeaway with a grounding quote is clickable and
// jumps to the exact passage in the article (text-fragment deep link).
const takeawayLink: CSSProperties = {
  color: 'inherit',
  textDecoration: 'underline',
  textDecorationStyle: 'dotted',
  textDecorationColor: 'var(--accent, #6b21a8)',
  textUnderlineOffset: '0.2em',
};

const tagsRow: CSSProperties = {
  display: 'flex',
  flexWrap: 'wrap',
  gap: '0.4rem',
  marginTop: '0.75rem',
};

const tagButton: CSSProperties = {
  fontSize: '0.75rem',
  fontFamily: 'inherit',
  color: 'inherit',
  background: 'var(--code-bg, #f4f4f5)',
  border: '1px solid var(--border, #ddd)',
  borderRadius: '999px',
  padding: '0.1rem 0.55rem',
  cursor: 'pointer',
};

const tagButtonActive: CSSProperties = {
  ...tagButton,
  fontWeight: 600,
  color: 'var(--accent, #6b21a8)',
  background: 'var(--accent-bg, #f3e8ff)',
  border: '1px solid var(--accent-border, #c4b5fd)',
};

// Per-card UA|RU|EN switcher (feature 017): compact chips next to the
// category badge; the current language gets the active-tag-chip treatment.
const langGroup: CSSProperties = {
  display: 'inline-flex',
  alignItems: 'baseline',
  gap: '0.2rem',
  marginLeft: '0.75rem',
};

const langButton: CSSProperties = {
  fontSize: '0.7rem',
  fontFamily: 'inherit',
  color: 'inherit',
  background: 'var(--code-bg, #f4f4f5)',
  border: '1px solid var(--border, #ddd)',
  borderRadius: '999px',
  padding: '0.1rem 0.45rem',
  cursor: 'pointer',
};

const langButtonActive: CSSProperties = {
  ...langButton,
  fontWeight: 600,
  color: 'var(--accent, #6b21a8)',
  background: 'var(--accent-bg, #f3e8ff)',
  border: '1px solid var(--accent-border, #c4b5fd)',
  cursor: 'default',
};

const langBusyHint: CSSProperties = {
  fontSize: '0.7rem',
  opacity: 0.6,
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

// Feature 019: "Похожие" button + inline results list.
const similarButton: CSSProperties = {
  fontSize: '0.75rem',
  fontFamily: 'inherit',
  color: 'inherit',
  border: '1px solid var(--border, #ddd)',
  background: 'transparent',
  borderRadius: '6px',
  padding: '0.1rem 0.5rem',
  cursor: 'pointer',
  marginLeft: '0.5rem',
  whiteSpace: 'nowrap',
};

const similarBlock: CSSProperties = {
  marginTop: '0.75rem',
  paddingTop: '0.6rem',
  borderTop: '1px dashed var(--border, #ddd)',
  fontSize: '0.82rem',
};

const similarItem: CSSProperties = {
  display: 'block',
  width: '100%',
  textAlign: 'left',
  fontFamily: 'inherit',
  fontSize: 'inherit',
  color: 'inherit',
  background: 'transparent',
  border: 'none',
  borderRadius: '6px',
  padding: '0.2rem 0.3rem',
  cursor: 'pointer',
};

const similarReason: CSSProperties = { opacity: 0.7 };
const similarEmpty: CSSProperties = { fontStyle: 'italic', opacity: 0.7 };

export function Card({
  card,
  onDelete,
  onTagClick,
  activeTag,
  onTranslate,
  translatingId,
  similar,
}: {
  card: CardModel;
  onDelete: (id: string) => void;
  onTagClick: (tag: string) => void;
  activeTag: string | null;
  onTranslate: (id: string, language: Language) => void;
  translatingId: string | null;
  similar: SimilarUiProps;
}) {
  const isTranslating = translatingId === card.id;
  // Feature 019: this card's slice of the bundled similar-materials state.
  const similarResults = similar.resultsByCard[card.id] ?? null;
  const findingSimilar = similar.findingId === card.id;
  const highlighted = similar.highlightedId === card.id;
  const boxStyle = highlighted
    ? { ...box, outline: '2px solid var(--accent, #6b21a8)', outlineOffset: '2px' }
    : box;
  return (
    <article id={cardElementId(card.id)} style={boxStyle}>
      <header style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between' }}>
        <a href={card.url} target="_blank" rel="noopener noreferrer" style={titleLink}>
          {card.title}
        </a>
        <span style={{ display: 'flex', alignItems: 'baseline' }}>
          <span style={badge}>{card.category}</span>
          <span style={langGroup} aria-label="Перевести карточку">
            {SUPPORTED_LANGUAGES.map((lang) => (
              <button
                type="button"
                key={lang}
                style={lang === card.language ? langButtonActive : langButton}
                // The current language is a no-op (disabled, never calls
                // back); everything is disabled while this card translates.
                disabled={lang === card.language || isTranslating}
                aria-pressed={lang === card.language}
                onClick={() => onTranslate(card.id, lang)}
              >
                {languageLabel(lang)}
              </button>
            ))}
            {isTranslating && <span style={langBusyHint}>…</span>}
          </span>
          <button
            type="button"
            style={similarButton}
            disabled={similar.disabled || findingSimilar}
            title={similar.disabled ? 'Пока не с чем сравнивать' : undefined}
            onClick={() => similar.onFind(card.id)}
          >
            {findingSimilar ? 'Похожие…' : 'Похожие'}
          </button>
          <button type="button" style={deleteButton} onClick={() => onDelete(card.id)}>
            ✕
          </button>
        </span>
      </header>
      <p style={summaryText}>{card.summary}</p>
      <ul style={pointsList}>
        {card.keyPoints.map((point) => {
          const href = takeawayHref(card.url, point.quote);
          return (
            <li key={point.takeaway}>
              {href === null ? (
                point.takeaway
              ) : (
                <a href={href} target="_blank" rel="noopener noreferrer" style={takeawayLink}>
                  {point.takeaway}
                </a>
              )}
            </li>
          );
        })}
      </ul>
      <div style={tagsRow}>
        {card.tags.map((tag) => (
          <button
            type="button"
            key={tag}
            style={isSameTag(tag, activeTag) ? tagButtonActive : tagButton}
            onClick={() => onTagClick(tag)}
          >
            {tag}
          </button>
        ))}
      </div>
      {similarResults !== null && (
        <div style={similarBlock}>
          {similarResults.length === 0 ? (
            <span style={similarEmpty}>На доске пока нет похожих материалов</span>
          ) : (
            similarResults.map((match) => (
              <button
                type="button"
                key={match.id}
                style={similarItem}
                onClick={() => similar.onGoTo(match.id)}
              >
                → {match.title} <span style={similarReason}>— {match.reason}</span>
              </button>
            ))
          )}
        </div>
      )}
    </article>
  );
}
