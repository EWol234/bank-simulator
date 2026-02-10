import { BrowserRouter, Routes, Route } from 'react-router-dom';
import SimulationList from './pages/SimulationList';
import SimulationDetail from './pages/SimulationDetail';
import AccountLedger from './pages/AccountLedger';
import './App.css';

function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <Routes>
          <Route path="/" element={<SimulationList />} />
          <Route path="/:simName" element={<SimulationDetail />} />
          <Route path="/:simName/:accountId" element={<AccountLedger />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
