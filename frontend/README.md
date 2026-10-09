# Revisit — web client

A minimal, interactive front end for the Revisit knowledge base. Built with
**Next.js 16** (App Router), **React 19**, **TypeScript**, **Tailwind CSS v4**, and
subtle motion via [`motion`](https://motion.dev).

## What it does

- **Auth** — register / log in against the FastAPI backend; the JWT is stored in
  `localStorage` and attached to every request.
- **Notes** — searchable card grid with create / edit / delete and a focus-trapped modal.
- **Documents** — drag-and-drop PDF upload, live processing status with polling, and
  reprocess / delete actions.
- **Ask** — chat over your own documents with grounded answers, inline citation chips,
  a conversation drawer, and per-document scoping.

## Getting started

The backend must be running (see the repo root `README.md`) and allow this origin via
`CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000`.

```bash
npm install
npm run dev        # http://localhost:3000
```

## Configuration

Copy `.env.local.example` to `.env.local` and adjust if needed:

```bash
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

## Scripts

```bash
npm run dev      # start the dev server (Turbopack)
npm run build    # production build + type check
npm run lint     # ESLint (React Compiler rules enabled)
```

## Layout

```
src/
  app/
    layout.tsx          root layout, fonts, providers
    page.tsx            redirect splash
    login/page.tsx      auth screen
    (app)/              authenticated shell + guarded routes
      layout.tsx template.tsx
      ask/page.tsx
      notes/page.tsx
      documents/page.tsx
  components/           ui primitives, toast, logo, app-shell, auth-guard
  lib/                  api client, auth context, types, utils
```

## Notes for contributors

This is a Next.js 16 project, which includes breaking changes relative to older
releases. The `src/app/layout.tsx` and config follow the current App Router
conventions. ESLint runs the strict **React Compiler** rules — avoid synchronous
state updates directly inside effects and impure calls (e.g. `Date.now()`) during
render.
