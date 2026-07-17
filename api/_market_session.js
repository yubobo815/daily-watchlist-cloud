const MARKET_TIME_ZONE = "America/New_York";
const MARKET_CLOSE_MINUTES = 16 * 60;
const DAY_MS = 86400000;
const HOLIDAY_CACHE = new Map();

function isoDate(year, month, day) {
  return `${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
}

function parseIsoDate(value) {
  const text = String(value || "").slice(0, 10);
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(text);
  if (!match) return null;
  const date = new Date(Date.UTC(Number(match[1]), Number(match[2]) - 1, Number(match[3])));
  if (Number.isNaN(date.getTime()) || date.toISOString().slice(0, 10) !== text) return null;
  return date;
}

function addDays(date, count) {
  return new Date(date.getTime() + count * DAY_MS);
}

function observedFixedHoliday(year, monthIndex, day) {
  const holiday = new Date(Date.UTC(year, monthIndex, day));
  if (holiday.getUTCDay() === 6) return addDays(holiday, -1);
  if (holiday.getUTCDay() === 0) return addDays(holiday, 1);
  return holiday;
}

function nthWeekday(year, monthIndex, weekday, nth) {
  const first = new Date(Date.UTC(year, monthIndex, 1));
  const offset = (weekday - first.getUTCDay() + 7) % 7;
  return new Date(Date.UTC(year, monthIndex, 1 + offset + (nth - 1) * 7));
}

function lastWeekday(year, monthIndex, weekday) {
  const last = new Date(Date.UTC(year, monthIndex + 1, 0));
  const offset = (last.getUTCDay() - weekday + 7) % 7;
  return addDays(last, -offset);
}

function easterSunday(year) {
  const a = year % 19;
  const b = Math.floor(year / 100);
  const c = year % 100;
  const d = Math.floor(b / 4);
  const e = b % 4;
  const f = Math.floor((b + 8) / 25);
  const g = Math.floor((b - f + 1) / 3);
  const h = (19 * a + b - d - g + 15) % 30;
  const i = Math.floor(c / 4);
  const k = c % 4;
  const l = (32 + 2 * e + 2 * i - h - k) % 7;
  const m = Math.floor((a + 11 * h + 22 * l) / 451);
  const month = Math.floor((h + l - 7 * m + 114) / 31);
  const day = ((h + l - 7 * m + 114) % 31) + 1;
  return new Date(Date.UTC(year, month - 1, day));
}

function marketHolidays(year) {
  if (HOLIDAY_CACHE.has(year)) return HOLIDAY_CACHE.get(year);
  const holidays = [
    observedFixedHoliday(year, 0, 1),
    nthWeekday(year, 0, 1, 3),
    nthWeekday(year, 1, 1, 3),
    addDays(easterSunday(year), -2),
    lastWeekday(year, 4, 1),
    observedFixedHoliday(year, 6, 4),
    nthWeekday(year, 8, 1, 1),
    nthWeekday(year, 10, 4, 4),
    observedFixedHoliday(year, 11, 25),
  ];
  if (year >= 2022) holidays.push(observedFixedHoliday(year, 5, 19));
  const result = holidays.map((date) => date.toISOString().slice(0, 10));
  HOLIDAY_CACHE.set(year, result);
  return result;
}

function isMarketSession(date) {
  const weekday = date.getUTCDay();
  if (weekday === 0 || weekday === 6) return false;
  const text = date.toISOString().slice(0, 10);
  const year = date.getUTCFullYear();
  const holidays = new Set([
    ...marketHolidays(year - 1),
    ...marketHolidays(year),
    ...marketHolidays(year + 1),
  ]);
  return !holidays.has(text);
}

function previousMarketSession(date) {
  let candidate = addDays(date, -1);
  while (!isMarketSession(candidate)) candidate = addDays(candidate, -1);
  return candidate;
}

function marketCloseMinutes(date) {
  const year = date.getUTCFullYear();
  const dateText = date.toISOString().slice(0, 10);
  const independenceObserved = observedFixedHoliday(year, 6, 4);
  const preIndependence = previousMarketSession(independenceObserved).toISOString().slice(0, 10);
  const thanksgiving = nthWeekday(year, 10, 4, 4);
  const blackFriday = addDays(thanksgiving, 1).toISOString().slice(0, 10);
  const christmasEve = isoDate(year, 12, 24);
  const earlyClose = dateText === preIndependence
    || dateText === blackFriday
    || (dateText === christmasEve && isMarketSession(date));
  return earlyClose ? 13 * 60 : MARKET_CLOSE_MINUTES;
}

function newYorkClock(now = new Date()) {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: MARKET_TIME_ZONE,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).formatToParts(now).reduce((result, part) => {
    if (part.type !== "literal") result[part.type] = Number(part.value);
    return result;
  }, {});
  return parts;
}

function latestCompletedMarketSession(now = new Date()) {
  const clock = newYorkClock(now);
  const currentDate = parseIsoDate(isoDate(clock.year, clock.month, clock.day));
  if (!currentDate) return null;
  const afterClose = clock.hour * 60 + clock.minute >= marketCloseMinutes(currentDate);
  return isMarketSession(currentDate) && afterClose ? currentDate : previousMarketSession(currentDate);
}

function marketSessionAge(dataDate, now = new Date()) {
  const data = parseIsoDate(dataDate);
  const reference = latestCompletedMarketSession(now);
  if (!data || !reference || data > reference) return null;
  if (data.getTime() === reference.getTime()) return 0;
  let age = 0;
  let cursor = data;
  while (cursor < reference) {
    cursor = addDays(cursor, 1);
    if (isMarketSession(cursor)) age += 1;
  }
  return age;
}

module.exports = {
  isMarketSession,
  latestCompletedMarketSession,
  marketCloseMinutes,
  marketSessionAge,
  previousMarketSession,
};
