/**
 * Human-readable message from FastAPI / Starlette error bodies.
 */
export function formatApiDetail(data) {
  if (!data || typeof data !== 'object') return null;
  const d = data.detail;
  if (typeof d === 'string') return d;
  if (Array.isArray(d)) {
    return d
      .map((item) => {
        if (item && typeof item === 'object' && item.msg) return String(item.msg).replace(/^Value error,\s*/i, '');
        return String(item);
      })
      .filter(Boolean)
      .join(' ');
  }
  if (d && typeof d === 'object' && d.msg) return String(d.msg);
  return null;
}

/**
 * Read response body as JSON; logs and returns {} on failure.
 */
export async function readResponseJson(res, logTag) {
  const text = await res.text();
  if (!text.trim()) return {};
  try {
    return JSON.parse(text);
  } catch (err) {
    console.error(`[${logTag}] JSON inválido`, {
      status: res.status,
      preview: text.slice(0, 400),
      err,
    });
    return { _invalidJson: true };
  }
}
