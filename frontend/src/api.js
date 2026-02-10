const BASE = '/simulations';

async function request(url, options = {}) {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.error || `Request failed: ${res.status}`);
  }
  if (res.status === 204) return null;
  return res.json();
}

export function listSimulations() {
  return request(BASE);
}

export function createSimulation(name, startDate, endDate) {
  return request(BASE, {
    method: 'POST',
    body: JSON.stringify({
      name,
      start_date: startDate || null,
      end_date: endDate || null,
    }),
  });
}

export function deleteSimulation(name) {
  return request(`${BASE}/${name}`, { method: 'DELETE' });
}

export function getMetadata(simName) {
  return request(`${BASE}/${simName}/metadata`);
}

export function updateMetadata(simName, startDate, endDate) {
  return request(`${BASE}/${simName}/metadata`, {
    method: 'PATCH',
    body: JSON.stringify({
      start_date: startDate || null,
      end_date: endDate || null,
    }),
  });
}

export function listAccounts(simName) {
  return request(`${BASE}/${simName}/accounts`);
}

export function createAccount(simName, name) {
  return request(`${BASE}/${simName}/accounts`, {
    method: 'POST',
    body: JSON.stringify({ name }),
  });
}

export function deleteAccount(simName, accountId) {
  return request(`${BASE}/${simName}/accounts/${accountId}`, {
    method: 'DELETE',
  });
}

export function listActivity(simName) {
  return request(`${BASE}/${simName}/activity`);
}

export function listEntries(simName, accountId) {
  return request(`${BASE}/${simName}/accounts/${accountId}/entries`);
}

export function createEntry(simName, accountId, entry) {
  return request(`${BASE}/${simName}/accounts/${accountId}/entries`, {
    method: 'POST',
    body: JSON.stringify(entry),
  });
}
