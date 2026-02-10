import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getMetadata, updateMetadata, listAccounts, createAccount, deleteAccount, listActivity, listFundingRules, createFundingRule } from '../api';
import AccountForm from '../components/AccountForm';
import FundingForm from '../components/FundingForm';
import ActivityTimeline from '../components/ActivityTimeline';

export default function SimulationDetail() {
  const { simName } = useParams();
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [accounts, setAccounts] = useState([]);
  const [activity, setActivity] = useState([]);
  const [rules, setRules] = useState([]);
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

  async function loadActivity() {
    try {
      const data = await listActivity(simName);
      setActivity(data);
    } catch (e) {
      setError(e.message);
    }
  }

  async function loadRules() {
    try {
      const data = await listFundingRules(simName);
      setRules(data);
    } catch (e) {
      setError(e.message);
    }
  }

  useEffect(() => {
    loadMetadata();
    loadAccounts();
    loadActivity();
    loadRules();
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

  async function handleCreateRule(rule) {
    setError(null);
    try {
      await createFundingRule(simName, rule);
      await loadRules();
      await loadActivity();
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

      <section>
        <h2>Backup Funding Rules</h2>
        {accounts.length >= 2 ? (
          <FundingForm accounts={accounts} onSubmit={handleCreateRule} />
        ) : (
          <p>Create at least 2 accounts to add backup funding rules.</p>
        )}
        {rules.length > 0 && (
          <table>
            <thead>
              <tr>
                <th>Target Account</th>
                <th>Backup Account</th>
                <th>Time of Day (ET)</th>
                <th>Currency</th>
              </tr>
            </thead>
            <tbody>
              {rules.map((rule) => (
                <tr key={rule.id}>
                  <td>{accounts.find((a) => a.id === rule.target_account_id)?.name || rule.target_account_id}</td>
                  <td>{accounts.find((a) => a.id === rule.source_account_id)?.name || rule.source_account_id}</td>
                  <td>{rule.time_of_day}</td>
                  <td>{rule.currency}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      {activity.length > 0 && (
        <section>
          <h2>Activity Timeline</h2>
          <ActivityTimeline entries={activity} />
        </section>
      )}
    </>
  );
}
