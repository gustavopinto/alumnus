import React, { useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { slugify } from '../mentionUtils.jsx';

const URL_RE = /(https?:\/\/[^\s<]+)/;

// Converte markdown simples para HTML (para notas legadas sem HTML do TipTap)
// Suporta: **bold**, *italic*, _italic_, parágrafos duplos, \n como <br>
function markdownToHtml(text, inline = false) {
  if (!text) return '';

  let result = text
    // Bold: **texto**
    .replace(/\*\*(.+?)\*\*/gs, '<strong>$1</strong>')
    // Italic: *texto* (não adjacente a outro *)
    .replace(/(?<!\*)\*([^*\n]+?)\*(?!\*)/g, '<em>$1</em>')
    // Italic: _texto_
    .replace(/(?<!_)_([^_\n]+?)_(?!_)/g, '<em>$1</em>');

  if (inline) {
    return result.replace(/\n+/g, ' ');
  }

  // Wrap em parágrafos separados por linha dupla
  const paragraphs = result.split(/\n\n+/).filter(p => p.trim());
  if (paragraphs.length === 0) return '';
  return paragraphs
    .map(para => `<p>${para.replace(/\n/g, '<br>')}</p>`)
    .join('');
}

export default function RichContent({ html = '', researchers = [], className = '', inline = false }) {
  const navigate = useNavigate();
  const ref = useRef();

  const isHtml = typeof html === 'string' && html.includes('<');

  // Para conteúdo não-HTML, converte markdown → HTML para renderizar formatação
  const renderedHtml = isHtml ? html : markdownToHtml(html, inline);
  const useHtmlPath = isHtml || (renderedHtml !== '' && renderedHtml !== html);

  useEffect(() => {
    if (!ref.current) return;

    // Linkifica URLs bare dentro de text nodes que não estão dentro de <a>
    const walker = document.createTreeWalker(ref.current, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    for (const node of nodes) {
      if (node.parentElement?.closest('a')) continue;
      if (!URL_RE.test(node.textContent)) continue;
      const frag = document.createDocumentFragment();
      node.textContent.split(URL_RE).forEach(seg => {
        if (seg && URL_RE.test(seg)) {
          const a = document.createElement('a');
          a.href = seg;
          a.target = '_blank';
          a.rel = 'noopener noreferrer';
          a.className = 'text-blue-600 hover:underline break-all';
          a.textContent = seg;
          frag.appendChild(a);
        } else if (seg) {
          frag.appendChild(document.createTextNode(seg));
        }
      });
      node.parentNode.replaceChild(frag, node);
    }

    function handler(e) {
      if (e.target.closest('a')) return;
      const el = e.target.closest('[data-type="mention"]');
      if (el) {
        const id = el.getAttribute('data-id');
        if (id && id !== 'todos') navigate(`/app/profile/${id}`);
      }
    }
    const nodeEl = ref.current;
    nodeEl.addEventListener('click', handler);
    return () => nodeEl.removeEventListener('click', handler);
  }, [html, navigate]);

  // Caminho HTML: conteúdo TipTap ou markdown convertido
  if (useHtmlPath) {
    const Tag = inline ? 'span' : 'div';
    return (
      <Tag
        ref={ref}
        className={`rich-content ${className}`}
        dangerouslySetInnerHTML={{ __html: renderedHtml }}
      />
    );
  }

  // Caminho plain text: texto puro sem formatação (sem markdown detectado)
  if (!html) return null;
  const valid = new Set((researchers || []).map(r => slugify(r.nome)));
  const parts = html.split(/(@[a-zA-Z0-9_-]+)/g);
  const content = parts.map((part, i) => {
    if (part.startsWith('@') && valid.has(part.slice(1))) {
      return (
        <span
          key={i}
          onClick={() => navigate(`/app/profile/${part.slice(1)}`)}
          className="inline-flex items-center rounded bg-blue-100 px-1 py-0.5 text-[11px] font-semibold text-blue-700 leading-tight hover:bg-blue-200 cursor-pointer"
        >
          {part}
        </span>
      );
    }
    return <React.Fragment key={i}>{part}</React.Fragment>;
  });
  const Tag2 = inline ? 'span' : 'p';
  return <Tag2 ref={ref} className={`whitespace-pre-wrap ${className}`}>{content}</Tag2>;
}
