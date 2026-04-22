import React, { useEffect, useState } from 'react'
import { api } from '../api.js'

const CATS = ['','Informatique','Fournitures de bureau','Mobilier','Electronique',
              'Hygiene et Entretien','Logiciels','Emballage','Services','Autre']
const STATUS_MAP = { en_attente:'En attente', valide:'Valide', rejete:'Rejete' }

export default function Historique() {
  const [rows,   setRows]   = useState([])
  const [statut, setStatut] = useState('')
  const [cat,    setCat]    = useState('')
  const [loading,setLoading]= useState(true)
  const [open,   setOpen]   = useState(null)
  const [msg,    setMsg]    = useState(null)

  function load() {
    setLoading(true)
    const p = new URLSearchParams()
    if (statut) p.set('statut', statut)
    if (cat)    p.set('categorie', cat)
    api.listDemandes(p.toString() ? '?'+p : '')
      .then(r => setRows(r))
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  async function downloadPDF(id) {
    try {
      const res  = await api.downloadPDF(id)
      const blob = await res.blob()
      const url  = URL.createObjectURL(blob)
      const a    = document.createElement('a'); a.href=url; a.download=`Fiche_${id}.pdf`; a.click()
    } catch(e) { setMsg({ type:'error', text:e.message }) }
  }

  async function changeStatut(id, s) {
    try {
      await api.updateStatut(id, { statut: s })
      setMsg({ type:'success', text:'Statut mis a jour.' })
      load()
    } catch(e) { setMsg({ type:'error', text:e.message }) }
  }

  async function exportCSV() {
    try {
      const res  = await api.exportCSV()
      const blob = await res.blob()
      const url  = URL.createObjectURL(blob)
      const a    = document.createElement('a'); a.href=url; a.download='historique.csv'; a.click()
    } catch(e) { setMsg({ type:'error', text:e.message }) }
  }

  const nb_val = rows.filter(r=>r.statut==='valide').length
  const nb_att = rows.filter(r=>r.statut==='en_attente').length

  return (
    <>
      <div className="page-header">
        <h1>Historique des Demandes</h1>
        <p>Suivi et gestion de toutes les demandes traitees</p>
      </div>

      {/* Filtres */}
      <div className="flex gap-3 mb-4 items-center">
        <select className="form-select" style={{maxWidth:180}} value={statut} onChange={e=>setStatut(e.target.value)}>
          <option value="">Tous statuts</option>
          <option value="en_attente">En attente</option>
          <option value="valide">Valide</option>
          <option value="rejete">Rejete</option>
        </select>
        <select className="form-select" style={{maxWidth:220}} value={cat} onChange={e=>setCat(e.target.value)}>
          <option value="">Toutes categories</option>
          {CATS.filter(Boolean).map(c=><option key={c}>{c}</option>)}
        </select>
        <button className="btn btn-secondary btn-sm" onClick={load}>Filtrer</button>
        <button className="btn btn-secondary btn-sm" onClick={exportCSV}>Exporter CSV</button>
      </div>

      {/* Métriques */}
      <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:14, marginBottom:24 }}>
        <div className="metric-card"><div className="metric-label">Total</div><div className="metric-value">{rows.length}</div></div>
        <div className="metric-card"><div className="metric-label">Validees</div><div className="metric-value">{nb_val}</div></div>
        <div className="metric-card"><div className="metric-label">En attente</div><div className="metric-value">{nb_att}</div></div>
        <div className="metric-card"><div className="metric-label">Rejetees</div><div className="metric-value">{rows.length-nb_val-nb_att}</div></div>
      </div>

      {msg && <div className={`alert alert-${msg.type} mb-4`}>{msg.text}</div>}

      {loading ? <div className="spinner"/> : (
        <div>
          {rows.length === 0
            ? <div className="alert alert-info">Aucune demande enregistree.</div>
            : rows.map(r => (
              <div key={r.demand_id} className="card mb-4">
                {/* En-tête cliquable */}
                <div
                  className="flex justify-between items-center"
                  style={{ cursor:'pointer' }}
                  onClick={() => setOpen(open===r.demand_id ? null : r.demand_id)}
                >
                  <div>
                    <code style={{ fontSize:12, marginRight:10 }}>{r.demand_id}</code>
                    <strong style={{ fontSize:14 }}>{r.type_produit}</strong>
                    <span className="text-muted text-sm" style={{ marginLeft:10 }}>{r.created_at?.slice(0,16)}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`badge ${r.statut==='valide'?'badge-success':r.statut==='rejete'?'badge-danger':'badge-warning'}`}>
                      {STATUS_MAP[r.statut]||r.statut}
                    </span>
                    <span style={{ color:'var(--muted)', fontSize:18 }}>{open===r.demand_id ? '▲' : '▼'}</span>
                  </div>
                </div>

                {/* Détail */}
                {open===r.demand_id && (
                  <div style={{ marginTop:16 }}>
                    <hr className="divider"/>
                    <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:10, marginBottom:14 }}>
                      {[['Categorie',r.categorie],['Quantite',r.quantite],
                        ['Budget',r.budget_max?`${r.budget_max} DH`:'—'],
                        ['Demandeur',r.demandeur||'—'],['Service',r.service||'—'],
                        ['Traitement',`${r.processing_time}s`],
                      ].map(([l,v])=>(
                        <div key={l}><span className="text-muted text-sm">{l} : </span><strong style={{fontSize:13}}>{v}</strong></div>
                      ))}
                    </div>

                    {r.rag_answer && (
                      <div className="alert alert-success" style={{ whiteSpace:'pre-line', marginBottom:12 }}>
                        {r.rag_answer.slice(0,600)}{r.rag_answer.length>600&&'...'}
                      </div>
                    )}

                    {r.top_suppliers?.length > 0 && (
                      <div style={{ marginBottom:12 }}>
                        <strong style={{ fontSize:13 }}>Fournisseurs selectionnes :</strong>{' '}
                        {r.top_suppliers.map(s=>(
                          <span key={s.rank} className="badge badge-success" style={{ marginRight:4 }}>
                            Rang {s.rank} : {s.supplier_name} ({s.score_percent}%)
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Actions */}
                    <div className="flex gap-3 items-center">
                      <button className="btn btn-secondary btn-sm" onClick={()=>downloadPDF(r.demand_id)}>
                        Fiche PDF
                      </button>
                      <select className="form-select" style={{ width:'auto', padding:'5px 10px', fontSize:12 }}
                        value={r.statut}
                        onChange={e => changeStatut(r.demand_id, e.target.value)}>
                        <option value="en_attente">En attente</option>
                        <option value="valide">Valide</option>
                        <option value="rejete">Rejete</option>
                      </select>
                    </div>
                  </div>
                )}
              </div>
            ))
          }
        </div>
      )}
    </>
  )
}
