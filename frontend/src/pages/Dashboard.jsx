import React, { useEffect, useState } from 'react'
import { api } from '../api.js'
import { useNavigate } from 'react-router-dom'

const STATUS_LABEL = { en_attente:'En attente', valide:'Valide', rejete:'Rejete' }

export default function Dashboard() {
  const [data,   setData]   = useState(null)
  const [status, setStatus] = useState(null)
  const [err,    setErr]    = useState(null)
  const nav = useNavigate()

  useEffect(() => {
    Promise.all([api.dashboard(), api.status()])
      .then(([d, s]) => { setData(d); setStatus(s) })
      .catch(e => setErr(e.message))
  }, [])

  if (err) return <div className="alert alert-error">{err}</div>
  if (!data) return <div className="loading-center"><div className="spinner"/><span>Chargement...</span></div>

  const metrics = [
    { label: 'Demandes traitees',   value: data.nb_demandes },
    { label: 'Fournisseurs actifs', value: data.nb_fournisseurs },
    { label: 'Demandes validees',   value: data.nb_validees },
    { label: 'En attente',          value: data.nb_en_attente },
    { label: 'Temps moyen (s)',     value: data.temps_moyen },
  ]

  const svcLabels = {
    analyse_documentaire:    "Systeme d'analyse documentaire",
    base_vectorielle:        'Base de connaissances vectorielle',
    similarite_semantique:   'Moteur de similarite semantique',
    extraction_pdf:          'Extraction de documents PDF',
    base_donnees:            'Base de donnees locale',
  }

  return (
    <>
      <div className="page-header">
        <h1>Tableau de bord</h1>
        <p>Vue d'ensemble du systeme de gestion des achats Novec</p>
      </div>

      {/* Métriques */}
      <div className="metrics-grid">
        {metrics.map(m => (
          <div className="metric-card" key={m.label}>
            <div className="metric-label">{m.label}</div>
            <div className="metric-value">{m.value}</div>
          </div>
        ))}
      </div>

      <hr className="divider" />

      {/* Etat des services */}
      <h2>Etat des services</h2>
      <div style={{ display:'flex', flexDirection:'column', gap:8, marginBottom:24 }}>
        {status && Object.entries(status.services).map(([key, ok]) => (
          <div className="status-dot" key={key}>
            <span className={`dot ${ok ? 'dot-ok' : 'dot-err'}`} />
            <span>{svcLabels[key] || key}{!ok && ' (non disponible)'}</span>
          </div>
        ))}
      </div>

      {data.nb_fournisseurs === 0 && (
        <div className="alert alert-warning" style={{ marginBottom:16 }}>
          Aucun fournisseur charge.{' '}
          <button className="btn btn-sm btn-secondary" onClick={() => nav('/fournisseurs')}>
            Importer un CSV
          </button>
        </div>
      )}

      {/* Dernières demandes */}
      {data.recentes?.length > 0 && (
        <>
          <hr className="divider" />
          <h2>Dernieres demandes</h2>
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  {['Reference','Date','Produit','Categorie','Demandeur','Statut'].map(h =>
                    <th key={h}>{h}</th>)}
                </tr>
              </thead>
              <tbody>
                {data.recentes.map(r => (
                  <tr key={r.demand_id} style={{ cursor:'pointer' }}
                      onClick={() => nav('/historique')}>
                    <td><code style={{ fontSize:12 }}>{r.demand_id}</code></td>
                    <td>{r.created_at?.slice(0,16)}</td>
                    <td>{r.type_produit}</td>
                    <td>{r.categorie}</td>
                    <td>{r.demandeur || '—'}</td>
                    <td>
                      <span className={`badge ${
                        r.statut==='valide'     ? 'badge-success' :
                        r.statut==='rejete'     ? 'badge-danger'  :
                        r.statut==='en_attente' ? 'badge-warning' : 'badge-neutral'
                      }`}>{STATUS_LABEL[r.statut] || r.statut}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </>
  )
}
