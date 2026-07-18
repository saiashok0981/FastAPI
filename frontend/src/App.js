import { useEffect, useState } from 'react';

function App() {
  const [healthData, setHealthData] = useState(null);

  useEffect(() => {
    fetch('http://localhost:8000/health')
      .then(response => response.json())
      .then(data => setHealthData(data))
      .catch(error => console.error("Error fetching data:", error));
  }, []);

  return (
    <div>
      <h1>React Connected to FastAPI</h1>
      {healthData ? (
        <p>Database Status: {healthData.database}</p>
      ) : (
        <p>Loading...</p>
      )}
    </div>
  );
}

export default App;