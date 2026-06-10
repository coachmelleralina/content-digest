import { useEffect, useState } from 'react';
import { greeting } from './greeting';
import { Board } from './components/Board';
import UrlInput from './components/UrlInput';
import { digestUrl, listCards } from './lib/api';
import type { Card } from './types';

export default function App() {
  const [cards, setCards] = useState<Card[]>([]);

  useEffect(() => {
    void listCards().then(setCards);
  }, []);

  const handleDigest = async (url: string) => {
    const card = await digestUrl(url);
    setCards((prev) => [...prev, card]);
  };

  return (
    <main style={{ fontFamily: 'system-ui', padding: '2rem 0' }}>
      <h1>{greeting('content-digest')}</h1>
      <p>Paste an article link and get an AI summary, key points, tags, and a topic board.</p>
      <UrlInput onSubmit={handleDigest} />
      <Board cards={cards} />
    </main>
  );
}
