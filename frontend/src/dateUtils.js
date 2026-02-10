const NY_DATE_FORMAT = new Intl.DateTimeFormat('en-US', {
  timeZone: 'America/New_York',
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
});

const NY_DISPLAY_FORMAT = new Intl.DateTimeFormat('en-US', {
  timeZone: 'America/New_York',
  year: 'numeric',
  month: 'long',
  day: 'numeric',
});

const NY_TIME_FORMAT = new Intl.DateTimeFormat('en-US', {
  timeZone: 'America/New_York',
  hour: '2-digit',
  minute: '2-digit',
  second: '2-digit',
  hour12: true,
});

const NY_DATETIME_FORMAT = new Intl.DateTimeFormat('en-US', {
  timeZone: 'America/New_York',
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
  second: '2-digit',
  hour12: true,
});

export function toNYDateKey(isoString) {
  return NY_DATE_FORMAT.format(new Date(isoString));
}

export function toNYDisplay(isoString) {
  return NY_DISPLAY_FORMAT.format(new Date(isoString));
}

export function toNYTime(isoString) {
  return NY_TIME_FORMAT.format(new Date(isoString));
}

export function toNYDateTime(isoString) {
  return NY_DATETIME_FORMAT.format(new Date(isoString));
}
