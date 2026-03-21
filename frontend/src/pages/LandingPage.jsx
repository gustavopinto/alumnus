import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';

/* ── Fade-in on scroll ────────────────────────────────────────────────── */
function FadeIn({ children, delay = 0, className = '' }) {
  const ref = useRef(null);
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    const obs = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) { setVisible(true); obs.disconnect(); } },
      { threshold: 0.08 },
    );
    if (ref.current) obs.observe(ref.current);
    return () => obs.disconnect();
  }, []);
  return (
    <div
      ref={ref}
      className={className}
      style={{
        opacity: visible ? 1 : 0,
        transform: visible ? 'translateY(0)' : 'translateY(24px)',
        transition: `opacity 0.55s ease ${delay}ms, transform 0.55s ease ${delay}ms`,
      }}
    >
      {children}
    </div>
  );
}

/* ── Graph demo ───────────────────────────────────────────────────────── */
const NODES = [
  { id: 0, x: 210, y: 130, label: 'Prof. Ana',   status: 'Professor',  color: '#7c3aed', r: 28 },
  { id: 1, x: 380, y: 70,  label: 'Dr. Lucas',   status: 'Doutorado',  color: '#16a34a', r: 23 },
  { id: 2, x: 370, y: 215, label: 'Me. Paula',   status: 'Mestrado',   color: '#d97706', r: 23 },
  { id: 3, x: 100, y: 235, label: 'Grad. Teo',   status: 'Graduação',  color: '#2563eb', r: 20 },
  { id: 4, x: 500, y: 145, label: 'Dr. Beto',    status: 'Doutorado',  color: '#16a34a', r: 23 },
  { id: 5, x: 300, y: 285, label: 'Me. Clara',   status: 'Mestrado',   color: '#d97706', r: 20 },
  { id: 6, x: 120, y: 115, label: 'Grad. Rafa',  status: 'Graduação',  color: '#2563eb', r: 19 },
];
const EDGES = [[0,1],[0,2],[0,3],[0,6],[1,4],[2,5],[1,2],[3,5],[6,3]];

function GraphDemo({ compact = false }) {
  const [hovered, setHovered] = useState(null);
  const [pulse, setPulse] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setPulse(p => (p + 1) % NODES.length), 2000);
    return () => clearInterval(id);
  }, []);
  const vb = compact ? '40 30 530 310' : '40 30 530 310';
  return (
    <svg viewBox={vb} className="w-full h-full" style={{ userSelect: 'none' }}>
      <defs>
        <filter id="glow2">
          <feGaussianBlur stdDeviation="3.5" result="blur" />
          <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
        <filter id="shadow2" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="2" stdDeviation="3" floodOpacity="0.12" />
        </filter>
      </defs>
      {EDGES.map(([a, b], i) => {
        const na = NODES[a], nb = NODES[b];
        const active = hovered === a || hovered === b;
        return (
          <line key={i} x1={na.x} y1={na.y} x2={nb.x} y2={nb.y}
            stroke={active ? '#93c5fd' : '#e2e8f0'}
            strokeWidth={active ? 2.5 : 1.5}
            style={{ transition: 'stroke 0.25s, stroke-width 0.25s' }}
          />
        );
      })}
      {NODES.map(n => {
        const isPulse = pulse === n.id;
        const isHov = hovered === n.id;
        return (
          <g key={n.id} onMouseEnter={() => setHovered(n.id)} onMouseLeave={() => setHovered(null)}
            style={{ cursor: 'pointer' }}>
            {isPulse && (
              <circle cx={n.x} cy={n.y} r={n.r + 14} fill={n.color} opacity="0.12"
                style={{ animation: 'lpulse 1.6s ease-out forwards' }} />
            )}
            <circle cx={n.x} cy={n.y} r={isHov ? n.r + 4 : n.r}
              fill={n.color} filter={isHov ? 'url(#glow2)' : 'url(#shadow2)'}
              style={{ transition: 'r 0.2s' }} />
            {isHov && (
              <circle cx={n.x} cy={n.y} r={n.r + 7} fill="none"
                stroke={n.color} strokeWidth="1.5" opacity="0.4" strokeDasharray="4 3" />
            )}
            <text x={n.x} y={n.y + 4} textAnchor="middle"
              fontSize="9.5" fill="white" fontFamily="system-ui, sans-serif" fontWeight="700">
              {n.label.charAt(0)}
            </text>
            <text x={n.x} y={n.y + n.r + 14} textAnchor="middle"
              fontSize="10" fill="#475569" fontFamily="system-ui, sans-serif" fontWeight="600">
              {n.label}
            </text>
          </g>
        );
      })}
      <style>{`@keyframes lpulse { 0%{opacity:.3} 100%{opacity:0;r:${42}} }`}</style>
    </svg>
  );
}

/* ── Status badge ─────────────────────────────────────────────────────── */
function StatusBadge({ label, color }) {
  return (
    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold text-white"
      style={{ backgroundColor: color }}>
      <span className="w-1.5 h-1.5 rounded-full bg-white/60" />
      {label}
    </span>
  );
}

/* ── Section heading ──────────────────────────────────────────────────── */
function SectionHeading({ eyebrow, title, subtitle, light = false }) {
  return (
    <FadeIn>
      <div className="text-center mb-12 max-w-2xl mx-auto">
        {eyebrow && (
          <p className={`text-xs font-bold uppercase tracking-widest mb-2 ${light ? 'text-blue-300' : 'text-blue-600'}`}>
            {eyebrow}
          </p>
        )}
        <h2 className={`text-2xl md:text-3xl font-extrabold mb-3 leading-tight ${light ? 'text-white' : 'text-gray-900'}`}>
          {title}
        </h2>
        {subtitle && (
          <p className={`text-sm leading-relaxed ${light ? 'text-slate-300' : 'text-gray-500'}`}>{subtitle}</p>
        )}
      </div>
    </FadeIn>
  );
}

/* ── Feature block ────────────────────────────────────────────────────── */
function FeatureBlock({ icon, title, items, delay }) {
  return (
    <FadeIn delay={delay}
      className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 hover:shadow-md transition-shadow">
      <div className="w-10 h-10 rounded-xl flex items-center justify-center text-lg mb-4 bg-blue-50 text-blue-600">
        {icon}
      </div>
      <h3 className="font-bold text-gray-900 mb-3">{title}</h3>
      <ul className="space-y-1.5">
        {items.map((item, i) => (
          <li key={i} className="flex items-start gap-2 text-sm text-gray-500">
            <svg className="w-3.5 h-3.5 mt-0.5 shrink-0 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
            </svg>
            {item}
          </li>
        ))}
      </ul>
    </FadeIn>
  );
}

/* ── Code-style endpoint ──────────────────────────────────────────────── */
function Endpoint({ method, path, desc }) {
  const colors = {
    GET:    'bg-emerald-100 text-emerald-700',
    POST:   'bg-blue-100 text-blue-700',
    PUT:    'bg-amber-100 text-amber-700',
    DELETE: 'bg-red-100 text-red-700',
  };
  return (
    <div className="flex items-start gap-3 py-2.5 border-b border-slate-700/40 last:border-0">
      <span className={`shrink-0 text-[10px] font-bold px-1.5 py-0.5 rounded font-mono ${colors[method]}`}>
        {method}
      </span>
      <code className="text-slate-300 text-xs font-mono flex-1 min-w-0 truncate">{path}</code>
      <span className="text-slate-500 text-xs shrink-0 hidden sm:block">{desc}</span>
    </div>
  );
}

/* ── Main component ───────────────────────────────────────────────────── */
export default function LandingPage() {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <div className="min-h-screen bg-white font-sans antialiased">

      {/* ════════════════════════════════════════════
          NAVBAR
      ════════════════════════════════════════════ */}
      <nav className="sticky top-0 z-50 bg-white/90 backdrop-blur border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
          {/* Logo */}
          <div className="flex items-center gap-2 shrink-0">
            <div className="w-7 h-7 rounded-lg bg-blue-600 flex items-center justify-center">
              <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5}
                  d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </div>
            <span className="font-bold text-blue-700 text-lg">Alumnus</span>
          </div>
          {/* Desktop nav */}
          <div className="hidden md:flex items-center gap-5 text-sm text-gray-600">
            <a href="#problema"       className="hover:text-blue-600 transition-colors">Problema</a>
            <a href="#funcionalidades" className="hover:text-blue-600 transition-colors">Funcionalidades</a>
            <a href="#pricing"        className="hover:text-blue-600 transition-colors">Preços</a>
          </div>
          <div className="hidden md:flex items-center gap-2">
            <Link to="/login"
              className="text-sm text-gray-600 hover:text-blue-600 px-3 py-1.5 rounded-lg transition-colors">
              Entrar
            </Link>
            <Link to="/register"
              className="text-sm bg-blue-600 text-white px-4 py-1.5 rounded-lg hover:bg-blue-700 transition-colors font-medium">
              Começar agora
            </Link>
          </div>
          {/* Mobile toggle */}
          <button className="md:hidden p-2 rounded-lg hover:bg-gray-100"
            onClick={() => setMenuOpen(o => !o)} aria-label="Menu">
            <svg className="w-5 h-5 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              {menuOpen
                ? <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                : <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />}
            </svg>
          </button>
        </div>
        {menuOpen && (
          <div className="md:hidden border-t bg-white px-4 py-3 space-y-1 text-sm">
            {['problema','funcionalidades','pricing'].map(s => (
              <a key={s} href={`#${s}`}
                className="block py-2 px-2 rounded-lg text-gray-600 hover:bg-gray-50 capitalize"
                onClick={() => setMenuOpen(false)}>
                {s.charAt(0).toUpperCase() + s.slice(1)}
              </a>
            ))}
            <div className="pt-2 border-t flex flex-col gap-2 mt-2">
              <Link to="/login" className="block text-center py-2 border rounded-lg text-gray-700">Entrar</Link>
              <Link to="/register" className="block text-center py-2 bg-blue-600 text-white rounded-lg font-medium">Começar agora</Link>
            </div>
          </div>
        )}
      </nav>

      {/* ════════════════════════════════════════════
          HERO
      ════════════════════════════════════════════ */}
      <section className="relative overflow-hidden bg-gradient-to-br from-slate-950 via-blue-950 to-slate-900 pt-16 pb-24 md:pt-24 md:pb-32">
        {/* Background texture */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-0 left-1/4 w-96 h-96 rounded-full bg-blue-600/10 blur-3xl" />
          <div className="absolute bottom-0 right-1/4 w-80 h-80 rounded-full bg-purple-600/10 blur-3xl" />
        </div>

        <div className="relative max-w-6xl mx-auto px-4">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            {/* Left: text */}
            <div>
              <FadeIn delay={0}>
                <div className="inline-flex items-center gap-2 bg-blue-500/10 border border-blue-500/20 rounded-full px-3 py-1 text-xs text-blue-300 font-medium mb-5">
                  <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
                  Gestão de Grupos de Pesquisa
                </div>
                <h1 className="text-3xl md:text-4xl lg:text-5xl font-extrabold text-white leading-tight mb-4">
                  Gerencie seu grupo de pesquisa como um{' '}
                  <span className="text-blue-400">grafo interativo</span>
                </h1>
                <p className="text-slate-300 text-base leading-relaxed mb-8 max-w-lg">
                  Visualize pesquisadores, acompanhe relações, registre reuniões,
                  organize trabalhos e mantenha lembretes e prazos em um só lugar.
                </p>
                {/* Bullets */}
                <ul className="space-y-2.5 mb-8">
                  {[
                    ['🗺️', 'Grafo interativo do grupo com drag, zoom e pan'],
                    ['👤', 'Perfis individuais com notas, trabalhos e links'],
                    ['🔔', 'Lembretes e deadlines de conferências'],
                    ['🔐', 'Login com papéis distintos para professores e alunos'],
                  ].map(([icon, text]) => (
                    <li key={text} className="flex items-center gap-2.5 text-sm text-slate-300">
                      <span className="text-base">{icon}</span>
                      {text}
                    </li>
                  ))}
                </ul>
                {/* CTAs */}
                <div className="flex flex-wrap gap-3">
                  <Link to="/register"
                    className="bg-blue-500 hover:bg-blue-400 text-white px-6 py-2.5 rounded-xl font-semibold text-sm transition-colors shadow-lg shadow-blue-500/20">
                    Começar agora
                  </Link>
                  <a href="#funcionalidades"
                    className="text-slate-400 hover:text-slate-200 px-4 py-2.5 text-sm transition-colors">
                    Ver funcionalidades ↓
                  </a>
                </div>
              </FadeIn>
            </div>

            {/* Right: graph demo */}
            <FadeIn delay={150} className="relative">
              <div className="bg-slate-800/60 border border-slate-700/60 rounded-2xl overflow-hidden shadow-2xl h-72 md:h-80">
                {/* Window chrome */}
                <div className="flex items-center gap-1.5 px-4 py-2.5 border-b border-slate-700/60 bg-slate-800/80">
                  <div className="w-3 h-3 rounded-full bg-red-500/70" />
                  <div className="w-3 h-3 rounded-full bg-yellow-500/70" />
                  <div className="w-3 h-3 rounded-full bg-green-500/70" />
                  <span className="ml-2 text-slate-500 text-xs font-mono">alumnus — grupo de pesquisa</span>
                </div>
                <div className="h-[calc(100%-2.5rem)] bg-slate-900/40">
                  <GraphDemo />
                </div>
              </div>
              {/* Floating status badges */}
              <div className="absolute -bottom-3 left-4 flex flex-wrap gap-1.5">
                <StatusBadge label="Professor"  color="#7c3aed" />
                <StatusBadge label="Doutorado"  color="#16a34a" />
                <StatusBadge label="Mestrado"   color="#d97706" />
                <StatusBadge label="Graduação"  color="#2563eb" />
              </div>
            </FadeIn>
          </div>
        </div>
      </section>

      {/* ════════════════════════════════════════════
          PROBLEMA
      ════════════════════════════════════════════ */}
      <section id="problema" className="py-20 bg-gray-50">
        <div className="max-w-5xl mx-auto px-4">
          <SectionHeading
            eyebrow="O desafio"
            title="Seu grupo cresce, mas a gestão continua espalhada"
            subtitle="Professores orientadores acumulam informações em e-mails, planilhas e cadernos — sem visibilidade clara do grupo como um todo."
          />
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {[
              { icon: '📋', title: 'Dados dispersos', desc: 'Informações de cada aluno espalhadas por e-mail, planilhas e anotações pessoais.' },
              { icon: '🗒️', title: 'Reuniões e notas perdidas', desc: 'Histórico de reuniões, decisões e próximos passos sem registro centralizado.' },
              { icon: '🔗', title: 'Relações invisíveis', desc: 'As conexões entre pesquisadores, co-autorias e projetos compartilhados ficam implícitas.' },
              { icon: '📚', title: 'Produção desorganizada', desc: 'Artigos, projetos e publicações de cada membro sem uma visão consolidada.' },
              { icon: '⏰', title: 'Prazos manuais', desc: 'Deadlines de conferências e lembretes de orientações controlados de forma manual.' },
              { icon: '👁️', title: 'Sem visão do grupo', desc: 'Impossível enxergar de um só lugar quem está em qual estágio e o que está produzindo.' },
            ].map(({ icon, title, desc }, i) => (
              <FadeIn key={i} delay={i * 60}
                className="bg-white rounded-xl border border-gray-100 shadow-sm p-5 hover:shadow-md transition-shadow">
                <span className="text-2xl mb-3 block">{icon}</span>
                <h3 className="font-bold text-gray-900 mb-1.5 text-sm">{title}</h3>
                <p className="text-xs text-gray-500 leading-relaxed">{desc}</p>
              </FadeIn>
            ))}
          </div>
        </div>
      </section>

      {/* ════════════════════════════════════════════
          SOLUÇÃO
      ════════════════════════════════════════════ */}
      <section className="py-20 bg-white">
        <div className="max-w-5xl mx-auto px-4">
          <SectionHeading
            eyebrow="A solução"
            title="Uma visão estruturada do seu grupo de pesquisa"
          />
          <div className="grid md:grid-cols-2 gap-10 items-center">
            {/* Graph preview */}
            <FadeIn delay={0}>
              <div className="bg-slate-50 border border-gray-200 rounded-2xl overflow-hidden h-64 md:h-72 shadow-sm">
                <GraphDemo />
              </div>
              {/* Legend */}
              <div className="mt-4 flex flex-wrap gap-2 justify-center">
                {[
                  { label: 'Professor',  color: '#7c3aed' },
                  { label: 'Doutorado',  color: '#16a34a' },
                  { label: 'Mestrado',   color: '#d97706' },
                  { label: 'Graduação',  color: '#2563eb' },
                ].map(({ label, color }) => (
                  <div key={label} className="flex items-center gap-1.5 text-xs text-gray-600">
                    <span className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: color }} />
                    {label}
                  </div>
                ))}
              </div>
            </FadeIn>
            {/* Text */}
            <FadeIn delay={100}>
              <p className="text-gray-600 leading-relaxed mb-6">
                O Alumnus reúne em um único ambiente o mapa do grupo, os perfis dos pesquisadores,
                notas de reuniões, histórico de trabalhos, lembretes e prazos.
              </p>
              <p className="text-gray-600 leading-relaxed mb-8">
                Professores acessam a visão completa do grupo e gerenciam todos os pesquisadores.
                Pesquisadores acessam seu próprio perfil com notas, trabalhos e lembretes associados.
              </p>
              <ul className="space-y-3">
                {[
                  'Cada pesquisador é um nó no grafo',
                  'Relações entre pesquisadores são arestas visuais',
                  'Clicar em um nó abre o perfil completo',
                  'Layout do grafo persiste entre sessões',
                ].map((item, i) => (
                  <li key={i} className="flex items-center gap-2.5 text-sm text-gray-700">
                    <div className="w-5 h-5 rounded-full bg-blue-100 flex items-center justify-center shrink-0">
                      <svg className="w-3 h-3 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                      </svg>
                    </div>
                    {item}
                  </li>
                ))}
              </ul>
            </FadeIn>
          </div>
        </div>
      </section>

      {/* ════════════════════════════════════════════
          COMO FUNCIONA
      ════════════════════════════════════════════ */}
      <section className="py-20 bg-blue-600">
        <div className="max-w-4xl mx-auto px-4">
          <SectionHeading
            eyebrow="Fluxo de uso"
            title="Três passos para organizar seu grupo"
            light
          />
          <div className="grid md:grid-cols-3 gap-6">
            {[
              {
                step: '01',
                title: 'Cadastre o grupo',
                desc: 'Adicione pesquisadores com nome, status, links e interesses. Defina conexões entre eles.',
                icon: '👥',
              },
              {
                step: '02',
                title: 'Navegue pelo grafo',
                desc: 'Arraste nós, reorganize o layout e explore as relações do grupo de forma visual.',
                icon: '🗺️',
              },
              {
                step: '03',
                title: 'Acompanhe o trabalho',
                desc: 'Abra perfis, registre reuniões com anexos, gerencie trabalhos e consulte lembretes.',
                icon: '📊',
              },
            ].map(({ step, title, desc, icon }, i) => (
              <FadeIn key={i} delay={i * 100}>
                <div className="relative bg-blue-500/30 border border-blue-400/30 rounded-2xl p-6">
                  <div className="text-3xl mb-3">{icon}</div>
                  <span className="text-blue-300 text-xs font-mono font-bold">{step}</span>
                  <h3 className="font-bold text-white mt-1 mb-2">{title}</h3>
                  <p className="text-blue-100 text-sm leading-relaxed">{desc}</p>
                  {i < 2 && (
                    <div className="hidden md:block absolute top-1/2 -right-3 -translate-y-1/2 text-blue-400 text-xl z-10">→</div>
                  )}
                </div>
              </FadeIn>
            ))}
          </div>
        </div>
      </section>

      {/* ════════════════════════════════════════════
          FUNCIONALIDADES
      ════════════════════════════════════════════ */}
      <section id="funcionalidades" className="py-20 bg-white">
        <div className="max-w-6xl mx-auto px-4">
          <SectionHeading
            eyebrow="Recursos"
            title="Funcionalidades do produto"
            subtitle="Tudo que um grupo de pesquisa ativo precisa, em um único sistema."
          />
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
            <FeatureBlock delay={0} icon="🗺️" title="Grafo interativo"
              items={['Arrastar e reposicionar nós', 'Zoom e pan do canvas', 'Persistência do layout por sessão', 'Cores por status do pesquisador']} />
            <FeatureBlock delay={80} icon="👤" title="Perfis de pesquisadores"
              items={['Links sociais e WhatsApp', 'Interesses de pesquisa', 'Notas de reuniões com anexos', 'Foto de perfil com compressão']} />
            <FeatureBlock delay={160} icon="📄" title="Histórico de trabalhos"
              items={['Projetos em andamento', 'Artigos em preparação', 'Publicações concluídas', 'Registro por pesquisador']} />
            <FeatureBlock delay={0} icon="🔔" title="Lembretes e deadlines"
              items={['Lembretes com datas de vencimento', 'Separação de vencidos e futuros', 'Deadlines de conferências no sidebar', 'Download automático de prazos por URL']} />
            <FeatureBlock delay={80} icon="🔐" title="Controle por papéis"
              items={['Professor gerencia o grupo completo', 'Pesquisador acessa seu próprio perfil', 'Admin com dashboard de usuários', 'Autenticação JWT segura']} />
            <FeatureBlock delay={160} icon="⚙️" title="Infraestrutura pronta"
              items={['Upload com validação e limite de 5 MB', 'Imagens comprimidas automaticamente', 'Migrações SQL versionadas', 'Startup via dev.sh com Docker Compose']} />
          </div>
        </div>
      </section>

      {/* ════════════════════════════════════════════
          DIFERENCIAIS
      ════════════════════════════════════════════ */}
      <section className="py-20 bg-slate-50">
        <div className="max-w-5xl mx-auto px-4">
          <SectionHeading
            eyebrow="Por que Alumnus"
            title="Diferenciais do produto"
            subtitle="Ao contrário de planilhas ou anotações isoladas, o Alumnus conecta estrutura, perfis, interações e produção em uma interface única."
          />
          <div className="grid sm:grid-cols-2 gap-5">
            {[
              { icon: '🔗', title: 'Visualização relacional', desc: 'O grafo torna visível o que antes estava implícito — quem orienta quem, quais projetos são compartilhados, como o grupo se organiza.' },
              { icon: '🎓', title: 'Foco em orientação', desc: 'Criado especificamente para o contexto acadêmico de orientadores com múltiplos alunos em estágios diferentes.' },
              { icon: '📂', title: 'Dados acadêmicos e operacionais no mesmo fluxo', desc: 'Perfis, reuniões, publicações, lembretes e prazos de conferências na mesma plataforma, sem alternar ferramentas.' },
              { icon: '👁️', title: 'Acesso diferenciado por papel', desc: 'Professor vê o todo. Pesquisador vê o próprio perfil. Cada um acessa exatamente o que precisa.' },
              { icon: '📐', title: 'Arquitetura pronta para evoluir', desc: 'Separação clara entre routers e services, migrações versionadas, upload com validação — base sólida para crescimento.' },
              { icon: '🐳', title: 'Roda localmente com um comando', desc: 'Frontend, backend e banco isolados em Docker Compose. Um único script inicia e configura todo o ambiente.' },
            ].map(({ icon, title, desc }, i) => (
              <FadeIn key={i} delay={i * 70}
                className="flex gap-4 bg-white rounded-xl border border-gray-100 shadow-sm p-5">
                <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center text-xl shrink-0">
                  {icon}
                </div>
                <div>
                  <h3 className="font-bold text-gray-900 text-sm mb-1">{title}</h3>
                  <p className="text-xs text-gray-500 leading-relaxed">{desc}</p>
                </div>
              </FadeIn>
            ))}
          </div>
        </div>
      </section>

      {/* ════════════════════════════════════════════
          LEGENDA DE STATUS
      ════════════════════════════════════════════ */}
      <section className="py-12 bg-white border-y border-gray-100">
        <div className="max-w-4xl mx-auto px-4">
          <FadeIn>
            <p className="text-center text-xs font-bold uppercase tracking-widest text-gray-400 mb-6">
              Legenda visual do grafo
            </p>
            <div className="flex flex-wrap justify-center gap-6">
              {[
                { label: 'Professor',  color: '#7c3aed', desc: 'Orientador, visualiza e gerencia o grupo completo' },
                { label: 'Doutorado',  color: '#16a34a', desc: 'Estudante de pós-graduação (PhD)' },
                { label: 'Mestrado',   color: '#d97706', desc: 'Estudante de pós-graduação (MSc)' },
                { label: 'Graduação',  color: '#2563eb', desc: 'Estudante de graduação (IC, TCC)' },
              ].map(({ label, color, desc }) => (
                <div key={label} className="flex flex-col items-center gap-2 text-center max-w-[130px]">
                  <div className="w-10 h-10 rounded-full border-4 border-white shadow"
                    style={{ backgroundColor: color }} />
                  <span className="text-sm font-bold text-gray-800">{label}</span>
                  <span className="text-xs text-gray-400 leading-tight">{desc}</span>
                </div>
              ))}
            </div>
          </FadeIn>
        </div>
      </section>

      {/* ════════════════════════════════════════════
          PRICING
      ════════════════════════════════════════════ */}
      <section id="pricing" className="py-20 bg-white">
        <div className="max-w-5xl mx-auto px-4">
          <SectionHeading
            eyebrow="Preços"
            title="Planos simples e transparentes"
            subtitle="30 dias de trial grátis em qualquer plano. Sem cartão de crédito."
          />
          <div className="grid sm:grid-cols-3 gap-6 items-start">
            {/* Trial */}
            <FadeIn delay={0} className="flex flex-col rounded-2xl p-7 border border-dashed border-gray-300 bg-gray-50 hover:shadow-lg transition-shadow">
              <p className="text-xs font-bold uppercase tracking-wider text-gray-500 mb-1">Trial</p>
              <div className="flex items-end gap-1 mb-1">
                <span className="text-4xl font-extrabold text-gray-900">Grátis</span>
              </div>
              <p className="text-xs text-gray-400 mb-6">30 dias · sem cartão de crédito</p>
              <ul className="space-y-2.5 flex-1 mb-6">
                {['Até 10 pesquisadores','Grafo interativo','Perfis e reuniões','Lembretes básicos','Suporte por e-mail'].map(f => (
                  <li key={f} className="flex items-start gap-2 text-sm text-gray-600">
                    <svg className="w-4 h-4 mt-0.5 shrink-0 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                    </svg>
                    {f}
                  </li>
                ))}
              </ul>
              <Link to="/register" className="text-center py-2.5 px-4 rounded-xl text-sm font-semibold border border-gray-300 text-gray-700 hover:bg-white hover:border-gray-400 transition-colors">
                Começar trial
              </Link>
            </FadeIn>

            {/* Mensal */}
            <FadeIn delay={0} className="flex flex-col rounded-2xl p-7 border border-gray-200 bg-white hover:shadow-lg transition-shadow">
              <p className="text-xs font-bold uppercase tracking-wider text-blue-600 mb-1">Mensal</p>
              <div className="flex items-end gap-1 mb-1">
                <span className="text-sm mt-1 text-gray-400">R$</span>
                <span className="text-4xl font-extrabold text-gray-900">20</span>
                <span className="text-sm mb-1 text-gray-400">/mês</span>
              </div>
              <p className="text-xs text-gray-400 mb-6">Cobrado mensalmente · cancele quando quiser</p>
              <ul className="space-y-2.5 flex-1 mb-6">
                {['Pesquisadores ilimitados','Grafo interativo','Perfis e reuniões','Lembretes e deadlines','Mural colaborativo','Suporte por e-mail'].map(f => (
                  <li key={f} className="flex items-start gap-2 text-sm text-gray-600">
                    <svg className="w-4 h-4 mt-0.5 shrink-0 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                    </svg>
                    {f}
                  </li>
                ))}
              </ul>
              <Link to="/register" className="text-center py-2.5 px-4 rounded-xl text-sm font-semibold bg-blue-600 text-white hover:bg-blue-700 transition-colors">
                Assinar mensalmente
              </Link>
            </FadeIn>

            {/* Anual — destaque */}
            <FadeIn delay={120} className="relative flex flex-col rounded-2xl p-7 border border-blue-600 bg-blue-600 text-white shadow-xl shadow-blue-200 hover:shadow-2xl transition-shadow">
              <span className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full text-xs font-bold bg-white text-blue-600">
                Mais popular
              </span>
              <p className="text-xs font-bold uppercase tracking-wider text-blue-200 mb-1">Anual</p>
              <div className="flex items-end gap-1 mb-1">
                <span className="text-sm mt-1 text-blue-200">R$</span>
                <span className="text-4xl font-extrabold">200</span>
                <span className="text-sm mb-1 text-blue-200">/ano</span>
              </div>
              <p className="text-xs text-blue-200 mb-6">Equivale a R$ 16,67/mês · 2 meses grátis</p>
              <ul className="space-y-2.5 flex-1 mb-6">
                {['Tudo do plano Mensal','Dashboard administrativo','Exportação de dados','Acesso antecipado a novidades','Suporte prioritário'].map(f => (
                  <li key={f} className="flex items-start gap-2 text-sm text-blue-50">
                    <svg className="w-4 h-4 mt-0.5 shrink-0 text-blue-200" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                    </svg>
                    {f}
                  </li>
                ))}
              </ul>
              <Link to="/register" className="text-center py-2.5 px-4 rounded-xl text-sm font-semibold bg-white text-blue-600 hover:bg-blue-50 transition-colors">
                Assinar anualmente
              </Link>
            </FadeIn>

          </div>
        </div>
      </section>

      {/* ════════════════════════════════════════════
          CTA FINAL
      ════════════════════════════════════════════ */}
      <section className="py-24 bg-gradient-to-br from-blue-600 to-blue-700">
        <div className="max-w-2xl mx-auto px-4 text-center">
          <FadeIn>
            <h2 className="text-3xl md:text-4xl font-extrabold text-white mb-4 leading-tight">
              Organize seu grupo de pesquisa com mais contexto e menos dispersão
            </h2>
            <p className="text-blue-100 mb-10 leading-relaxed">
              Visualize pessoas, acompanhe relações e concentre o histórico do grupo em uma única plataforma.
            </p>
            <div className="flex flex-wrap justify-center gap-3">
              <Link to="/register"
                className="bg-white text-blue-600 hover:bg-blue-50 px-7 py-3 rounded-xl font-semibold text-sm transition-colors shadow-md">
                Começar agora
              </Link>
              <Link to="/login"
                className="border border-blue-400/50 hover:border-white/60 text-white px-6 py-3 rounded-xl text-sm transition-colors">
                Fazer login
              </Link>
            </div>
          </FadeIn>
        </div>
      </section>

      {/* ════════════════════════════════════════════
          FOOTER
      ════════════════════════════════════════════ */}
      <footer className="bg-slate-950 border-t border-slate-800 py-10">
        <div className="max-w-5xl mx-auto px-4">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-md bg-blue-600 flex items-center justify-center">
                <svg className="w-3.5 h-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5}
                    d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </div>
              <span className="text-white font-bold">Alumnus</span>
              <span className="text-slate-600 text-xs ml-2">© {new Date().getFullYear()}</span>
            </div>
            <div className="flex items-center gap-5 text-sm">
              <Link to="/login" className="text-slate-500 hover:text-slate-300 transition-colors">
                Entrar
              </Link>
              <Link to="/register" className="text-slate-500 hover:text-slate-300 transition-colors">
                Cadastrar
              </Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
