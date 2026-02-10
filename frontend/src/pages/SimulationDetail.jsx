import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getMetadata, updateMetadata, listAccounts, createAccount, deleteAccount } from '../api';
import AccountForm from '../components/AccountForm';

export default function SimulationDetail() {
  const { simName } = useParams();
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [accounts, setAccounts] = useState([]);
  const [error, setError] = useState(null);

  async function loadMetadata() {
    try {
      const data = await getMetadata(simName);
      setStartDate(data.start_date ? data.start_date.slice(0, 10) : '');
      setEndDate(data.end_date ? data.end_date.slice(0, 10) : '');
    } catch (e) {
      setError(e.message);
    }
  }

  async function loadAccounts() {
    try {
      const data = await listAccounts(simName);
      setAccounts(data);
    } catch (e) {
      setError(e.message);
    }
  }

  useEffect(() => {
    loadMetadata();
    loadAccounts();
  }, [simName]);

  async function handleMetadataSave(e) {
    e.preventDefault();
    setError(null);
    try {
      await updateMetadata(simName, startDate, endDate);
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleCreateAccount(name) {
    setError(null);
    try {
      await createAccount(simName, name);
      await loadAccounts();
    } catch (e) {
      setError(e.message);
    }
  }

  async function handleDeleteAccount(id) {
    setError(null);
    try {
      await deleteAccount(simName, id);
      await loadAccounts();
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <>
      <div className="breadcrumb">
        <Link to="/">Simulations</Link> / {simName}
      </div>
      <h1>{simName}</h1>
      {error && <div className="error">{error}</div>}

      <section>
        <h2>Date Range</h2>
        <form className="metadata-form" onSubmit={handleMetadataSave}>
          <div className="field">
            <label>Start Date</label>
            <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
          </div>
          <div className="field">
            <label>End Date</label>
            <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
          </div>
          <button type="submit">Save</button>
        </form>
      </section>

      <section>
        <h2>Accounts</h2>
        <AccountForm onSubmit={handleCreateAccount} />
        <ul>
          {accounts.map((acct) => (
            <li key={acct.id}>
              <Link to={`/${simName}/${acct.id}`}>{acct.name}</Link>
              <button className="danger" onClick={() => handleDeleteAccount(acct.id)}>Delete</button>
            </li>
          ))}
          {accounts.length === 0 && <li>No accounts yet.</li>}
        </ul>
      </section>
    </>
  );
}
