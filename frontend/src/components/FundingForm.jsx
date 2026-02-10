import { useState } from 'react';

export default function FundingForm({ accounts, onSubmit }) {
  const [ruleType, setRuleType] = useState('BACKUP_FUNDING');
  const [targetAccountId, setTargetAccountId] = useState('');
  const [sourceAccountId, setSourceAccountId] = useState('');
  const [timeOfDay, setTimeOfDay] = useState('');
  const [currency, setCurrency] = useState('USD');
  const [threshold, setThreshold] = useState('');
  const [targetAmount, setTargetAmount] = useState('');

  function handleSubmit(e) {
    e.preventDefault();
    if (!targetAccountId || !sourceAccountId || !timeOfDay) return;
    if ((ruleType === 'TOPUP' || ruleType === 'SWEEP_OUT') && (!threshold || !targetAmount)) return;
    const rule = {
      rule_type: ruleType,
      target_account_id: parseInt(targetAccountId),
      source_account_id: parseInt(sourceAccountId),
      time_of_day: timeOfDay.length === 5 ? timeOfDay + ':00' : timeOfDay,
      currency,
    };
    if (ruleType === 'TOPUP' || ruleType === 'SWEEP_OUT') {
      rule.threshold = parseFloat(threshold);
      rule.target_amount = parseFloat(targetAmount);
    }
    onSubmit(rule);
    setRuleType('BACKUP_FUNDING');
    setTargetAccountId('');
    setSourceAccountId('');
    setTimeOfDay('');
    setCurrency('USD');
    setThreshold('');
    setTargetAmount('');
  }

  return (
    <form onSubmit={handleSubmit}>
      <div className="field">
        <label>Rule Type</label>
        <select value={ruleType} onChange={(e) => setRuleType(e.target.value)} required>
          <option value="BACKUP_FUNDING">Backup Funding</option>
          <option value="TOPUP">Topup</option>
          <option value="SWEEP_OUT">Sweep Out</option>
        </select>
      </div>
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
        <label>Source Account</label>
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
      {(ruleType === 'TOPUP' || ruleType === 'SWEEP_OUT') && (
        <>
          <div className="field">
            <label>Threshold</label>
            <input type="number" step="any" value={threshold} onChange={(e) => setThreshold(e.target.value)} required />
          </div>
          <div className="field">
            <label>Target Amount</label>
            <input type="number" step="any" value={targetAmount} onChange={(e) => setTargetAmount(e.target.value)} required />
          </div>
        </>
      )}
      <button type="submit">Add Rule</button>
    </form>
  );
}
