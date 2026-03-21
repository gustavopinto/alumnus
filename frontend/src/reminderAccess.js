import { getTokenPayload } from './auth';

/** Garante comparação estável (API/JSON pode mandar id como string). */
export function normalizeUserId(v) {
  if (v == null || v === '') return null;
  const n = Number(v);
  return Number.isNaN(n) ? null : n;
}

export function viewerUserId() {
  return normalizeUserId(getTokenPayload()?.sub);
}

/**
 * Nome do autor do lembrete.
 * @param {object} opts - opcional: `viewerName` (ex.: nome de getMe quando o JWT não traz `nome`)
 */
export function creatorDisplayName(reminder, opts = {}) {
  const name = reminder.created_by_name && String(reminder.created_by_name).trim();
  if (name) return name;

  const vid = normalizeUserId(opts.viewerId ?? viewerUserId());
  const creatorId = normalizeUserId(reminder.created_by_id);
  const viewerName =
    (opts.viewerName && String(opts.viewerName).trim())
    || (getTokenPayload()?.nome && String(getTokenPayload().nome).trim())
    || '';

  if (creatorId != null && vid != null && creatorId === vid) {
    return viewerName || 'Você';
  }
  return '—';
}

/** Lembrete criado por outro usuário (você é destinatário). */
export function isReminderFromSomeoneElse(reminder) {
  const vid = viewerUserId();
  const creatorId = normalizeUserId(reminder.created_by_id);
  if (vid == null || creatorId == null) return false;
  return creatorId !== vid;
}

/** Criador remove o próprio; sem criador (legado), só professor. */
export function canDeleteReminder(reminder) {
  const viewerId = viewerUserId();
  if (viewerId == null) return false;
  if (reminder.created_by_id == null) return getTokenPayload()?.role === 'professor';
  return normalizeUserId(reminder.created_by_id) === viewerId;
}
