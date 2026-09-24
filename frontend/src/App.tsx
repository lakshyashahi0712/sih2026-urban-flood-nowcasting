import { useState } from 'react';
import FloodMap from './components/FloodMap';
import DelhiApp from './components/delhi/DelhiApp';
import { getInitialMapTheme, type MapTheme } from './config/mapStyles';
import './App.css';

type CityMode = 'DELHI_V2' | 'MUMBAI_V1';

function App() {
  const [mode, setMode] = useState<CityMode>(() => {
    if (typeof window !== 'undefined' && window.location.search.toLowerCase().includes('mumbai')) {
      return 'MUMBAI_V1';
    }
    return 'DELHI_V2';
  });

  const [theme, setTheme] = useState<MapTheme>(() => getInitialMapTheme());

  const handleThemeChange = (newTheme: MapTheme) => {
    if (newTheme === theme) return;
    setTheme(newTheme);
    if (typeof window !== 'undefined') {
      const url = new URL(window.location.href);
      url.searchParams.set('theme', newTheme.toLowerCase());
      window.history.replaceState({}, '', url.toString());
    }
  };

  return (
    <div className="app-root">
      <div className="app-floating-controls">
        <div className="city-switch" role="tablist" aria-label="System version">
          <button
            role="tab"
            aria-selected={mode === 'DELHI_V2'}
            aria-label="Switch to Delhi V2 operational surface"
            className={`city-btn ${mode === 'DELHI_V2' ? 'active' : ''}`}
            onClick={() => setMode('DELHI_V2')}
          >
            DELHI V2
            <span className="city-tag">CURRENT</span>
          </button>
          <button
            role="tab"
            aria-selected={mode === 'MUMBAI_V1'}
            aria-label="Switch to Mumbai V1 pilot surface"
            className={`city-btn ${mode === 'MUMBAI_V1' ? 'active' : ''}`}
            onClick={() => setMode('MUMBAI_V1')}
          >
            MUMBAI V1
            <span className="city-tag legacy">LEGACY</span>
          </button>
        </div>

        <div className="theme-switch" role="radiogroup" aria-label="Map style selector">
          <button
            type="button"
            role="radio"
            aria-checked={theme === 'LIGHT'}
            aria-label="Light map style"
            className={`theme-btn ${theme === 'LIGHT' ? 'active' : ''}`}
            onClick={() => handleThemeChange('LIGHT')}
          >
            <span className="theme-icon" aria-hidden="true">☀</span>
            LIGHT
          </button>
          <button
            type="button"
            role="radio"
            aria-checked={theme === 'DARK'}
            aria-label="Dark map style"
            className={`theme-btn ${theme === 'DARK' ? 'active' : ''}`}
            onClick={() => handleThemeChange('DARK')}
          >
            <span className="theme-icon" aria-hidden="true">◐</span>
            DARK
          </button>
        </div>
      </div>
      {mode === 'DELHI_V2' ? <DelhiApp theme={theme} /> : <FloodMap theme={theme} />}
    </div>
  );
}

export default App;
