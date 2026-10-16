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
