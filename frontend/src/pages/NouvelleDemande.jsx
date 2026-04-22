import React, { useState, useRef } from 'react'
import { api } from '../api.js'
import { useNavigate } from 'react-router-dom'

const CATS = [
  'Informatique','Fournitures de bureau','Mobilier','Electronique',
  'Hygiene et Entretien','Logiciels','Emballage','Equipements industriels','Services','Autre',
]

const CODE_LABELS = {
  SIGNATURE_MANQUANTE:        'Signature manquante',
  VISA_MANQUANT:              'Visa hierarchique manquant',
  SERVICE_MANQUANT:           'Service emetteur non renseigne',
  PRODUIT_MANQUANT:           'Designation du produit absente',
  DEPASSEMENT_BUDGET_CRITIQUE:'Depassement de budget critique (> 20%)',
  DEPASSEMENT_BUDGET_MINEUR:  'Depassement de budget mineur (<= 20%)',
  QUANTITE_INVALIDE:          'Quantite invalide',
  DATE_MANQUANTE:             'Date de la demande non renseignee',
}

// ─── Rapport de conformite ────────────────────────────────────────────────────

function RapportConformite({ rapport, onCorrige, labelCorrection = 'Corriger la demande' }) {
  const { problemes = [], avertissements = [], conforme, message_global, date_verification } = rapport
  return (
    <div style={{
      border:`2px solid ${conforme?'var(--main)':'#dc2626'}`,
      borderRadius:8, overflow:'hidden', marginBottom:24,
    }}>
      <div style={{
        background:conforme?'var(--dark)':'#dc2626', color:'white',
        padding:'14px 20px', display:'flex', justifyContent:'space-between', alignItems:'center',
      }}>
        <div>
          <div style={{fontWeight:700,fontSize:15}}>
            {conforme ? 'Demande conforme — Analyse autorisee' : 'Demande non conforme — Analyse bloquee'}
          </div>
          <div style={{fontSize:12,opacity:0.85,marginTop:2}}>
            Verification effectuee le {date_verification}
          </div>
        </div>
        <div style={{
          background:'rgba(255,255,255,0.2)', borderRadius:6,
          padding:'6px 14px', fontWeight:700, fontSize:14,
        }}>
          {conforme ? 'CONFORME' : 'NON CONFORME'}
        </div>
      </div>

      <div style={{padding:'16px 20px', background:'var(--white)'}}>
        <p style={{marginBottom:12, color:'var(--text)', fontSize:13}}>{message_global}</p>

        {problemes.length > 0 && (
          <div style={{marginBottom:12}}>
            <div style={{fontWeight:700,fontSize:12,color:'#7f1d1d',textTransform:'uppercase',letterSpacing:'0.5px',marginBottom:8}}>
              Problemes bloquants ({problemes.length})
            </div>
            {problemes.map((p,i) => (
              <div key={i} style={{
                display:'flex',gap:10,alignItems:'flex-start',
                background:'#fef2f2',border:'1px solid #fecaca',
                borderLeft:'4px solid #dc2626',borderRadius:'0 6px 6px 0',
                padding:'10px 14px',marginBottom:6,fontSize:13,
              }}>
                <span style={{color:'#dc2626',fontWeight:700,flexShrink:0}}>✕</span>
                <div>
                  <div style={{fontWeight:600,color:'#7f1d1d',marginBottom:2}}>
                    {CODE_LABELS[p.code]||p.code}
                  </div>
                  <div style={{color:'#991b1b'}}>{p.message}</div>
                  {p.pourcentage!=null && (
                    <div style={{marginTop:4,fontWeight:600,color:'#7f1d1d'}}>
                      Depassement : +{p.pourcentage}% ({p.depassement?.toLocaleString()} DH)
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {avertissements.length > 0 && (
          <div style={{marginBottom:12}}>
            <div style={{fontWeight:700,fontSize:12,color:'#92400e',textTransform:'uppercase',letterSpacing:'0.5px',marginBottom:8}}>
              Avertissements ({avertissements.length})
            </div>
            {avertissements.map((a,i) => (
              <div key={i} style={{
                display:'flex',gap:10,alignItems:'flex-start',
                background:'#fefce8',border:'1px solid #fde68a',
                borderLeft:'4px solid #f59e0b',borderRadius:'0 6px 6px 0',
                padding:'10px 14px',marginBottom:6,fontSize:13,
              }}>
                <span style={{color:'#f59e0b',fontWeight:700,flexShrink:0}}>!</span>
                <div>
                  <div style={{fontWeight:600,color:'#92400e',marginBottom:2}}>
                    {CODE_LABELS[a.code]||a.code}
                  </div>
                  <div style={{color:'#78350f'}}>{a.message}</div>
                  {a.pourcentage!=null && (
                    <div style={{marginTop:4,fontWeight:600}}>
                      Depassement : +{a.pourcentage}% ({a.depassement?.toLocaleString()} DH)
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {conforme && (
          <div style={{
            background:'var(--alt)',border:'1px solid var(--border)',
            borderLeft:'4px solid var(--dark)',borderRadius:'0 6px 6px 0',
            padding:'10px 14px',fontSize:13,color:'var(--text)',
          }}>
            Tous les controles de conformite sont satisfaits. La demande peut etre soumise a l'analyse.
          </div>
        )}

        {!conforme && onCorrige && (
          <button className="btn btn-secondary" style={{marginTop:12}} onClick={onCorrige}>
            {labelCorrection}
          </button>
        )}
      </div>
    </div>
  )
}

// ─── Indicateur d'etapes ──────────────────────────────────────────────────────

function Etapes({ active }) {
  const steps = [
    {n:1, label:'Import PDF'},
    {n:2, label:'Verification conformite'},
    {n:3, label:'Analyse et selection IA'},
  ]
  return (
    <div style={{
      display:'flex', background:'var(--white)',
      border:'1px solid var(--border)', borderRadius:8,
      overflow:'hidden', marginBottom:24,
    }}>
      {steps.map((s,i) => (
        <div key={i} style={{
          flex:1, padding:'13px 16px', fontSize:12, fontWeight:600,
          background: s.n === active ? 'var(--dark)' : 'var(--bg)',
          color: s.n === active ? 'white' : 'var(--muted)',
          borderRight: i<2 ? '1px solid var(--border)' : 'none',
          letterSpacing:'0.3px',
        }}>
          <span style={{
            display:'inline-flex',alignItems:'center',justifyContent:'center',
            width:20,height:20,borderRadius:'50%',
            background: s.n === active ? 'rgba(255,255,255,0.25)' : 'var(--border)',
            color: s.n === active ? 'white' : 'var(--muted)',
            fontSize:11, fontWeight:800, marginRight:8, flexShrink:0,
          }}>{s.n}</span>
          {s.label}
        </div>
      ))}
    </div>
  )
}

// ─── Page principale — Upload PDF uniquement ──────────────────────────────────

export default function NouvelleDemande() {
  const nav     = useNavigate()
  const fileRef = useRef()

  const [file,      setFile]      = useState(null)
  const [step,      setStep]      = useState(1)
  const [extracted, setExtracted] = useState(null)
  const [rapport,   setRapport]   = useState(null)
  const [err,       setErr]       = useState(null)

  const loading = step === 3

  // ── Etape 1 : extraire le PDF et verifier la conformite
  async function handleExtract() {
    if (!file) return
    setErr(null); setStep(3)
    try {
      const res = await api.extractPDF(file)
      setExtracted(res.extracted)
      setRapport(res.rapport_conformite)
      setStep(2)
    } catch(ex) { setErr(ex.message); setStep(1) }
  }

  // ── Modification d'un champ extrait
  const setField = (k,v) => {
    setExtracted(d => ({...d, [k]:v}))
    setRapport(null)
  }

  // ── Re-verifier apres correction
  async function handleReverifier() {
    setErr(null); setStep(3)
    try {
      const r = await api.verifierConformite(extracted)
      setRapport(r); setStep(2)
    } catch(ex) { setErr(ex.message); setStep(2) }
  }

  // ── Etape 2 : soumettre si conforme
  async function handleConfirmer() {
    setErr(null); setStep(3)
    try {
      const result = await api.confirmPDF({
        data:         extracted,
        text_extrait: extracted.text_extrait || '',
        filename:     extracted.filename || file.name,
      })
      if (result.conforme === false) {
        setRapport(result.rapport_conformite); setStep(2); return
      }
      sessionStorage.setItem('last_result', JSON.stringify(result))
      nav('/resultats')
    } catch(ex) { setErr(ex.message); setStep(2) }
  }

  // ── Reset complet
  function handleReset() {
    setFile(null); setExtracted(null)
    setRapport(null); setErr(null); setStep(1)
  }

  return (
    <>
      <div className="page-header">
        <h1>Nouvelle Demande d'Achat</h1>
        <p>Importez votre fiche PDF — le systeme verifie la conformite puis selectionne les fournisseurs.</p>
      </div>

      <Etapes active={step === 2 ? 2 : step === 3 ? 3 : 1} />

      {/* ── Etape 1 : zone de depot ─────────────────────────────────────────── */}
      {step === 1 && (
        <>
          <div className="alert alert-info" style={{marginBottom:16}}>
            Importez votre demande d'achat en PDF. Le systeme extrait automatiquement les champs
            puis effectue la verification de conformite avant de lancer l'analyse.
          </div>
          <div
            className={`dropzone ${file?'active':''}`}
            onClick={() => fileRef.current?.click()}
            onDrop={e => { e.preventDefault(); setFile(e.dataTransfer.files[0]) }}
            onDragOver={e => e.preventDefault()}
          >
            <div style={{fontSize:40, opacity:0.4, marginBottom:10}}>📄</div>
            <div className="dropzone-text">
              {file ? file.name : 'Glissez votre document PDF ici'}
            </div>
            <div className="dropzone-sub">ou cliquez pour parcourir</div>
            <input ref={fileRef} type="file" accept=".pdf" style={{display:'none'}}
              onChange={e => setFile(e.target.files[0])} />
          </div>

          {file && (
            <div style={{marginTop:12}}>
              <div className="alert alert-success" style={{marginBottom:12}}>
                Document recu : <strong>{file.name}</strong> ({(file.size/1024).toFixed(1)} Ko)
              </div>
              <button className="btn btn-primary btn-lg btn-full"
                onClick={handleExtract} disabled={loading}>
                {loading ? 'Extraction en cours...' : 'Extraire et verifier la conformite'}
              </button>
            </div>
          )}
          {err && <div className="alert alert-error mt-4">{err}</div>}
        </>
      )}

      {/* ── Etape 2 : rapport + correction ──────────────────────────────────── */}
      {step === 2 && extracted && (
        <>
          {rapport && (
            <RapportConformite
              rapport={rapport}
              onCorrige={handleReset}
              labelCorrection="Reimporter un autre PDF"
            />
          )}

          {/* Champs extraits modifiables */}
          <div style={{background:'var(--white)',border:'1px solid var(--border)',borderRadius:8,padding:20,marginBottom:16}}>
            <h2 style={{marginBottom:6}}>Champs extraits du PDF</h2>
            <p style={{fontSize:12,color:'var(--muted)',marginBottom:16}}>
              Verifiez et corrigez les informations extraites avant de soumettre.
            </p>

            <div className="form-grid-2">
              <div>
                <div className="form-group">
                  <label className="form-label">
                    Demandeur <span style={{color:'#dc2626'}}>*</span>
                    {!extracted.demandeur && <span style={{color:'#dc2626',marginLeft:6,fontSize:11}}>manquant</span>}
                  </label>
                  <input className="form-input" value={extracted.demandeur||''}
                    onChange={e=>setField('demandeur',e.target.value)}
                    style={!extracted.demandeur?{borderColor:'#fca5a5'}:{}} />
                </div>
                <div className="form-group">
                  <label className="form-label">
                    Visa du responsable <span style={{color:'#dc2626'}}>*</span>
                    {!extracted.responsable && <span style={{color:'#dc2626',marginLeft:6,fontSize:11}}>manquant</span>}
                  </label>
                  <input className="form-input" value={extracted.responsable||''}
                    onChange={e=>setField('responsable',e.target.value)}
                    style={!extracted.responsable?{borderColor:'#fca5a5'}:{}} />
                </div>
                <div className="form-group">
                  <label className="form-label">Service</label>
                  <input className="form-input" value={extracted.service||''}
                    onChange={e=>setField('service',e.target.value)} />
                </div>
                <div className="form-group">
                  <label className="form-label">Date de la demande</label>
                  <input className="form-input" type="date" value={extracted.date_demande||''}
                    onChange={e=>setField('date_demande',e.target.value)} />
                </div>
              </div>
              <div>
                <div className="form-group">
                  <label className="form-label">
                    Produit / Prestation <span style={{color:'#dc2626'}}>*</span>
                  </label>
                  <input className="form-input" value={extracted.type_produit||''}
                    onChange={e=>setField('type_produit',e.target.value)}
                    style={!extracted.type_produit?{borderColor:'#fca5a5'}:{}} />
                </div>
                <div className="form-group">
                  <label className="form-label">Categorie</label>
                  <select className="form-select" value={extracted.categorie||'Autre'}
                    onChange={e=>setField('categorie',e.target.value)}>
                    {CATS.map(c=><option key={c}>{c}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Quantite</label>
                  <input className="form-input" type="number" min="1"
                    value={extracted.quantite||1}
                    onChange={e=>setField('quantite',+e.target.value)} />
                </div>
                <div className="form-grid-2">
                  <div className="form-group">
                    <label className="form-label">Budget alloue (DH)</label>
                    <input className="form-input" type="number" value={extracted.budget_alloue||''}
                      onChange={e=>setField('budget_alloue',e.target.value?+e.target.value:null)} />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Budget demande (DH)</label>
                    <input className="form-input" type="number" value={extracted.budget_max||''}
                      onChange={e=>setField('budget_max',e.target.value?+e.target.value:null)} />
                  </div>
                </div>
                <div className="form-group">
                  <label className="form-label">Delai max (jours)</label>
                  <input className="form-input" type="number"
                    value={extracted.delai_max_jours||''}
                    onChange={e=>setField('delai_max_jours',e.target.value?+e.target.value:null)} />
                </div>
              </div>
            </div>
          </div>

          {err && <div className="alert alert-error mb-4">{err}</div>}

          <div style={{display:'flex', gap:12}}>
            {/* Re-verifier si rapport efface apres correction */}
            {!rapport && (
              <button className="btn btn-secondary" style={{flex:1}}
                onClick={handleReverifier} disabled={loading}>
                {loading ? 'Verification...' : 'Re-verifier la conformite'}
              </button>
            )}

            {/* Non conforme : bouton re-verifier apres corrections */}
            {rapport && !rapport.conforme && (
              <button className="btn btn-secondary" style={{flex:1}}
                onClick={handleReverifier} disabled={loading}>
                {loading ? 'Verification...' : 'Re-verifier apres correction'}
              </button>
            )}

            {/* Conforme : lancer l'analyse */}
            {rapport?.conforme && (
              <button className="btn btn-primary btn-lg" style={{flex:2}}
                onClick={handleConfirmer} disabled={loading}>
                {loading ? 'Analyse en cours...' : "Lancer l'analyse et selectionner les fournisseurs"}
              </button>
            )}
          </div>
        </>
      )}
    </>
  )
}