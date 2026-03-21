export const DEADLINES = [
  { label: 'ICSE 2026',           url: 'https://conf.researchr.org/home/icse-2026',                              date: '2026-01-24' },
  { label: 'FSE 2026',            url: 'https://conf.researchr.org/home/fse-2026',                               date: '2026-02-06' },
  { label: 'ASE 2026',            url: 'https://conf.researchr.org/home/ase-2026',                               date: '2026-04-10' },
  { label: 'MSR 2026',            url: 'https://conf.researchr.org/home/msr-2026',                               date: '2026-02-13' },
  { label: 'ISSTA 2026',          url: 'https://conf.researchr.org/home/issta-2026',                             date: '2026-02-07' },
  { label: 'SBES 2026',           url: 'https://cbsoft.sbc.org.br/2026/',                                        date: '2026-05-04' },
  { label: 'SBSI 2026',           url: 'https://sbsi.sbc.org.br/2026/',                                         date: '2025-09-29' },
  { label: 'SBIE 2025',           url: 'https://cbie.sbc.org.br/2025/sbie2/',                                   date: '2025-06-09' },
  { label: 'WASHES 2026',         url: 'https://csbc.sbc.org.br/2026/washes/',                                  date: '2026-03-30' },
  { label: 'WER 2026 – Regular',  url: 'https://organizacaower.github.io/WER2026/es/track-regular.html',        date: '2026-03-31' },
  { label: 'WER 2026 – Industry', url: 'https://organizacaower.github.io/WER2026/es/track-industry.html',       date: '2026-04-13' },
];

export function daysUntil(dateStr) {
  return Math.ceil((new Date(dateStr) - new Date()) / (1000 * 60 * 60 * 24));
}

/** Mesmo critério do backend (`slugify`) e das rotas `/profile/:slug`. */
export function slugify(nome) {
  return (nome || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .toLowerCase().trim().replace(/[^a-z0-9\s-]/g, '').replace(/\s+/g, '-');
}
