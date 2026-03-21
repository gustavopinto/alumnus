import React, { useEffect } from 'react';

export default function Toast({ message, onClose }) {
  useEffect(() => {
    const t = setTimeout(onClose, 3000);
    return () => clearTimeout(t);
  }, [message]);

  if (!message) return null;

  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 bg-gray-900 text-white text-sm px-5 py-2.5 rounded-xl shadow-lg flex items-center gap-2 animate-fade-in">
      <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4 text-green-400 shrink-0" viewBox="0 0 20 20" fill="currentColor">
        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
      </svg>
      {message}
    </div>
  );
}
