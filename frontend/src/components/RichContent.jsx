import React, { useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { slugify } from '../mentionUtils.jsx';

export default function RichContent({ html = '', researchers = [], className = '', inline = false }) {
  const navigate = useNavigate();
  const ref = useRef();

  const isHtml = typeof html === 'string' && html.includes('<');

  useEffect(() => {
    if (!isHtml || !ref.current) return;
    function handler(e) {
      const el = e.target.closest('[data-type="mention"]');
      if (el) {
        const id = el.getAttribute('data-id');
        if (id) navigate(`/app/profile/${id}`);
      }
    }
    const node = ref.current;
    node.addEventListener('click', handler);
    return () => node.removeEventListener('click', handler);
  }, [html, isHtml, navigate]);

  if (isHtml) {
    const Tag = inline ? 'span' : 'div';
    return (
      <Tag
        ref={ref}
        className={`rich-content ${className}`}
        dangerouslySetInnerHTML={{ __html: html }}
      />
    );
  }

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
    return part;
  });
  const Tag2 = inline ? 'span' : 'p';
  return <Tag2 className={`whitespace-pre-wrap ${className}`}>{content}</Tag2>;
}
