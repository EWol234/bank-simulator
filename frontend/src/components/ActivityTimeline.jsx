import { toNYDateKey, toNYDisplay, toNYTime } from '../dateUtils';

function formatAmount(amount) {
  return amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export default function ActivityTimeline({ entries }) {
  if (!entries || entries.length === 0) return null;

  // Group by NY date, preserving order
  const dayOrder = [];
  const dayMap = new Map();
  for (const entry of entries) {
    const key = toNYDateKey(entry.effective_time);
    if (!dayMap.has(key)) {
      dayMap.set(key, []);
      dayOrder.push(key);
    }
    dayMap.get(key).push(entry);
  }

  // Track running balances across all days
  const runningBalances = new Map();

  // Compute final balances
  const allEntries = [...entries];
  const finalBalances = new Map();
  for (const entry of allEntries) {
    finalBalances.set(entry.account_id, (finalBalances.get(entry.account_id) || 0) + entry.amount);
  }

  // Collect unique accounts for final summary (ordered by account_id)
  const accountNames = new Map();
  for (const entry of entries) {
    if (!accountNames.has(entry.account_id)) {
      accountNames.set(entry.account_id, entry.account_name);
    }
  }
  const sortedAccountIds = [...accountNames.keys()].sort((a, b) => a - b);

  return (
    <div className="activity-timeline">
      {dayOrder.map((dateKey) => {
        const dayEntries = dayMap.get(dateKey);
        const displayDate = toNYDisplay(dayEntries[0].effective_time);

        // Group by account within day (ordered by account_id)
        const accountGroups = new Map();
        for (const entry of dayEntries) {
          if (!accountGroups.has(entry.account_id)) {
            accountGroups.set(entry.account_id, { name: entry.account_name, entries: [] });
          }
          accountGroups.get(entry.account_id).entries.push(entry);
        }
        const sortedAccounts = [...accountGroups.entries()].sort(([a], [b]) => a - b);

        // End-of-day balances for accounts active this day
        const eodBalances = [];

        return (
          <div key={dateKey} className="activity-day">
            <h3 className="day-header">{displayDate}</h3>
            {sortedAccounts.map(([accountId, { name, entries: acctEntries }]) => {
              // Consolidate entries with same timestamp+description+currency
              const consolidated = [];
              const groupMap = new Map();
              for (const entry of acctEntries) {
                const key = `${entry.effective_time}|${entry.description}|${entry.currency}`;
                if (!groupMap.has(key)) {
                  groupMap.set(key, { ...entry, amount: 0 });
                  consolidated.push(groupMap.get(key));
                }
                groupMap.get(key).amount += entry.amount;
              }
              const filtered = consolidated.filter(e => Math.abs(e.amount) > 1e-9);

              const rows = filtered.map((entry) => {
                const prev = runningBalances.get(accountId) || 0;
                const next = prev + entry.amount;
                runningBalances.set(accountId, next);
                return { ...entry, runningTotal: next };
              });
              eodBalances.push({ accountId, name, balance: runningBalances.get(accountId) || 0 });
              if (rows.length === 0) return null;
              return (
                <div key={accountId} className="activity-account">
                  <h4>{name}</h4>
                  <table>
                    <thead>
                      <tr>
                        <th>Time (ET)</th>
                        <th>Description</th>
                        <th>Currency</th>
                        <th className="number">Amount</th>
                        <th className="number">Running Total</th>
                      </tr>
                    </thead>
                    <tbody>
                      {rows.map((row) => (
                        <tr key={row.id}>
                          <td>{toNYTime(row.effective_time)}</td>
                          <td>{row.description}</td>
                          <td>{row.currency}</td>
                          <td className="number">{formatAmount(row.amount)}</td>
                          <td className="number">{formatAmount(row.runningTotal)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              );
            })}
            <div className="eod-balances">
              <strong>End of day:</strong>
              {eodBalances.map(({ accountId, name, balance }) => (
                <span key={accountId} className="eod-item">
                  {name}: {formatAmount(balance)}
                </span>
              ))}
            </div>
          </div>
        );
      })}

      <div className="final-summary">
        <h3>Final Balances</h3>
        <table>
          <thead>
            <tr>
              <th>Account</th>
              <th className="number">Balance</th>
            </tr>
          </thead>
          <tbody>
            {sortedAccountIds.map((id) => (
              <tr key={id}>
                <td>{accountNames.get(id)}</td>
                <td className="number">{formatAmount(finalBalances.get(id))}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
