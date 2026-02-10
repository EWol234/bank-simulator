import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { listEntries, createEntry } from '../api';
import EntryForm from '../components/EntryForm';
import EntryTable from '../components/EntryTable';

export default function AccountLedger() {
  const { simName, accountId } = useParams();
  const [entries, setEntries] = useState([]);
  const [error, setError] = useState(null);

  async function load() {
    try {
      const data = await listEntries(simName, accountId);
      setEntries(data);
    } catch (e) {
      setError(e.message);
    }
  }

  useEffect(() => { load(); }, [simName, accountId]);

  async function handleCreate(entry) {
    setError(null);
    try {
      const updatedEntries = await createEntry(simName, accountId, entry);
      setEntries(updatedEntries);
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <>
      <div className="breadcrumb">
        <Link to="/">Simulations</Link> / <Link to={`/${simName}`}>{simName}</Link> / Account {accountId}
      </div>
      <h1>Account {accountId} Ledger</h1>
      {error && <div className="error">{error}</div>}
      <EntryTable entries={entries} />
      <h2>New Entry</h2>
      <EntryForm onSubmit={handleCreate} />
    </>
  );
}
