// Shared slate logic for Card, Legs and Floor Lines: which slate is "next", and the THU / SUN / MON switch.

export const SLATES = [["tnf", "THU"], ["sun", "SUN"], ["mnf", "MON"]];

// First kickoff of each slate, in minutes after Tuesday 00:00 ET (the NFL week turns over on Tuesday).
// Fixed times: Thu 8:15 PM, Sun 1:00 PM, Mon 8:15 PM ET. Early international Sunday games are ignored.
const DAY = 1440;
const KICKOFF = { tnf: 2 * DAY + 20 * 60 + 15, sun: 5 * DAY + 13 * 60, mnf: 6 * DAY + 20 * 60 + 15 };
const WEEKDAY = { Tue: 0, Wed: 1, Thu: 2, Fri: 3, Sat: 4, Sun: 5, Mon: 6 };

function minutesIntoWeekET(now = new Date()) {
  const parts = Object.fromEntries(new Intl.DateTimeFormat("en-US", { timeZone: "America/New_York",
    weekday: "short", hour: "numeric", minute: "numeric", hourCycle: "h23" })
    .formatToParts(now).map(p => [p.type, p.value]));
  return WEEKDAY[parts.weekday] * DAY + Number(parts.hour) * 60 + Number(parts.minute);
}

// TNF until Thursday's kickoff, then SUN until Sunday's first kickoff, then MNF; after MNF kicks off, next week's TNF.
export function upcomingSlate(now = new Date()) {
  const t = minutesIntoWeekET(now);
  return SLATES.map(([s]) => s).find(s => t < KICKOFF[s]) || "tnf";
}

// The upcoming slate if its file is posted; otherwise the most recent posted slate before it, then any posted one.
export function defaultSlate(files, now = new Date()) {
  const order = SLATES.map(([s]) => s);
  const want = upcomingSlate(now);
  const i = order.indexOf(want);
  const back = [0, 1, 2].map(k => order[(i - k + 3) % 3]);
  return back.find(s => files?.[s]) || want;
}
