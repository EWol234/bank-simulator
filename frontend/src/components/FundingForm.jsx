import { useState } from 'react';

export default function FundingForm({ accounts, onSubmit }) {
  const [targetAccountId, setTargetAccountId] = useState('');
  const [sourceAccountId, setSourceAccountId] = useState('');
  const [timeOfDay, setTimeOfDay] = useState('');
  const [currency, setCurrency] = useState('USD');

  function handleSubmit(e) {
    e.preventDefault();
    if (!targetAccountId || !sourceAccountId || !timeOfDay) return;
    onSubmit({
      target_account_id: parseInt(targetAccountId),
      source_account_id: parseInt(sourceAccountId),
      time_of_day: timeOfDay.length === 5 ? timeOfDay + ':00' : timeOfDay,
      currency,
    });
    setTargetAccountId('');
    setSourceAccountId('');
    setTimeOfDay('');
    setCurrency('USD');
  }

  return (
    <form onSubmit={handleSubmit}>
      <div className="field">
        <label>Target Account</label>
        <select value={targetAccountId} onChange={(e) => setTargetAccountId(e.target.value)} required>
          <option value="">Select account...</option>
          {accounts.map((a) => (
            <option key={a.id} value={a.id}>{a.name}</option>
          ))}
        </select>
      </div>
      <div className="field">
        <label>Backup Account</label>
        <select value={sourceAccountId} onChange={(e) => setSourceAccountId(e.target.value)} required>
          <option value="">Select account...</option>
          {accounts.filter((a) => String(a.id) !== targetAccountId).map((a) => (
            <option key={a.id} value={a.id}>{a.name}</option>
          ))}
        </select>
      </div>
      <div className="field">
        <label>Time of Day (ET)</label>
        <input type="time" value={timeOfDay} onChange={(e) => setTimeOfDay(e.target.value)} required />
      </div>
      <div className="field">
        <label>Currency</label>
        <input value={currency} onChange={(e) => setCurrency(e.target.value)} required />
      </div>
      <button type="submit">Add Rule</button>
    </form>
  );
}
