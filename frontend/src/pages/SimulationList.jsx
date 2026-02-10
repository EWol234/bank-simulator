import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { listSimulations, createSimulation, deleteSimulation, seedDemoData } from '../api';
import SimulationForm from '../components/SimulationForm';

export default function SimulationList() {
  const [simulations, setSimulations] = useState([]);
  const [error, setError] = useState(null);

  async function load() {
    try {
      const data = await listSimulations();
      setSimulations(data.simulations);
    } catch (e) {
      setError(e.message);
    }
  }

  useEffect(() => { load(); }, []);

  async function handleCreate(name, startDate, endDate) {
    setError(null);
    try {
      await createSimulation(name, startDate, endDate);
      await load();
    } catch (e) {
      setError(e.message);
    }
  }

  async function handleSeedDemo() {
    setError(null);
    try {
      await seedDemoData('demo');
      await load();
    } catch (e) {
      setError(e.message);
    }
  }

  async function handleDelete(name) {
    setError(null);
    try {
      await deleteSimulation(name);
      await load();
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <>
      <h1>Simulations</h1>
      {error && <div className="error">{error}</div>}
      <SimulationForm onSubmit={handleCreate} />
      <button onClick={handleSeedDemo} style={{ marginBottom: '1rem' }}>Seed Demo</button>
      <ul>
        {simulations.map((name) => (
          <li key={name}>
            <Link to={`/${name}`}>{name}</Link>
            <button className="danger" onClick={() => handleDelete(name)}>Delete</button>
          </li>
        ))}
        {simulations.length === 0 && <li>No simulations yet.</li>}
      </ul>
    </>
  );
}
