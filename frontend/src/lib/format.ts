const clp = new Intl.NumberFormat('es-CL', {
  style: 'currency',
  currency: 'CLP',
  maximumFractionDigits: 0,
})

/** 31990 -> "$31.990" */
export const formatCLP = (value: number) => clp.format(value)

/** 32.4 -> "32%" (sin decimales: en una tarjeta el decimal es ruido) */
export const formatPct = (value: number) => `${Math.round(value)}%`

const dateTime = new Intl.DateTimeFormat('es-CL', {
  day: 'numeric',
  month: 'long',
  hour: '2-digit',
  minute: '2-digit',
})

/** ISO -> "15 de octubre, 22:37" en hora de Chile */
export const formatDateTime = (iso: string) => dateTime.format(new Date(iso))

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
