const clp = new Intl.NumberFormat('es-CL', {
  style: 'currency',
  currency: 'CLP',
  maximumFractionDigits: 0,
})

/** 31990 -> "$31.990" */
export const formatCLP = (value: number) => clp.format(value)

/** 32.4 -> "32%" (sin decimales: en una tarjeta el decimal es ruido) */
export const formatPct = (value: number) => `${Math.round(value)}%`

// hourCycle h23: es-CL usa 12 horas por defecto ("08:39 p. m.").
const dateTime = new Intl.DateTimeFormat('es-CL', {
  day: 'numeric',
  month: 'long',
  hour: '2-digit',
  minute: '2-digit',
  hourCycle: 'h23',
})

/** ISO -> "15 de octubre, 22:37" en hora de Chile */
export const formatDateTime = (iso: string) => dateTime.format(new Date(iso))

const clock = new Intl.DateTimeFormat('es-CL', { hour: '2-digit', minute: '2-digit', hourCycle: 'h23' })

/** ISO -> "hoy a las 13:41", "ayer a las 22:15" o "15 de octubre, 22:37" */
export function formatUpdated(iso: string, now: Date = new Date()) {
  const date = new Date(iso)
  const yesterday = new Date(now)
  yesterday.setDate(now.getDate() - 1)
  if (date.toDateString() === now.toDateString()) return `hoy a las ${clock.format(date)}`
  if (date.toDateString() === yesterday.toDateString()) return `ayer a las ${clock.format(date)}`
  return `el ${formatDateTime(iso)}`
}

/** ISO -> "hoy", "ayer" o "hace 3 días", contando días de calendario y no horas */
export function formatDaysAgo(iso: string, now: Date = new Date()) {
  const startOfDay = (d: Date) => new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime()
  // round y no floor: un dia con cambio de horario dura 23 o 25 horas.
  const days = Math.round((startOfDay(now) - startOfDay(new Date(iso))) / 86_400_000)
  if (days <= 0) return 'hoy'
  if (days === 1) return 'ayer'
  return `hace ${days} días`
}

// Los dias del historial vienen como "2026-10-13" (sin hora): se formatean
// en UTC para que la zona horaria no los corra al dia anterior.
const day = new Intl.DateTimeFormat('es-CL', { day: 'numeric', month: 'short', timeZone: 'UTC' })

/** "2026-10-13" -> "13 oct" */
export const formatDay = (isoDate: string) => day.format(new Date(isoDate)).replace('.', '')

const shortDate = new Intl.DateTimeFormat('es-CL', { day: 'numeric', month: 'short', year: 'numeric' })

/** Timestamp ISO -> "13 oct 2026", en hora de Chile */
export const formatShortDate = (iso: string) => shortDate.format(new Date(iso)).replaceAll('.', '')

const count = new Intl.NumberFormat('es-CL')

/** 6194 -> "6.194" */
export const formatCount = (value: number) => count.format(value)
