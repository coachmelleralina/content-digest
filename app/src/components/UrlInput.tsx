// UrlInput (feature 006, issue #3) — render-only. All decision logic lives in
// lib/validateUrl; the onSubmit callback (lib/api.ts, issue #4) is injected by App.
import { useState, type FormEvent } from 'react';
import { toErrorMessage, validateUrl } from '../lib/validateUrl';

type UrlInputProps = {
  onSubmit: (url: string) => Promise<void>;
};

export default function UrlInput({ onSubmit }: UrlInputProps) {
  const [value, setValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const result = validateUrl(value);
    if (!result.ok) {
      setError(result.reason);
      return;
    }
    setError(null);
    setLoading(true);
    try {
      await onSubmit(result.url);
      setValue('');
    } catch (err) {
      setError(toErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <form
      onSubmit={(event) => void handleSubmit(event)}
      style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', maxWidth: '40rem' }}
    >
      <input
        type="text"
        value={value}
        onChange={(event) => setValue(event.target.value)}
        placeholder="Paste an article link…"
        aria-label="Article URL"
        disabled={loading}
        style={{
          flex: '1 1 16rem',
          padding: '0.5rem 0.75rem',
          fontSize: '1rem',
          fontFamily: 'inherit',
          border: '1px solid #c4c4c4',
          borderRadius: '0.375rem',
        }}
      />
      <button
        type="submit"
        disabled={loading}
        style={{
          padding: '0.5rem 1rem',
          fontSize: '1rem',
          fontFamily: 'inherit',
          border: '1px solid transparent',
          borderRadius: '0.375rem',
          background: loading ? '#9aa7b8' : '#2f6fed',
          color: '#fff',
          cursor: loading ? 'default' : 'pointer',
        }}
      >
        {loading ? 'Digesting…' : 'Digest'}
      </button>
      {error !== null && (
        <p
          role="alert"
          style={{ flexBasis: '100%', margin: 0, fontSize: '0.875rem', color: '#b3261e' }}
        >
          {error}
        </p>
      )}
    </form>
  );
}
