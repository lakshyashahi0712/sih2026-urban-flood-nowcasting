import { useState } from 'react';
import FloodMap from './components/FloodMap';
import DelhiApp from './components/delhi/DelhiApp';
import './App.css';

type CityMode = 'DELHI_V2' | 'MUMBAI_V1';

function App() {
  const [mode, setMode] = useState<CityMode>('DELHI_V2');

  return (
    <div className="app-root">
      <div className="city-switch" role="tablist" aria-label="System version">
        <button
          role="tab"
          aria-selected={mode === 'DELHI_V2'}
          className={`city-btn ${mode === 'DELHI_V2' ? 'active' : ''}`}
          onClick={() => setMode('DELHI_V2')}
        >
          DELHI V2
          <span className="city-tag">CURRENT</span>
        </button>
        <button
          role="tab"
          aria-selected={mode === 'MUMBAI_V1'}
          className={`city-btn ${mode === 'MUMBAI_V1' ? 'active' : ''}`}
          onClick={() => setMode('MUMBAI_V1')}
        >
          MUMBAI V1
          <span className="city-tag legacy">LEGACY</span>
        </button>
      </div>
      {mode === 'DELHI_V2' ? <DelhiApp /> : <FloodMap />}
    </div>
  );
}

export default App;
