/** Horas de partida del scraper (hora de Chile), en minutos desde medianoche. */
const SCRAPER_RUNS = [5 * 60 + 17, 19 * 60 + 17]

const chileClock = new Intl.DateTimeFormat('es-CL', {
  timeZone: 'America/Santiago',
  hour: 'numeric',
  minute: 'numeric',
  hourCycle: 'h23',
})

/** "hoy a las 19:17" o "mañana a las 5:17", según la hora de Chile (aunque el navegador esté en otra zona). */
export function nextScraperRun(now: Date = new Date()) {
  const parts = Object.fromEntries(chileClock.formatToParts(now).map((p) => [p.type, p.value]))
  const minutes = Number(parts.hour) * 60 + Number(parts.minute)
  const next = SCRAPER_RUNS.find((run) => run > minutes)
  const run = next ?? SCRAPER_RUNS[0]
  const time = `${Math.floor(run / 60)}:${String(run % 60).padStart(2, '0')}`
  return `${next === undefined ? 'mañana' : 'hoy'} a las ${time}`
}
