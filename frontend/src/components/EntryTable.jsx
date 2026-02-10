export default function EntryTable({ entries }) {
  if (entries.length === 0) {
    return <p>No entries yet.</p>;
  }

  // Consolidate entries with same timestamp+description+currency
  const consolidated = [];
  const groupMap = new Map();
  for (const entry of entries) {
    const key = `${entry.effective_time}|${entry.description}|${entry.currency}`;
    if (!groupMap.has(key)) {
      groupMap.set(key, { ...entry, amount: 0 });
      consolidated.push(groupMap.get(key));
    }
    groupMap.get(key).amount += entry.amount;
  }
  const filtered = consolidated.filter(e => Math.abs(e.amount) > 1e-9);

  let runningTotal = 0;

  return (
    <table>
      <thead>
        <tr>
          <th>Effective Time</th>
          <th>Description</th>
          <th>Currency</th>
          <th style={{ textAlign: 'right' }}>Amount</th>
          <th style={{ textAlign: 'right' }}>Running Total</th>
        </tr>
      </thead>
      <tbody>
        {filtered.map((entry, i) => {
          runningTotal += entry.amount;
          return (
            <tr key={i}>
              <td>{new Date(entry.effective_time).toLocaleString()}</td>
              <td>{entry.description || '\u2014'}</td>
              <td>{entry.currency}</td>
              <td className="number">{entry.amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
              <td className="number">{runningTotal.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
