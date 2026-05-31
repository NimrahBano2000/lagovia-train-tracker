import {useState, useEffect} from 'react';


const API_BASE = 'http://localhost:8000';
function App() {

  const [query, setQuery] = useState('');
  const [departures, setDepartures] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const isTooShort = query.length > 0 && query.length < 3;
  const hasSearched = query.length >= 3 && !loading && !error;
  const noResults = hasSearched && departures.length === 0;

  // Group departures by station — derived from state, not stored.
  const grouped = departures.reduce((acc, dep) => {
      if (!acc[dep.station]) acc[dep.station] = [];
      acc[dep.station].push(dep);
      return acc;
  }, {});

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
      <p>Search for a station to see upcoming departures within the next 15 minutes.</p>

      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Type at least 3 characters..."
      />

      {isTooShort && <p>Keep typing — need at least 3 characters.</p>}
      {loading && <p>Loading…</p>}
      {error && <p style={{ color: 'red' }}>Error: {error}</p>}
      {noResults && <p>No departures in the next 15 minutes for "{query}".</p>}

      {hasSearched && departures.length > 0 && (
        <div className="results">
          <p>Found <strong>{departures.length}</strong> departures across <strong>{Object.keys(grouped).length}</strong> stations.</p>

          {Object.entries(grouped).map(([station, deps]) => (
            <section key={station} className="station-group">
              <h2>{station}</h2>
              <table>
                <thead>
                  <tr>
                    <th>Train</th>
                    <th>Destination</th>
                    <th>Scheduled</th>
                    <th>Delay</th>
                    <th>Platform</th>
                  </tr>
                </thead>
                <tbody>
                  {deps.map((d) => (
                    <tr
                      key={`${d.train_number}-${d.scheduled_time_utc}-${d.station}`}
                      style={d.canceled ? { textDecoration: 'line-through', opacity: 0.6 } : undefined}
                    >
                      <td>{d.train_number}</td>
                      <td>{d.destination}</td>
                      <td>{d.scheduled_time_local}</td>
                      <td>
                        {d.delay_minutes > 0
                          ? <span style={{ color: 'orange' }}>+{d.delay_minutes} min</span>
                          : 'on time'}
                      </td>
                      <td>{d.platform || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          ))}
        </div>
      )}
    </div>
  );
}

export default App;