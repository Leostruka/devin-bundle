---
name: typescript-node
description: Use when writing or reviewing TypeScript or Node.js code. Strict mode, async/await footguns, error handling, null safety, real types vs any, ESM/CJS interop, npm hygiene (engines, lockfile, scripts, ci).
triggers: [user, model]
allowed-tools: [read, exec, grep, edit]
---

# TypeScript & Node.js

Modern TypeScript and Node.js. The compiler only helps if you do not lie to it - `any`, `as`, and `!` disable the protection that justifies the cost of TS.

## Config and types

- `strict: true` in tsconfig (includes `strictNullChecks`, `noImplicitAny`). A project without strict is JavaScript with annotations.
- `noUncheckedIndexedAccess` for safe indexing (`arr[i]` returns `T | undefined` - the source of most "undefined is not a function" bugs).
- `exactOptionalPropertyTypes` when the repo uses it - `x?: T` does not accept explicit `undefined`.
- `any` = virus: propagates and disables checking. Prefer `unknown` + narrowing (`typeof`, `instanceof`, type guard).
- `as T` only when you KNOW more than the compiler (rarely). `satisfies` validates without widening.
- `!` non-null assertion = "trust me": use only after a check that guarantees it, or refactor to narrowing.
- Type guard: `function isX(v: unknown): v is X` - real narrowing instead of cast.
- `interface` for objects/contracts, `type` for unions/intersections/utilities. `enum` only when a runtime value is needed; `as const` + union covers the rest.
- Generics with constraints (`<T extends X>`); hidden `any` in a generic does not count as typed.

## Null safety

- `?.`/`??` for optional access and fallback; `??` (not `||`) when `0`/`''`/`false` are valid values - `||` swallows them.
- `Array.find`/`Map.get` return `undefined`: handle it, do not assume.
- External API data is `unknown` until validated: `zod`/`valibot` at the boundary (parse, not cast) - `JSON.parse` returns `any` and lies.
- With `strictNullChecks` on, `T | null | undefined` is explicit - do not bypass with `!`.

## Async/await footguns

- Forgotten `await` = dangling promise: an `async` returning `Promise<T>` must be awaited or returned.
- `forEach(async)` does NOT wait: runs in parallel without awaiting. Correct: sequential `for...of` or `Promise.all(map)` for parallel.
- `Promise.all` rejects on the first failure and abandons the others (which keep running). `Promise.allSettled` when each result matters.
- try/catch only catches errors after `await` - a promise without await escapes the try (floating promise). ESLint `@typescript-eslint/no-floating-promises` catches this.
- `unhandledRejection` crashes modern Node: every promise gets await, `.catch()`, or `Promise.allSettled`.
- `async` in event-handler/fire-and-forget callbacks: explicit `.catch(log)`.
- Fetch timeout: `AbortSignal.timeout(ms)` - fetch without timeout can hang forever.

## Error handling

- `throw new Error('msg', { cause: e })` - never `throw 'string'` or `throw e` without context.
- `catch (e)`: `e` is `unknown` under strict - narrow (`e instanceof Error`) before `e.message`.
- Custom errors: class `extends Error` with `name` - `instanceof` distinguishes failure types.
- A catch that only logs and continues = swallowing: handle or re-throw with context.
- `process.on('unhandledRejection')` as a safety net in services - not as a strategy.

## Node and runtime

- `node:fs/promises` over sync callbacks; sync (`readFileSync`) blocks the whole event loop - only in scripts/CLIs, never in servers.
- Buffer/stream for large files; whole-file `readFile` into memory explodes on big files.
- `process.env.X` is `string | undefined`: validate at the boundary (throw at boot if missing) or explicit default - never `process.env.KEY!`.
- ESM (`import`) vs CJS (`require`): new projects ESM (`"type": "module"`); `__dirname` does not exist in ESM (`import.meta.dirname` on Node 20.11+).
- Top-level await only in ESM; in CJS wrap in `async main()`.

## npm and dependencies

- `npm ci` in CI/deploy (respects lockfile); `npm install` only in dev.
- `engines.node` declared; version pinned via `.nvmrc`/devcontainers.
- Dependency `prepublish`/`postinstall` scripts are supply-chain surface - `npm install --ignore-scripts` when not needed.
- `npm audit`/`npm ls <pkg>` before adopting a dep; commit the lockfile together with `package.json` (dep change without lockfile = CI installs something different from local).
- `npx` executes remote code: `npx pkg` downloads and runs - confirm the package is official.

## Common review findings

- `any`/`as`/`!` proliferating (fake typing).
- `forEach(async)` or `map` with async without `Promise.all`.
- Promises without await/catch (floating).
- `||` where `??` was meant (swallows `0`/`''`).
- `JSON.parse`/`res.json()` cast straight to a type (lie).
- `process.env.X` used unvalidated.
- `readFileSync`/`execSync` in a server (blocks the loop).
- `try` without a real `catch` (empty catch, log-only catch).
- New dependency without updated `package-lock`.
- `console.log` of large objects/objects with secrets in prod.

## Cascade

- JS test fundamentals: `testing` (vitest/jest at the boundary).
- npm/shell script footguns: `shell-safe`.
- Node CI (npm ci, cache): `github-actions`, `deploy`.
