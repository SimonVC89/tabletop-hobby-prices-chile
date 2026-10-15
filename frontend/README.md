# Frontend — Tabletop Hobby Prices Chile

React + TypeScript + Vite, con Tailwind CSS y componentes de shadcn/ui.

## Desarrollo

```bash
npm install
npm run dev      # http://localhost:5173
npm run build    # type-check + build de produccion
```

## Diseño

- El tema (colores, tipografías, radios) vive en `src/index.css` y se deriva
  de la paleta de marca en `docs/brand/thpc-paleta.css`.
- Colores semánticos del dominio disponibles como clases de Tailwind:
  `text-deal` / `bg-deal` (oferta real), `text-price-up` (subió de precio),
  `text-highlight` (destacado).
- Precios y cifras: clase utilitaria `price` (IBM Plex Mono + números
  tabulares, para que las columnas de precios alineen).
- Logos para la web en `public/brand/*-web.svg` (versiones recortadas y con
  fondo transparente de los originales `*-oscuro.svg` / `*-claro.svg`).
