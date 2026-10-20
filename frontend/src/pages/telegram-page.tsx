import { Bell, ShieldCheck, Star } from 'lucide-react'
import { useEffect } from 'react'
import { Button } from '@/components/ui/button'

const BOT_USERNAME = 'TabletopPricesChile_bot'
const BOT_URL = `https://t.me/${BOT_USERNAME}`

const COMMANDS = [
  { command: '/start', text: 'Recibir el resumen de ofertas.' },
  { command: '/seguir catan', text: 'Buscar un juego y seguirlo. Toca la opción que quieras: no hace falta escribir el nombre completo.' },
  { command: '/siguiendo', text: 'Ver los juegos que sigues (hasta 20).' },
  { command: '/stop', text: 'Pausar el resumen de ofertas. Tus juegos seguidos se mantienen.' },
  { command: '/dar_de_baja', text: 'Baja total y permanente: detiene todos los avisos y borra tu lista. Por ahora no se puede reactivar.' },
  { command: '/ayuda', text: 'Ver los comandos y cómo funciona.' },
]

export function TelegramPage() {
  useEffect(() => {
    document.title = 'Avisos por Telegram · Tabletop Hobby Prices Chile'
    return () => {
      document.title = 'Tabletop Hobby Prices Chile'
    }
  }, [])

  return (
    <div>
      <header className="max-w-3xl">
        <h1 className="text-3xl font-bold sm:text-4xl">Ofertas en tu Telegram</h1>
        <p className="mt-3 text-muted-foreground">
          Un bot te escribe cuando aparece una oferta de verdad, o cuando baja de precio un juego que tú sigues. Sin
          cuentas ni contraseñas: solo necesitas Telegram.
        </p>
        <Button asChild size="lg" className="mt-6 h-11 px-5 text-base">
          <a href={BOT_URL} target="_blank" rel="noopener noreferrer">
            Abrir @{BOT_USERNAME}
            <span className="sr-only"> (se abre en Telegram)</span>
          </a>
        </Button>
      </header>

      <section aria-labelledby="que-recibes" className="mt-12">
        <h2 id="que-recibes" className="text-xl font-bold">
          Qué puedes recibir
        </h2>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <Card icon={Bell} title="Resumen de ofertas">
            <p>
              Por la <strong className="font-medium text-foreground">mañana y por la tarde</strong>, solo cuando hay
              ofertas nuevas: juegos que una tienda vende al menos <strong className="font-medium text-foreground">20% bajo la mediana</strong> de
              3 o más tiendas. Las de 50% o más van arriba, destacadas.
            </p>
            <p className="mt-2">Si ese día no hay nada nuevo, no recibes nada. Para activarlo, escribe <Code>/start</Code>.</p>
          </Card>
          <Card icon={Star} title="Seguimiento de juegos">
            <p>
              Elige hasta 20 juegos con <Code>/seguir</Code>. Te aviso cuando su mejor precio baja{' '}
              <strong className="font-medium text-foreground">al menos 5%</strong>, o cuando un juego agotado{' '}
              <strong className="font-medium text-foreground">vuelve a tener stock</strong>.
            </p>
            <p className="mt-2">Si sigues juegos y además tienes el resumen, ambos llegan juntos en un solo mensaje.</p>
          </Card>
        </div>
      </section>

      <section aria-labelledby="ejemplo" className="mt-12">
        <h2 id="ejemplo" className="text-xl font-bold">
          Así se ve un aviso
        </h2>
        <figure className="mt-4 max-w-xl">
          <div className="rounded-2xl rounded-tl-sm border bg-secondary p-4 text-sm leading-relaxed break-words">
            <p className="font-medium">🌆 Resumen de esta tarde</p>
            <p className="mt-3 font-medium">⭐ De tu lista:</p>
            <p>• Catan bajó a $24.990 en Aldea Juegos (antes $29.990, -17%)</p>
            <p className="pl-3 text-muted-foreground">https://tienda.cl/catan</p>
            <p className="mt-3 font-medium">🔥 Ofertas destacadas (50%+ bajo la mediana):</p>
            <p>1. Juego de ejemplo - $15.990 (52% off, La Loseta)</p>
            <p className="pl-3 text-muted-foreground">https://tienda.cl/juego-de-ejemplo</p>
          </div>
          <figcaption className="mt-2 text-xs text-muted-foreground">
            Ejemplo con datos de muestra: los avisos reales traen el nombre, el precio, el descuento, la tienda y el enlace directo al
            producto.
          </figcaption>
        </figure>
      </section>

      <section aria-labelledby="empezar" className="mt-12">
        <h2 id="empezar" className="text-xl font-bold">
          Cómo empezar
        </h2>
        <ol className="mt-4 max-w-3xl list-decimal space-y-2 pl-5 text-muted-foreground marker:text-foreground">
          <li>
            Abre el bot y toca <strong className="font-medium text-foreground">Iniciar</strong> (o escribe <Code>/start</Code>) para recibir
            el resumen de ofertas.
          </li>
          <li>
            Para seguir un juego, escribe <Code>/seguir</Code> y su nombre, por ejemplo <Code>/seguir catan</Code>. El bot te ofrece
            opciones que puedes tocar, y si hay muchas, te sugiere qué palabra agregar para acotar.
          </li>
          <li>
            Cuando quieras pausar el resumen, escribe <Code>/stop</Code>.
          </li>
        </ol>
      </section>

      <section aria-labelledby="comandos" className="mt-12">
        <h2 id="comandos" className="text-xl font-bold">
          Comandos
        </h2>
        <dl className="mt-4 divide-y rounded-lg border bg-card">
          {COMMANDS.map((c) => (
            <div key={c.command} className="grid gap-1 px-4 py-3 sm:grid-cols-[13rem_1fr] sm:gap-4">
              <dt>
                <Code>{c.command}</Code>
              </dt>
              <dd className="text-sm text-muted-foreground">{c.text}</dd>
            </div>
          ))}
        </dl>
      </section>

      <section aria-labelledby="privacidad" className="mt-12 max-w-3xl">
        <h2 id="privacidad" className="flex items-center gap-2 text-xl font-bold">
          <ShieldCheck className="size-5 text-muted-foreground" aria-hidden="true" />
          Privacidad
        </h2>
        <p className="mt-3 text-muted-foreground">
          El bot guarda solo el identificador de tu chat (un número que asigna Telegram): ni tu nombre, ni tu teléfono, ni tu usuario. Con{' '}
          <Code>/dar_de_baja</Code> se detienen todos los avisos de forma permanente y se borra tu lista de juegos; se conserva únicamente
          ese número para recordar que pediste la baja.
        </p>
      </section>
    </div>
  )
}

function Card({
  icon: Icon,
  title,
  children,
}: {
  icon: typeof Bell
  title: string
  children: React.ReactNode
}) {
  return (
    <article className="rounded-lg border bg-card p-5 text-sm text-muted-foreground">
      <h3 className="flex items-center gap-2 text-base font-semibold text-foreground">
        <Icon className="size-4 text-primary" aria-hidden="true" />
        {title}
      </h3>
      <div className="mt-3 leading-relaxed">{children}</div>
    </article>
  )
}

function Code({ children }: { children: React.ReactNode }) {
  return <code className="price rounded bg-secondary px-1.5 py-0.5 text-[0.85em] text-foreground">{children}</code>
}
