import { greeting } from './greeting';

export default function App() {
  return (
    <main style={{ fontFamily: 'system-ui', padding: '2rem' }}>
      <h1>{greeting('content-digest')}</h1>
      <p>Paste an article link and get an AI summary, key points, tags, and a topic board.</p>
    </main>
  );
}
