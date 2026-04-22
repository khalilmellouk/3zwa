import React, { useEffect, useState } from 'react'
import { api } from '../api.js'

const EXAMPLES = [
  'Quel produit a ete demande en dernier ?',
  'Quel est le budget de la demande la plus recente ?',
  'Quelles conditions particulieres ont ete requises ?',
  'Quel fournisseur a ete retenu pour l\'informatique ?',
]

export default function QA() {
  const [demands,   setDemands]   = useState([])
  const [demandId,  setDemandId]  = useState('')
  const [question,  setQuestion]  = useState('')
  const [answer,    setAnswer]    = useState(null)
  const [loading,   setLoading]   = useState(false)
  const [err,       setErr]       = useState(null)

  useEffect(() => {
    api.listDemandes().then(r => setDemands(r)).catch(()=>{})
  }, [])

  async function handleAsk() {
    if (!question.trim()) return
    setLoading(true); setErr(null); setAnswer(null)
    try {
      const r = await api.qa(question.trim(), demandId || null)
      setAnswer(r.answer)
    } catch(e) { setErr(e.message) }
    finally { setLoading(false) }
  }

  return (
    <>
      <div className="page-header">
        <h1>Q&A Documentaire</h1>
        <p>Posez des questions sur vos demandes d'achat indexees dans le systeme</p>
      </div>

      {/* Périmètre */}
      <div className="card mb-6">
        <div className="form-group">
          <label className="form-label">Perimetre de recherche</label>
          <select className="form-select" value={demandId} onChange={e=>setDemandId(e.target.value)}
            style={{ maxWidth:400 }}>
            <option value="">Toutes les demandes</option>
            {demands.map(d=>(
              <option key={d.demand_id} value={d.demand_id}>
                {d.demand_id} — {d.type_produit}
              </option>
            ))}
          </select>
        </div>

        {/* Questions exemples */}
        <div style={{ marginBottom:16 }}>
          <div className="text-muted text-sm" style={{ marginBottom:8 }}>Questions courantes :</div>
          <div style={{ display:'flex', flexWrap:'wrap', gap:8 }}>
            {EXAMPLES.map(ex => (
              <button key={ex} className="btn btn-secondary btn-sm"
                onClick={()=>setQuestion(ex)}>{ex}</button>
            ))}
          </div>
        </div>

        {/* Input question */}
        <div className="form-group">
          <label className="form-label">Votre question</label>
          <textarea className="form-textarea" rows={3}
            placeholder="Ex : Quels fournisseurs ont ete selectionnes pour l'informatique ?"
            value={question} onChange={e=>setQuestion(e.target.value)}
            onKeyDown={e => e.key==='Enter' && !e.shiftKey && (e.preventDefault(), handleAsk())}
          />
        </div>
        <button className="btn btn-primary btn-lg" onClick={handleAsk}
          disabled={loading || !question.trim()}>
          {loading ? 'Recherche en cours...' : 'Soumettre la question'}
        </button>
      </div>

      {/* Réponse */}
      {err && <div className="alert alert-error mb-4">{err}</div>}

      {answer && (
        <div className="card">
          <h2>Reponse</h2>
          <div className="alert alert-success" style={{ whiteSpace:'pre-line', lineHeight:1.6 }}>
            {answer}
          </div>
          <button className="btn btn-secondary btn-sm mt-4" onClick={()=>setAnswer(null)}>
            Effacer
          </button>
        </div>
      )}

      {demands.length === 0 && (
        <div className="alert alert-warning">
          Aucune demande indexee. Soumettez d'abord une demande depuis la page Nouvelle demande.
        </div>
      )}
    </>
  )
}
