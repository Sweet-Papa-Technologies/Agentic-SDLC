Vendored third-party parser — ships with the skill so intent-gate gets a real
AST with ZERO user install (no npm, no network at runtime).

- acorn.js — acorn 8.17.0, MIT. Source: https://github.com/acornjs/acorn
  Unmodified dist/acorn.js. License text in acorn.LICENSE.

intent-gate prefers this AST engine and falls back to its built-in token analyzer
for any file acorn cannot parse (e.g. TypeScript type syntax, JSX).
