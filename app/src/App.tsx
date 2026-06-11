import { useEffect, useState, type CSSProperties } from 'react';
import { greeting } from './greeting';
import { Board } from './components/Board';
import UrlInput from './components/UrlInput';
import { deleteCard, digestUrl, listCards, translateCard } from './lib/api';
import { filterByTag, isSameTag } from './lib/filterByTag';
import type { Language } from './lib/languages';
import { toErrorMessage } from './lib/validateUrl';
import type { Card } from './types';

const filterBar: CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  gap: '0.5rem',
  fontSize: '0.85rem',
  border: '1px solid var(--accent-border, #c4b5fd)',
  background: 'var(--accent-bg, #f3e8ff)',
  borderRadius: '999px',
  padding: '0.25rem 0.5rem 0.25rem 0.85rem',
  margin: '0.75rem 0 0',
};

const clearFilterButton: CSSProperties = {
  fontSize: '0.75rem',
  fontFamily: 'inherit',
  color: 'inherit',
  border: 'none',
  background: 'transparent',
  cursor: 'pointer',
  padding: '0.1rem 0.35rem',
};

export default function App() {
  const [cards, setCards] = useState<Card[]>([]);
  const [boardError, setBoardError] = useState<string | null>(null);
  const [activeTag, setActiveTag] = useState<string | null>(null);
  // Feature 017: id of the card currently being translated (one at a time).
  const [translatingId, setTranslatingId] = useState<string | null>(null);

  useEffect(() => {
    listCards()
      .then((loaded) => {
        setCards(loaded);
        setBoardError(null);
      })
      .catch((error: unknown) => setBoardError(toErrorMessage(error)));
  }, []);

  const handleDigest = async (url: string) => {
    const card = await digestUrl(url);
    setCards((prev) => [...prev, card]);
  };

  const handleDelete = (id: string) => {
    deleteCard(id)
      .then(() => setCards((prev) => prev.filter((card) => card.id !== id)))
      .catch((error: unknown) => setBoardError(toErrorMessage(error)));
  };

  // Translate one card in place: the updated card replaces the old one, so
  // the board regroups naturally if the category came back different.
  const handleTranslate = (id: string, language: Language) => {
    setTranslatingId(id);
    translateCard(id, language)
      .then((updated) => setCards((prev) => prev.map((c) => (c.id === updated.id ? updated : c))))
      .catch((error: unknown) => setBoardError(toErrorMessage(error)))
      .finally(() => setTranslatingId(null));
  };

  // Clicking the already-active tag clears the filter.
  const handleTagClick = (tag: string) => {
    setActiveTag((prev) => (isSameTag(tag, prev) ? null : tag));
  };

  const visibleCards = filterByTag(cards, activeTag);

  return (
    <main style={{ fontFamily: 'system-ui', padding: '2rem 0' }}>
      <h1>{greeting('content-digest')}</h1>
      <p>Paste an article link and get an AI summary, key points, tags, and a topic board.</p>
      <UrlInput onSubmit={handleDigest} />
      {boardError !== null && (
        <p style={{ color: 'var(--danger, #b91c1c)', fontSize: '0.85rem' }}>{boardError}</p>
      )}
      {activeTag !== null && (
        <p style={filterBar}>
          <span>Показано: #{activeTag}</span>
          <button
            type="button"
            style={clearFilterButton}
            onClick={() => setActiveTag(null)}
            aria-label="Сбросить фильтр по тегу"
          >
            ✕
          </button>
        </p>
      )}
      {activeTag !== null && visibleCards.length === 0 ? (
        <p style={{ margin: '3rem 0', fontStyle: 'italic', opacity: 0.7 }}>
          Ничего с тегом #{activeTag} — нажмите ✕, чтобы снова увидеть все карточки.
        </p>
      ) : (
        <Board
          cards={visibleCards}
          onDelete={handleDelete}
          onTagClick={handleTagClick}
          activeTag={activeTag}
          onTranslate={handleTranslate}
          translatingId={translatingId}
        />
      )}
    </main>
  );
}
