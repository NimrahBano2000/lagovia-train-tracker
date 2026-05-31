import {useState, useEffect} from 'react';


const API_BASE = 'http://localhost:8000';
function App() {
  const [query, setQuery] = useState('');
  const [departures, setDepartures] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const isTooShort = query.length > 0 && query.length < 3;
  useEffect(() => {
    if (query.length < 3) {
      setDepartures([]);
      setError(null);
      return;
    }

    const timer = setTimeout(() => {
      setLoading(true);
      setError(null);

      fetch(`${API_BASE}/departures?q=${encodeURIComponent(query)}`)
        .then(async (response) => {
          const body = await response.json();
          if (!response.ok) {
            throw new Error(
              body?.detail?.message || `Request failed (${response.status})`
            );
          }
          return body;
        })
        .then((data) => {
          setDepartures(data.departures);
          setLoading(false);
        })
        .catch((err) => {
          setError(err.message);
          setLoading(false);
        });
    }, 300);

    return () => clearTimeout(timer);
  }, [query]);

  return (
    <div className="container">
      <h1>Lagovia Train Tracker</h1>
      <p>Search for a station to see upcoming departures.</p>
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Type at least 3 characters..."
      />
      {isTooShort && <p>Keep typing — need at least 3 characters.</p>}

      {loading && <p>Loading…</p>}

      {error && <p style={{ color: 'red' }}>Error: {error}</p>}

      {!loading && !error && query.length >= 3 && (
        <p>Found <strong>{departures.length}</strong> departures.</p>
      )}
    </div>
  );
}

export default App;