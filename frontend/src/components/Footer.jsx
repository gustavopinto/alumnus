import React from 'react';

export default function Footer() {
  return (
    <footer className="py-4 text-center text-xs text-gray-400">
      Quer uma funcionalidade?{' '}
      <a
        href="https://github.com/gustavopinto/alumnus"
        target="_blank"
        rel="noreferrer"
        className="text-blue-500 hover:underline"
      >
        Abra uma issue no GitHub
      </a>
    </footer>
  );
}
