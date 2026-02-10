import { useState } from 'react';

export default function EntryForm({ onSubmit }) {
  const [amount, setAmount] = useState('');
  const [currency, setCurrency] = useState('USD');
  const [description, setDescription] = useState('');
  const [effectiveTime, setEffectiveTime] = useState('');

  function handleSubmit(e) {
    e.preventDefault();
    if (!amount || !effectiveTime) return;
    onSubmit({
      amount: parseFloat(amount),
      currency,
      description: description || null,
      effective_time: effectiveTime,
    });
    setAmount('');
    setDescription('');
    setEffectiveTime('');
  }

  return (
    <form onSubmit={handleSubmit}>
      <div className="field">
        <label>Amount</label>
        <input type="number" step="any" value={amount} onChange={(e) => setAmount(e.target.value)} placeholder="0.00" required />
      </div>
      <div className="field">
        <label>Currency</label>
        <input value={currency} onChange={(e) => setCurrency(e.target.value)} required />
      </div>
      <div className="field">
        <label>Description</label>
        <input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Optional" />
      </div>
      <div className="field">
        <label>Effective Time (ET)</label>
        <input type="datetime-local" value={effectiveTime} onChange={(e) => setEffectiveTime(e.target.value)} required />
      </div>
      <button type="submit">Add Entry</button>
    </form>
  );
}
