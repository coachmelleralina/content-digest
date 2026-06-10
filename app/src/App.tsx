import { greeting } from './greeting';
import { Board } from './components/Board';
import { mockCards } from './mocks/cards';

export default function App() {
  return (
    <main style={{ fontFamily: 'system-ui', padding: '2rem 0' }}>
      <h1>{greeting('content-digest')}</h1>
      <p>Paste an article link and get an AI summary, key points, tags, and a topic board.</p>
      <Board cards={mockCards} />
    </main>
  );
}
