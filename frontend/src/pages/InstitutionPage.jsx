import React, { useEffect, useState, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { getMyEmails, addMyEmail, removeMyEmail, getGroups, updateGroup, getInstitutions, createInstitution } from '../api';
import { useAppLayout } from '../components/AppLayout';
import { getTokenPayload } from '../auth';
import { isModEnter } from '../platform';

export default function InstitutionPage() {
  const { refreshInstitutions, setCurrentInstitution } = useAppLayout();
  const payload = getTokenPayload();
  const isSuperadmin = payload?.role === 'superadmin';
  const isProfessor = payload?.role === 'professor' || isSuperadmin;

  const [searchParams] = useSearchParams();
  const instParam = searchParams.get('inst') ? Number(searchParams.get('inst')) : null;

  const [emails, setEmails] = useState([]);
  const [groups, setGroups] = useState([]);
  const [institutions, setInstitutions] = useState([]); // superadmin: all institutions

  const [selectedInstId, setSelectedInstId] = useState(instParam);

  const [newEmail, setNewEmail] = useState('');
  const [emailError, setEmailError] = useState('');
  const [addingEmail, setAddingEmail] = useState(false);

  const [newInstEmail, setNewInstEmail] = useState('');
  const [newInstError, setNewInstError] = useState('');
  const [addingInst, setAddingInst] = useState(false);

  const [editGroupId, setEditGroupId] = useState(null);
  const [editGroupName, setEditGroupName] = useState('');
  const [editGroupError, setEditGroupError] = useState('');

  const load = useCallback(async () => {
    const fetches = [
      getGroups().catch(() => null),
      isSuperadmin ? getInstitutions().catch(() => null) : (isProfessor ? getMyEmails().catch(() => null) : null),
    ];
    const [g, second] = await Promise.all(fetches);
    setGroups(Array.isArray(g) ? g : []);

    if (isSuperadmin) {
      const inst = Array.isArray(second) ? second : [];
      setInstitutions(inst);
      setSelectedInstId(prev => prev || (inst.length > 0 ? inst[0].id : null));
    } else {
      const em = Array.isArray(second) ? second : [];
      setEmails(em);
      setSelectedInstId(prev => prev || (em.length > 0 ? em[0].institution_id : null));
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isSuperadmin, isProfessor]);

  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    if (instParam) setSelectedInstId(instParam);
  }, [instParam]);

  // Professor: institutions derived from their emails
  const myInstitutions = emails.map(e => ({
    id: e.institution_id,
    name: e.institution_name,
    domain: e.institution_domain,
    pi_id: e.id,
    email: e.institutional_email,
  }));

  const instOptions = isSuperadmin ? institutions : myInstitutions;
  const selectedInst = instOptions.find(i => i.id === selectedInstId) || instOptions[0] || null;

  function handleSelectInstitution(inst) {
    setSelectedInstId(inst.id);
    setCurrentInstitution?.({ id: inst.id, name: inst.name });
  }

  // Groups for the selected institution
  const filteredGroups = selectedInstId
    ? groups.filter(g => g.institution_id === selectedInstId)
    : groups;

  async function handleAddEmail(e) {
    e.preventDefault();
    if (!newEmail.trim()) return;
    setAddingEmail(true);
    setEmailError('');
    try {
      const pi = await addMyEmail(newEmail.trim());
      setNewEmail('');
      await load();
      if (pi?.institution_id) {
        setSelectedInstId(pi.institution_id);
        if (refreshInstitutions) refreshInstitutions(pi.institution_id);
      }
    } catch {
      setEmailError('Erro ao adicionar email');
    } finally {
      setAddingEmail(false);
    }
  }

  async function handleRemoveEmail(piId) {
    if (!confirm('Remover este vínculo institucional?')) return;
    try {
      await removeMyEmail(piId);
      await load();
    } catch {
      alert('Mantenha ao menos um email institucional.');
    }
  }

  async function handleCreateInstitution(e) {
    e.preventDefault();
    if (!newInstEmail.trim()) return;
    setAddingInst(true);
    setNewInstError('');
    try {
      const inst = await createInstitution(newInstEmail.trim());
      if (inst?.id) {
        setNewInstEmail('');
        setSelectedInstId(inst.id);
        await load();
        if (refreshInstitutions) refreshInstitutions(inst.id);
      } else {
        setNewInstError(inst?.detail || 'Erro ao criar instituição');
      }
    } catch {
      setNewInstError('Erro ao criar instituição');
    } finally {
      setAddingInst(false);
    }
  }

  async function handleUpdateGroup(e) {
    e.preventDefault();
    if (!editGroupName.trim()) return;
    setEditGroupError('');
    try {
      await updateGroup(editGroupId, { name: editGroupName.trim() });
      setEditGroupId(null);
      await load();
    } catch {
      setEditGroupError('Erro ao salvar');
    }
  }

  // ── Header title ───────────────────────────────────────────────────────────
  function renderTitle() {
    return <h1 className="text-xl font-bold text-gray-800">Instituição</h1>;
  }

  return (
    <div className="max-w-2xl mx-auto p-6 space-y-8">
      {renderTitle()}

      {/* ── Emails / Vínculos institucionais (professor only) ──────── */}
      {!isSuperadmin && isProfessor && (
        <section className="space-y-3">
          <h2 className="text-sm font-semibold text-gray-600 uppercase tracking-wide">Vínculos institucionais</h2>

          {myInstitutions.length === 0 ? (
            <p className="text-sm text-gray-400">Nenhum vínculo registrado.</p>
          ) : (
            <ul className="space-y-2">
              {myInstitutions.map((inst) => (
                <li
                  key={inst.pi_id}
                  className={`flex items-start justify-between border rounded-lg px-4 py-3 shadow-sm cursor-pointer transition-colors ${
                    selectedInstId === inst.id ? 'bg-blue-50 border-blue-200' : 'bg-white hover:bg-gray-50'
                  }`}
                  onClick={() => handleSelectInstitution(inst)}
                >
                  <div>
                    <p className="text-sm font-semibold text-gray-800 uppercase tracking-wide">{inst.name}</p>
                    <p className="text-xs text-gray-400">{inst.email}</p>
                  </div>
                </li>
              ))}
            </ul>
          )}

          <p className="text-sm font-medium text-gray-700">Adicionar nova instituição</p>
          <form onSubmit={handleAddEmail} className="flex gap-2">
            <input
              type="email"
              placeholder="Email institucional (ex: nome@unicamp.br)"
              className="flex-1 border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
              value={newEmail}
              onChange={e => setNewEmail(e.target.value)}
              onKeyDown={e => isModEnter(e) && !addingEmail && handleAddEmail(e)}
            />
            <button
              type="submit"
              disabled={addingEmail}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50"
            >
              Adicionar
            </button>
          </form>
          {emailError && <p className="text-xs text-red-500">{emailError}</p>}
          <p className="text-xs text-gray-400">
            O sistema detecta a instituição automaticamente a partir do domínio do email.
          </p>
        </section>
      )}

      {/* ── Instituições (superadmin) ──────────────────────────────── */}
      {isSuperadmin && (
        <section className="space-y-3">
          <h2 className="text-sm font-semibold text-gray-600 uppercase tracking-wide">Instituições cadastradas</h2>
          {institutions.length > 0 && (
            <ul className="space-y-2">
              {institutions.map((inst) => (
                <li
                  key={inst.id}
                  className={`border rounded-lg px-4 py-3 shadow-sm cursor-pointer transition-colors ${
                    selectedInstId === inst.id ? 'bg-blue-50 border-blue-200' : 'bg-white hover:bg-gray-50'
                  }`}
                  onClick={() => handleSelectInstitution(inst)}
                >
                  <p className="text-sm font-semibold text-gray-800 uppercase tracking-wide">{inst.name}</p>
                  <p className="text-xs text-gray-400">{inst.domain}</p>
                </li>
              ))}
            </ul>
          )}

          <p className="text-sm font-medium text-gray-700">Adicionar nova instituição</p>
          <form onSubmit={handleCreateInstitution} className="flex gap-2">
            <input
              type="email"
              placeholder="Email institucional (ex: nome@unicamp.br)"
              className="flex-1 border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
              value={newInstEmail}
              onChange={e => setNewInstEmail(e.target.value)}
              onKeyDown={e => isModEnter(e) && !addingInst && handleCreateInstitution(e)}
            />
            <button
              type="submit"
              disabled={addingInst}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50 shrink-0"
            >
              Adicionar
            </button>
          </form>
          {newInstError && <p className="text-xs text-red-500">{newInstError}</p>}
          <p className="text-xs text-gray-400">O nome da instituição é extraído automaticamente do domínio do email.</p>
        </section>
      )}

      {/* ── Grupos de pesquisa ────────────────────────────────────── */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-gray-600 uppercase tracking-wide">
            Grupos de pesquisa
            {selectedInst && instOptions.length > 1 && (
              <span className="ml-1 text-blue-600 normal-case font-normal">· {selectedInst.name}</span>
            )}
          </h2>
        </div>

        {filteredGroups.length === 0 ? (
          <p className="text-sm text-gray-400">Nenhum grupo registrado.</p>
        ) : (
          <ul className="space-y-2">
            {filteredGroups.map((g) => (
              <li key={g.id} className="bg-white border rounded-lg px-4 py-3 shadow-sm">
                {editGroupId === g.id ? (
                  <form onSubmit={handleUpdateGroup} className="flex gap-2">
                    <input
                      autoFocus
                      className="flex-1 border rounded px-2 py-1 text-sm"
                      value={editGroupName}
                      onChange={e => setEditGroupName(e.target.value)}
                    />
                    <button type="submit" className="text-xs bg-blue-600 text-white rounded px-2 hover:bg-blue-700">Salvar</button>
                    <button type="button" onClick={() => setEditGroupId(null)} className="text-xs text-gray-400 hover:text-gray-600">✕</button>
                    {editGroupError && <p className="text-xs text-red-500">{editGroupError}</p>}
                  </form>
                ) : (
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-800">{g.name}</p>
                      {g.institution_name && instOptions.length > 1 && (
                        <p className="text-xs text-gray-400">{g.institution_name}</p>
                      )}
                    </div>
                    {isProfessor && (
                      <button
                        onClick={() => { setEditGroupId(g.id); setEditGroupName(g.name); setEditGroupError(''); }}
                        className="text-xs text-blue-400 hover:text-blue-600 ml-4"
                      >
                        Editar
                      </button>
                    )}
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}

      </section>
    </div>
  );
}
