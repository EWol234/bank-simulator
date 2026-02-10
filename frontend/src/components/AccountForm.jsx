import { useState } from 'react';

export default function AccountForm({ onSubmit }) {
  const [name, setName] = useState('');

  function handleSubmit(e) {
    e.preventDefault();
    if (!name.trim()) return;
    onSubmit(name.trim());
    setName('');
  }

  return (
    <form onSubmit={handleSubmit}>
      <div className="field">
        <label>Account Name</label>
        <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Account name" required />
      </div>
      <button type="submit">Add Account</button>
    </form>
  );
}
