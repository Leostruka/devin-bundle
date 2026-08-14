#!/usr/bin/env node
/**
 * audit-design.mjs — Auditor determinístico de HIG para a UI WebView2 (BackupEmail).
 *
 * USO:
 *   node audit-design.mjs [caminhos...]
 *   Ex.: node audit-design.mjs dashboard.html settings.css app.js
 *   Aceita arquivos e diretórios (diretórios são varridos recursivamente).
 *   Aceita também .xaml/.ts para escanear JS embutido e marcações.
 *
 * PROPÓSITO:
 *   Reporta (NÃO corrige) desvios detectáveis por regex/heurística da família
 *   apple-hig. Cada desvio vira uma linha "CRÍTICO | AVISO arquivo:linha motivo".
 *
 * REGRAS E GRAVIDADE:
 *   CRÍTICO (exit 1):
 *     - `transition: all`                        → HIG Motion: só transform/opacity
 *     - alert( / confirm( / prompt( nativos      → HIG Alerts/Notifications
 *     - font-size < 11px em conteúdo             → HIG Typography (mínimo 10–11pt)
 *     - maximum-scale / user-scalable=no         → HIG Accessibility (zoom bloqueado)
 *   AVISO (exit 0):
 *     - font-size/padding/margin/gap em px fora da escala de tokens
 *     - cor hex fora de definição de token       → HIG Color (semânticas)
 *     - controles interativos sem :focus-visible no CSS
 *     - classes de estado (.ok/.error/.warning/...) que só pintam cor
 *     - <div onclick> em vez de <button>/<a>
 *
 * CONTRATO DE TOKENS PERMITIDOS (defina em :root):
 *   Texto:  --text-title1 .. --text-caption2
 *   Espaço: --space-1(4) --space-2(8) --space-3(12) --space-4(16) --space-5(20)
 *           --space-6(24) --space-8(32) --space-12(48)
 *   Raio:   --radius-controls(8) --radius-cards(10) --radius-large(20) --radius-capsule(999)
 *   Cor:    --bg-primary --bg-elevated --bg-secondary --text-primary --text-secondary
 *           --text-tertiary --separator --accent (e variantes *-dark)
 *   Dur:    --dur-fast(120ms) --dur-base(200ms) --dur-slow(300ms)
 *
 * EXIT: 0 = sem críticos (avisos ok) | 1 = ao menos um crítico | 2 = uso inválido.
 */
import { readFileSync, statSync, readdirSync } from 'node:fs';
import { join, extname } from 'node:path';

const EXT = new Set(['.html', '.htm', '.css', '.js', '.mjs', '.cjs', '.ts', '.tsx', '.xaml']);
const SPACE_SCALE = new Set([0, 4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 48, 56, 64, 80, 96, 128]);
const TEXT_MIN_PX = 11;
const STATE_RE = /\.([\w-]*(?:ok|success|error|warning|failed|running|paused|critical)[\w-]*)\s*[{,]/;

let criticals = 0;
let warnings = 0;
const report = [];

function collect(path, out = []) {
  const st = statSync(path);
  if (st.isDirectory()) {
    for (const entry of readdirSync(path)) collect(join(path, entry), out);
  } else if (EXT.has(extname(path).toLowerCase())) {
    out.push(path);
  }
  return out;
}

function add(sev, file, line, msg) {
  const tag = sev === 'CRIT' ? 'CRÍTICO' : 'AVISO';
  report.push(`${tag.padEnd(8)} ${file}:${line}  ${msg}`);
  if (sev === 'CRIT') criticals += 1;
  else warnings += 1;
}

function scanCss(text, file) {
  const src = text.split('\n');
  const isTokenDef = (l) => /--[\w-]+\s*:/.test(l);
  src.forEach((raw, i) => {
    const n = i + 1;
    const line = raw.trim();
    let m = line.match(/font-size:\s*(\d+(?:\.\d+)?)px/);
    if (m) {
      const v = parseFloat(m[1]);
      if (v < TEXT_MIN_PX) add('CRIT', file, n, `font-size ${v}px abaixo do mínimo legível (${TEXT_MIN_PX}px)`);
      else add('AVISO', file, n, `font-size hardcoded ${v}px — use token --text-*`);
    }
    m = line.match(/(?:padding|margin|gap|row-gap|column-gap):\s*(\d+)px/);
    if (m && !SPACE_SCALE.has(parseInt(m[1], 10))) {
      add('AVISO', file, n, `espaçamento ${m[1]}px fora da grade 8pt — use --space-*`);
    }
    if (!isTokenDef(line) && /#[0-9a-fA-F]{3,8}\b/.test(line) && !/gradient|shadow|url\(|stroke|fill/.test(line)) {
      add('AVISO', file, n, 'cor hex fora de token semântico — use --bg-*/--text-*/--accent');
    }
    if (/\btransition\s*:\s*all\b/.test(line)) {
      add('CRIT', file, n, 'transition: all — anime apenas transform/opacity');
    }
    if (STATE_RE.test(line) && !/font-|content\s*:|::|icon/.test(line)) {
      add('AVISO', file, n, 'estado expresso só por cor — garanta texto/ícone adjacente');
    }
  });
  const joined = text.replace(/\/\*[\s\S]*?\*\//g, '');
  const hasControls = /(button|input|select|textarea|a)\b/.test(joined) || /cursor:\s*pointer/.test(joined);
  if (hasControls && !/::?focus-visible/.test(joined)) {
    add('AVISO', file, 1, 'controles interativos sem regra :focus-visible (ring 2px + offset 2px)');
  }
}

function scanJs(text, file) {
  text.split('\n').forEach((raw, i) => {
    const line = raw.replace(/\/\/.*$/, '');
    const m = line.match(/\b(alert|confirm|prompt)\s*\(/);
    if (m) add('CRIT', file, i + 1, `nativo ${m[1]}() — use componente da skill hig-alerts`);
  });
}

function scanHtml(text, file) {
  text.split('\n').forEach((raw, i) => {
    const n = i + 1;
    if (/maximum-scale|user-scalable\s*=\s*['"]?no/i.test(raw)) {
      add('CRIT', file, n, 'zoom desabilitado — remover maximum-scale/user-scalable=no');
    }
    if (/<div[^>]*\bonclick=/i.test(raw)) {
      add('AVISO', file, n, '<div onclick> — use <button>/<a> reais (a11y + teclado)');
    }
  });
}

const files = [];
for (const arg of process.argv.slice(2)) {
  try { files.push(...collect(arg)); }
  catch (e) { console.error(`ignorando "${arg}": ${e.message}`); }
}

if (files.length === 0) {
  console.error('Nenhum arquivo .html/.css/.js/.ts/.xaml encontrado.');
  console.error('Uso: node audit-design.mjs [caminhos...]');
  process.exit(2);
}

for (const f of files) {
  const text = readFileSync(f, 'utf8');
  const ext = extname(f).toLowerCase();
  if (ext === '.css') scanCss(text, f);
  else if (ext === '.html' || ext === '.htm') scanHtml(text, f);
  else scanJs(text, f);
}

console.log(report.length ? report.join('\n') : 'Nenhum desvio detectado.');
console.log(`\nResumo: ${criticals} crítico(s), ${warnings} aviso(s), ${files.length} arquivo(s).`);
process.exit(criticals > 0 ? 1 : 0);
