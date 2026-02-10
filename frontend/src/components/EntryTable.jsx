export default function EntryTable({ entries }) {
  if (entries.length === 0) {
    return <p>No entries yet.</p>;
  }

  let runningTotal = 0;

  return (
    <table>
      <thead>
        <tr>
          <th>ID</th>
          <th>Effective Time</th>
          <th>Description</th>
          <th>Currency</th>
          <th style={{ textAlign: 'right' }}>Amount</th>
          <th style={{ textAlign: 'right' }}>Running Total</th>
        </tr>
      </thead>
      <tbody>
        {entries.map((entry) => {
          runningTotal += entry.amount;
          return (
            <tr key={entry.id}>
              <td>{entry.id}</td>
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
