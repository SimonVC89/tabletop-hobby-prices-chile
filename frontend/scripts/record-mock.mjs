// Graba las respuestas de la API en archivos JSON para el modo mock del frontend
// (src/api/client.ts, createMockApi): mismos datos y mismo contrato que la API, sin
// reglas propias. Reemplaza al antiguo export de Python, que recalculaba todo aparte.
//
//   npm run mock:record                # copia completa en public/mock/ (no se versiona)
//   npm run mock:sample                # muestra de ~60 juegos en public/mock-sample/ (se versiona)
//   node scripts/record-mock.mjs --api https://thpc-api.onrender.com --sample 60
//
// Por defecto lee la API local (http://localhost:8080): grabar la copia completa son
// ~18.000 pedidos y no conviene hacerlos contra el plan gratuito de Render.

import { mkdir, rm, writeFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const args = process.argv.slice(2)
const option = (name, fallback) => {
  const i = args.indexOf(`--${name}`)
  return i >= 0 && args[i + 1] ? args[i + 1] : fallback
}

const API = option('api', 'http://localhost:8080').replace(/\/$/, '')
const SAMPLE = args.includes('--sample') ? Number(option('sample', '60')) || 60 : null
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const OUT = path.join(ROOT, 'public', SAMPLE ? 'mock-sample' : 'mock')
const CONCURRENCY = 6

async function get(route, attempt = 1) {
  const res = await fetch(API + route)
  // Un 5xx o un servidor que despierta: se reintenta un par de veces con espera.
  if (res.status >= 500 && attempt < 4) {
    await new Promise((r) => setTimeout(r, 2000 * attempt))
    return get(route, attempt + 1)
  }
  if (!res.ok) throw new Error(`${res.status} en ${route}`)
  return res.json()
}

/** Corre fn sobre cada item con a lo mas `limit` pedidos a la vez. */
async function inPool(items, limit, fn) {
  const results = new Array(items.length)
  let next = 0
  let done = 0
  async function worker() {
    while (next < items.length) {
      const i = next++
      results[i] = await fn(items[i])
      done++
      if (done % 500 === 0) console.log(`  ${done}/${items.length} fichas`)
    }
  }
  await Promise.all(Array.from({ length: Math.min(limit, items.length) }, worker))
  return results
}

async function allProducts() {
  const products = []
  for (let page = 1; ; page++) {
    const res = await get(`/api/products?pageSize=100&page=${page}`)
    products.push(...res.items)
    if (page >= res.totalPages) return products
  }
}

/**
 * Juegos de la muestra: los de las ofertas y bajas (para que Inicio y Ofertas se vean
 * completos) y luego los mas comparados (mejor historial y mas relacionados).
 */
function pickSample(products, offers, drops, size) {
  const chosen = new Set()
  for (const id of [...offers.map((o) => o.productId), ...drops.map((d) => d.productId)]) {
    if (chosen.size < size) chosen.add(id)
  }
  for (const p of [...products].sort((a, b) => b.storeCount - a.storeCount)) {
    if (chosen.size >= size) break
    chosen.add(p.id)
  }
  return chosen
}

async function write(file, data) {
  await mkdir(path.dirname(file), { recursive: true })
  await writeFile(file, JSON.stringify(data), 'utf8')
}

async function main() {
  console.log(`Grabando desde ${API} en ${path.relative(ROOT, OUT)}${SAMPLE ? ` (muestra de ${SAMPLE})` : ''}`)
  const [meta, stores, offers, drops, products] = await Promise.all([
    get('/api/meta'),
    get('/api/stores'),
    get('/api/offers'),
    get('/api/price-drops'),
    allProducts(),
  ])

  const keep = SAMPLE ? pickSample(products, offers, drops, SAMPLE) : null
  const inSample = (id) => !keep || keep.has(id)
  const listed = products.filter((p) => inSample(p.id))

  console.log(`  ${listed.length} fichas por grabar...`)
  const files = await inPool(listed, CONCURRENCY, async (p) => {
    const [detail, history, similar] = await Promise.all([
      get(`/api/products/${p.id}`),
      get(`/api/products/${p.id}/price-history`),
      get(`/api/products/${p.id}/similar`),
    ])
    // En la muestra solo se enlazan relacionados que tambien estan en ella.
    return { id: p.id, data: { detail, history, similar: similar.filter((s) => inSample(s.id)) } }
  })

  // Se reemplaza todo: fichas de juegos que ya no existen no deben quedar.
  await rm(OUT, { recursive: true, force: true })
  await write(path.join(OUT, 'meta.json'), SAMPLE ? { ...meta, totalGames: listed.length } : meta)
  await write(path.join(OUT, 'stores.json'), stores)
  await write(path.join(OUT, 'offers.json'), offers.filter((o) => inSample(o.productId)))
  await write(path.join(OUT, 'price-drops.json'), drops.filter((d) => inSample(d.productId)))
  await write(path.join(OUT, 'products.json'), listed)
  for (const f of files) {
    await write(path.join(OUT, 'products', `${f.id}.json`), f.data)
  }
  console.log(`Listo: ${listed.length} juegos, ${offers.filter((o) => inSample(o.productId)).length} ofertas.`)
}

main().catch((err) => {
  console.error(`No se pudo grabar: ${err.message}`)
  process.exitCode = 1
})
