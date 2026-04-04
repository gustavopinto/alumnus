import React, { useEffect, useCallback, useState } from 'react';

/**
 * Modal de confirmação reutilizável.
 *
 * Uso declarativo (controlado pelo pai):
 *   <ConfirmModal
 *     open={open}
 *     title="Remover leitura?"
 *     description="Esta ação não pode ser desfeita."
 *     confirmLabel="Remover"
 *     onConfirm={handleDelete}
 *     onCancel={() => setOpen(false)}
 *   />
 *
 * Uso imperativo via hook:
 *   const { confirm, ConfirmModal } = useConfirm();
 *   ...
 *   if (await confirm({ title: 'Remover?', description: 'Sem volta.' })) { ... }
 *   ...
 *   return <>{ConfirmModal}</>;
 */

export default function ConfirmModal({
  open,
  title = 'Confirmar ação',
  description = '',
  confirmLabel = 'Confirmar',
  cancelLabel = 'Cancelar',
  variant = 'danger',   // 'danger' | 'warning' | 'default'
  onConfirm,
  onCancel,
}) {
  const handleKey = useCallback((e) => {
    if (!open) return;
    if (e.key === 'Escape') onCancel?.();
    if (e.key === 'Enter')  onConfirm?.();
  }, [open, onCancel, onConfirm]);

  useEffect(() => {
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [handleKey]);

  if (!open) return null;

  const btnCls = {
    danger:  'bg-red-600 hover:bg-red-700 text-white',
    warning: 'bg-amber-500 hover:bg-amber-600 text-white',
    default: 'bg-blue-600 hover:bg-blue-700 text-white',
  }[variant];

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      onClick={onCancel}
    >
      <div
        className="bg-white rounded-xl shadow-xl w-full max-w-sm p-6 space-y-4"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-start gap-3">
          {variant === 'danger' && (
            <div className="shrink-0 w-9 h-9 rounded-full bg-red-100 flex items-center justify-center mt-0.5">
              <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </div>
          )}
          {variant === 'warning' && (
            <div className="shrink-0 w-9 h-9 rounded-full bg-amber-100 flex items-center justify-center mt-0.5">
              <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
              </svg>
            </div>
          )}
          <div className="flex-1 min-w-0">
            <p className="text-base font-semibold text-gray-900">{title}</p>
            {description && (
              <p className="text-sm text-gray-500 mt-1 leading-relaxed">{description}</p>
            )}
          </div>
        </div>

        <div className="flex justify-end gap-3 pt-1">
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors"
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            onClick={onConfirm}
            className={`px-4 py-2 text-sm rounded-lg transition-colors ${btnCls}`}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}

/**
 * Hook imperativo — permite usar await confirm({ ... }) em handlers.
 *
 * Exemplo:
 *   const { confirm, modal } = useConfirm();
 *
 *   async function handleDelete(id) {
 *     if (!await confirm({ title: 'Remover?', description: 'Sem volta.' })) return;
 *     await deleteItem(id);
 *   }
 *
 *   return <>{modal}<div>...</div></>;
 */
export function useConfirm() {
  const [state, setState] = useState(null); // { opts, resolve }

  const confirm = useCallback((opts = {}) => {
    return new Promise((resolve) => {
      setState({ opts, resolve });
    });
  }, []);

  const handleConfirm = useCallback(() => {
    state?.resolve(true);
    setState(null);
  }, [state]);

  const handleCancel = useCallback(() => {
    state?.resolve(false);
    setState(null);
  }, [state]);

  const modal = state ? (
    <ConfirmModal
      open
      {...state.opts}
      onConfirm={handleConfirm}
      onCancel={handleCancel}
    />
  ) : null;

  return { confirm, modal };
}
