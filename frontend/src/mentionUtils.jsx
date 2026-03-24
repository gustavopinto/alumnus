import React, { useState } from 'react';
import { Link } from 'react-router-dom';

export function slugify(nome) {
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

/**
 * Hook que encapsula toda a lógica de @mention.
 * @param {object} opts
 * @param {string}   opts.text        - valor atual do input
 * @param {function} opts.setText     - setter do texto
 * @param {object}   opts.inputRef    - ref do elemento de input/textarea
 * @param {array}    opts.researchers - lista de pesquisadores disponíveis
 * @param {number}   [opts.maxLength] - limite de caracteres ao inserir menção
 */
export function useMentions({ text, setText, inputRef, researchers, maxLength = null }) {
  const [mentionSearch, setMentionSearch] = useState(null); // { start, query } | null
  const [mentionIndex, setMentionIndex] = useState(0);

  const mentionSuggestions = mentionSearch !== null
    ? researchers.filter(r =>
        r.nome.toLowerCase().includes(mentionSearch.query) ||
        slugify(r.nome).includes(mentionSearch.query)
      ).slice(0, 6)
    : [];

  function handleTextChange(e) {
    const val = e.target.value;
    setText(val);
    const pos = e.target.selectionStart;
    const before = val.slice(0, pos);
    const match = before.match(/@([\w-]*)$/);
    if (match) {
      setMentionSearch({ start: match.index, query: match[1].toLowerCase() });
      setMentionIndex(0);
    } else {
      setMentionSearch(null);
    }
  }

  function insertMention(slug) {
    const el = inputRef.current;
    if (!el || !mentionSearch) return;
    const pos = el.selectionStart;
    const before = text.slice(0, mentionSearch.start);
    const after = text.slice(pos);
    let newText = before + '@' + slug + ' ' + after;
    if (maxLength != null) newText = newText.slice(0, maxLength);
    setText(newText);
    setMentionSearch(null);
    setMentionIndex(0);
    requestAnimationFrame(() => {
      const newPos = before.length + slug.length + 2;
      el.setSelectionRange(newPos, newPos);
      el.focus();
    });
  }

  /**
   * Chame no onKeyDown do input. Retorna true se a tecla foi tratada pela lógica
   * de mention (para que o caller pule seu próprio handler, ex: submit).
   */
  function handleMentionKeyDown(e) {
    if (!mentionSuggestions.length) return false;
    if (e.key === 'Escape') { e.preventDefault(); setMentionSearch(null); return true; }
    if (e.key === 'ArrowDown') { e.preventDefault(); setMentionIndex(i => (i + 1) % mentionSuggestions.length); return true; }
    if (e.key === 'ArrowUp') { e.preventDefault(); setMentionIndex(i => (i - 1 + mentionSuggestions.length) % mentionSuggestions.length); return true; }
    if (e.key === 'Enter') { e.preventDefault(); insertMention(slugify(mentionSuggestions[mentionIndex].nome)); return true; }
    return false;
  }

  return {
    mentionSearch,
    setMentionSearch,
    mentionIndex,
    setMentionIndex,
    mentionSuggestions,
    handleTextChange,
    insertMention,
    handleMentionKeyDown,
  };
}

/** Dropdown de sugestões de @mention. Renderize dentro de um container `relative`. */
export function MentionDropdown({ suggestions, activeIndex, onSelect, onHover, zIndex = 'z-50' }) {
  if (!suggestions.length) return null;
  return (
    <div className={`absolute left-0 right-0 top-full mt-0.5 bg-white border rounded-lg shadow-lg ${zIndex} py-1`}>
      {suggestions.map((r, i) => (
        <button
          key={r.id}
          type="button"
          onMouseDown={e => { e.preventDefault(); onSelect(slugify(r.nome)); }}
          onMouseEnter={() => onHover(i)}
          className={`w-full text-left px-3 py-1.5 text-sm flex items-center gap-2 ${i === activeIndex ? 'bg-blue-50 text-blue-700' : 'hover:bg-blue-50 hover:text-blue-700'}`}
        >
          <span className="font-medium">{r.nome}</span>
          <span className="text-xs text-gray-400">@{slugify(r.nome)}</span>
        </button>
      ))}
    </div>
  );
}
