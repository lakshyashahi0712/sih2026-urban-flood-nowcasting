import FloodMap from './components/FloodMap';
import './App.css';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>Flood Modeling Dashboard</h1>
        <p>Professional flood visualization for Mumbai region</p>
      </header>
      <main>
        <FloodMap />
      </main>
    </div>
  );
}

export default App;