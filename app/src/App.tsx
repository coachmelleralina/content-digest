import { useEffect, useState } from 'react';
import { greeting } from './greeting';
import { Board } from './components/Board';
import UrlInput from './components/UrlInput';
import { deleteCard, digestUrl, listCards } from './lib/api';
import { toErrorMessage } from './lib/validateUrl';
import type { Card } from './types';

export default function App() {
  const [cards, setCards] = useState<Card[]>([]);
  const [boardError, setBoardError] = useState<string | null>(null);

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

  return (
    <main style={{ fontFamily: 'system-ui', padding: '2rem 0' }}>
      <h1>{greeting('content-digest')}</h1>
      <p>Paste an article link and get an AI summary, key points, tags, and a topic board.</p>
      <UrlInput onSubmit={handleDigest} />
      {boardError !== null && (
        <p style={{ color: 'var(--danger, #b91c1c)', fontSize: '0.85rem' }}>{boardError}</p>
      )}
      <Board cards={cards} onDelete={handleDelete} />
    </main>
  );
}
