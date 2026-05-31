import {useState} from 'react';



function App() {
  const [query, setQuery] = useState('');
  const isTooShort = query.length > 0 && query.length < 3;

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
      {query.length >= 3 && (
        <p>Searching for: <strong>{query}</strong></p>
      )}
    </div>
  );
}

export default App;