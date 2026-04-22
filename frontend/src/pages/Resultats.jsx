import React, { useEffect, useState } from 'react'
import { api } from '../api.js'
import { useNavigate } from 'react-router-dom'
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts'

const RANK_COLORS = ['#38761d','#6aa84f','#93c47d']
const RANK_LABELS = ['1er CHOIX','2eme CHOIX','3eme CHOIX']

function ScoreBar({ label, value }) {
  return (
    <div className="progress-row">
      <span className="progress-label">{label}</span>
      <div className="progress-bar">
        <div className="progress-fill" style={{ width: `${Math.round(value*100)}%` }}/>
      </div>
      <span className="progress-pct">{Math.round(value*100)}%</span>
    </div>
  )
}

function SupplierCard({ s, rank }) {
  const color = RANK_COLORS[rank] || '#6aa84f'
  const label = RANK_LABELS[rank] || `Rang ${s.rank}`
  const [open, setOpen] = useState(false)

  return (
    <div className={`supplier-card card-rank-${rank+1}`}>
      <div className="supplier-card-header" style={{ background: color }}>
        <h3>{label} — {s.supplier_name}</h3>
        <div className="score-box" style={{ background:'rgba(255,255,255,0.15)', border:'none', padding:'6px 14px' }}>
          <div className="score-value" style={{ color:'white', fontSize:20 }}>{s.score_percent}%</div>
          <div className="score-label" style={{ color:'rgba(255,255,255,0.8)', fontSize:10 }}>{s.niveau}</div>
        </div>
      </div>
      <div className="supplier-card-body">
        <div className="supplier-info-grid">
          <div className="supplier-info-item">
            <div className="label">Domaine</div><div className="value">{s.category || '—'}</div>
          </div>
          <div className="supplier-info-item">
            <div className="label">Note</div><div className="value">{s.rating || '—'}/5</div>
          </div>
          <div className="supplier-info-item">
            <div className="label">Niveau prix</div><div className="value">{s.price_level || '—'}</div>
          </div>
          <div className="supplier-info-item">
            <div className="label">Delai livraison</div><div className="value">{s.delivery_time_days || '—'} jours</div>
          </div>
          <div className="supplier-info-item">
            <div className="label">MOQ</div><div className="value">{s.minimum_order_quantity || '—'}</div>
          </div>
          <div className="supplier-info-item">
            <div className="label">Localisation</div><div className="value">{s.city || ''} {s.country || '—'}</div>
          </div>
          <div className="supplier-info-item">
            <div className="label">Contact</div><div className="value">{s.contact_person || '—'}</div>
          </div>
          <div className="supplier-info-item">
            <div className="label">Email</div><div className="value">{s.email || '—'}</div>
          </div>
          <div className="supplier-info-item">
            <div className="label">Paiement</div><div className="value">{s.payment_terms || '—'}</div>
          </div>
        </div>

        {s.justification && (
          <div className="justification-box">
            <strong>Justification :</strong> {s.justification}
          </div>
        )}

        <button className="btn btn-secondary btn-sm mt-4" onClick={()=>setOpen(o=>!o)}>
          {open ? 'Masquer' : 'Detail du scoring'}
        </button>

        {open && (
          <div style={{ marginTop:12 }}>
            <ScoreBar label="Correspondance metier (30%)" value={s.s_sem||0} />
            <ScoreBar label="Niveau de prix (20%)"        value={s.s_prix||0} />
            <ScoreBar label="Note fournisseur (20%)"      value={s.s_rating||0} />
            <ScoreBar label="Delai de livraison (15%)"    value={s.s_delai||0} />
            <ScoreBar label="Quantite minimale (10%)"     value={s.s_qte||0} />
            <ScoreBar label="Proximite geographique (5%)" value={s.s_geo||0} />
          </div>
        )}
      </div>
    </div>
  )
}

function RadarComparaison({ top }) {
  if (top.length < 2) return null
  const cats = ['Metier','Prix','Note','Delai','MOQ','Geo']
  const keys  = ['s_sem','s_prix','s_rating','s_delai','s_qte','s_geo']
  const data  = cats.map((c, i) => {
    const row = { subject: c }
    top.forEach(s => { row[s.supplier_name] = Math.round((s[keys[i]]||0)*100) })
    return row
  })
  const colors = ['#38761d','#6aa84f','#93c47d']
  return (
    <div className="chart-container mb-6">
      <h2>Comparaison des fournisseurs</h2>
      <ResponsiveContainer width="100%" height={340}>
        <RadarChart data={data}>
          <PolarGrid stroke="#c8dfc0"/>
          <PolarAngleAxis dataKey="subject" tick={{ fontSize:12, fill:'#5a7a4a' }}/>
          <PolarRadiusAxis angle={90} domain={[0,100]} tick={{ fontSize:10 }}/>
          {top.map((s,i) => (
            <Radar key={s.supplier_name} name={s.supplier_name} dataKey={s.supplier_name}
              stroke={colors[i]} fill={colors[i]} fillOpacity={0.15} />
          ))}
          <Tooltip formatter={v=>`${v}%`}/>
          <Legend/>
        </RadarChart>
      </ResponsiveContainer>
    </div>
  )
}

export default function Resultats() {
  const nav = useNavigate()
  const [result,  setResult]  = useState(null)
  const [loading, setLoading] = useState(false)
  const [comment, setComment] = useState('')
  const [msg,     setMsg]     = useState(null)

  useEffect(() => {
    const saved = sessionStorage.getItem('last_result')
    if (saved) setResult(JSON.parse(saved))
  }, [])

  if (!result) return (
    <div>
      <div className="page-header"><h1>Resultats de la Selection</h1></div>
      <div className="alert alert-info">
        Aucune demande en cours.{' '}
        <button className="btn btn-sm btn-secondary" onClick={()=>nav('/nouvelle-demande')}>
          Soumettre une demande
        </button>
      </div>
    </div>
  )

  const { demand, top_suppliers: top, rag_answer, demand_id, processing_time } = result

  async function downloadPDF() {
    try {
      const res = await api.downloadPDF(demand_id)
      const blob = await res.blob()
      const url  = URL.createObjectURL(blob)
      const a    = document.createElement('a'); a.href=url
      a.download = `Fiche_${demand_id}.pdf`; a.click()
    } catch(e) { setMsg({ type:'error', text:e.message }) }
  }

  async function valider() {
    try {
      await api.updateStatut(demand_id, { statut:'valide', commentaire:comment })
      setMsg({ type:'success', text:'Demande validee et archivee.' })
    } catch(e) { setMsg({ type:'error', text:e.message }) }
  }

  async function rejeter() {
    try {
      await api.updateStatut(demand_id, { statut:'rejete' })
      setMsg({ type:'warning', text:'Demande rejetee.' })
    } catch(e) { setMsg({ type:'error', text:e.message }) }
  }

  return (
    <>
      <div className="page-header">
        <h1>Resultats de la Selection</h1>
        <p>Classement et comparaison des fournisseurs selectionnes</p>
      </div>

      {/* Résumé demande */}
      <details className="card mb-6">
        <summary style={{ cursor:'pointer', fontWeight:600, color:'var(--dark)' }}>
          Consulter le detail de la demande — <code>{demand_id}</code>
        </summary>
        <div style={{ marginTop:12, display:'grid', gridTemplateColumns:'1fr 1fr 1fr', gap:8 }}>
          {[
            ['Produit',     demand?.type_produit],
            ['Categorie',   demand?.categorie],
            ['Quantite',    demand?.quantite],
            ['Budget max',  demand?.budget_max ? `${demand.budget_max} DH` : 'N/A'],
            ['Delai max',   demand?.delai_max_jours ? `${demand.delai_max_jours} j` : 'N/A'],
            ['Demandeur',   demand?.demandeur],
            ['Service',     demand?.service],
            ['Localisation',demand?.localisation],
          ].map(([l,v])=>(
            <div key={l}><span className="text-muted text-sm">{l} : </span><strong style={{ fontSize:13 }}>{v||'—'}</strong></div>
          ))}
        </div>
      </details>

      {/* Métriques */}
      <div style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:14, marginBottom:24 }}>
        <div className="metric-card"><div className="metric-label">Traitement</div><div className="metric-value">{processing_time}s</div></div>
        <div className="metric-card"><div className="metric-label">Selectionnes</div><div className="metric-value">{top?.length||0}</div></div>
        <div className="metric-card"><div className="metric-label">Meilleur score</div><div className="metric-value">{top?.[0]?.score_percent||0}%</div></div>
      </div>

      {!top?.length
        ? <div className="alert alert-warning">Aucun fournisseur eligible. Verifiez que des fournisseurs sont indexes.</div>
        : <>
            <h2>Fournisseurs selectionnes</h2>
            {top.map((s,i) => <SupplierCard key={s.supplier_id||i} s={s} rank={i}/>)}

            <RadarComparaison top={top}/>

            <div className="card mb-6">
              <h2>Synthese de la selection</h2>
              <div className="alert alert-success" style={{ whiteSpace:'pre-line' }}>{rag_answer}</div>
            </div>

            {msg && <div className={`alert alert-${msg.type} mb-4`}>{msg.text}</div>}

            <div className="card">
              <h2>Actions</h2>
              <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr 1fr', gap:14 }}>
                <div>
                  <button className="btn btn-primary btn-full" onClick={downloadPDF}>
                    Generer la fiche PDF
                  </button>
                </div>
                <div>
                  <input className="form-input" style={{ marginBottom:8 }}
                    placeholder="Commentaire (optionnel)"
                    value={comment} onChange={e=>setComment(e.target.value)}/>
                  <button className="btn btn-primary btn-full" onClick={valider}>Valider et archiver</button>
                </div>
                <div style={{ display:'flex', alignItems:'flex-end' }}>
                  <button className="btn btn-danger btn-full" onClick={rejeter}>Rejeter la demande</button>
                </div>
              </div>
            </div>
          </>
      }
    </>
  )
}
