# SEO Autoblog Money

Repositorio independiente en Python 3.11 para descubrir temas, generar articulos SEO largos, monetizar con afiliados y publicar automaticamente en GitHub Pages sin costo.

## Caracteristicas

- Generacion automatica de posts de 1200-1800 palabras con estructura SEO.
- Interlinking automatico (2 posts relacionados + 1 guia pilar).
- Monetizacion por afiliados configurable con disclaimer.
- Captura email sin backend (Google Form opcional + fallback mailto).
- SEO tecnico: `robots.txt`, `sitemap.xml`, `rss.xml`, JSON-LD por post.
- Idempotencia local en `state/state.json`.
- Pipeline diario en GitHub Actions + despliegue a GitHub Pages.

## Estructura principal

- `seo_factory/`: paquete Python con CLI y logica de negocio.
- `config/`: fuentes, afiliados y datos del sitio.
- `docs/`: contenido de MkDocs (posts, guias, assets, RSS).
- `state/state.json`: slugs publicados para evitar duplicados.
- `.github/workflows/publish.yml`: automatizacion diaria.

## Uso local

1. Crear entorno e instalar dependencias:

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate
pip install -r requirements.txt
```

2. Copiar variables de entorno:

```bash
cp .env.example .env
```

3. Ejecutar flujo diario local (modo editorial):

```bash
python -m seo_factory run --daily --limit 1
python -m seo_factory build-site
mkdocs serve
```

4. Comandos CLI disponibles:

```bash
python -m seo_factory discover --limit 20
python -m seo_factory generate --limit 1
python -m seo_factory build-site
python -m seo_factory run --daily --limit 1
```

Opcional: usar `--dry-run` para simular sin escribir en `docs/` ni `state/`.
Con `--daily` el sistema aplica **tope estricto de 1 articulo por dia (UTC)** usando `state/state.json`.

## Subir repo y publicar

1. Crear repo publico nuevo en GitHub: `seo-autoblog-money`.
2. Subir este contenido a `main`.
3. Ir a **Settings -> Pages** y seleccionar **GitHub Actions** como source.
4. Ejecutar workflow `publish-pages` manualmente (workflow_dispatch) o esperar el schedule.
5. Ver URL final en el panel de Pages.

## Como cambiar nicho y afiliados

1. Editar `config/site.yaml` para `site_name`, `site_url` y `niche`.
2. Editar `config/sources.yaml` para RSS, StackExchange y keywords prioritarias.
3. Editar `config/affiliates.yaml` para reglas por keyword/categoria.
4. (Opcional) Definir `NEWSLETTER_FORM_URL` y/o `NEWSLETTER_EMAIL` en `.env` (local).

## Estrategia de publicacion en Actions

Este proyecto **commitea los posts generados en `main`** con `github-actions[bot]` antes del build de MkDocs. Asi el contenido queda versionado y visible en el repositorio ademas de publicarse en Pages.

