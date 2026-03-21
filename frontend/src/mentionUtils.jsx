import React from 'react';
import { Link } from 'react-router-dom';

function slugify(nome) {
  return (nome || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .toLowerCase().trim().replace(/[^a-z0-9\s-]/g, '').replace(/\s+/g, '-');
}

/** Retorna os slugs inválidos encontrados no texto (menções que não existem). */
export function invalidMentions(text, researchers) {
  const valid = new Set(researchers.map(r => slugify(r.nome)));
  return (text.match(/@([\w-]+)/g) || []).filter(m => !valid.has(m.slice(1)));
}

const URL_RE = /https?:\/\/[^\s]+/g;
const SPLIT_RE = /(\*\*[^*]+\*\*|\*[^*]+\*|_[^_]+_|@[\w-]+|https?:\/\/[^\s]+)/g;

/**
 * Renderiza o texto com formatação (**negrito**, *itálico*, _sublinhado_),
 * @menções válidas destacadas em azul e URLs como links clicáveis.
 */
export function renderWithMentions(text, researchers) {
  const valid = new Set(researchers.map(r => slugify(r.nome)));
  const parts = text.split(SPLIT_RE);
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**'))
      return <strong key={i}>{part.slice(2, -2)}</strong>;
    if (part.startsWith('*') && part.endsWith('*'))
      return <em key={i}>{part.slice(1, -1)}</em>;
    if (part.startsWith('_') && part.endsWith('_'))
      return <u key={i}>{part.slice(1, -1)}</u>;
    if (part.startsWith('@') && valid.has(part.slice(1)))
      return (
        <Link key={i} to={`/app/profile/${part.slice(1)}`}
          className="inline-flex items-center rounded bg-blue-100 px-1 py-0.5 text-[11px] font-semibold text-blue-700 leading-tight hover:bg-blue-200">
          {part}
        </Link>
      );
    if (URL_RE.test(part)) {
      URL_RE.lastIndex = 0;
      return (
        <a key={i} href={part} target="_blank" rel="noreferrer"
          className="text-blue-600 underline underline-offset-2 hover:text-blue-800 break-all">
          {part}
        </a>
      );
    }
    return part;
  });
}
