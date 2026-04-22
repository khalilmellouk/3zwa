import React, { useEffect, useState, useRef } from 'react'
import { api } from '../api.js'

const CATS = ['Informatique','Fournitures de bureau','Mobilier','Electronique',
              'Hygiene et Entretien','Logiciels','Emballage','Equipements industriels','Services','Autre']

function TabImport({ onDone }) {
  const [file,    setFile]    = useState(null)
  const [loading, setLoading] = useState(false)
  const [result,  setResult]  = useState(null)
  const [err,     setErr]     = useState(null)
  const fileRef = useRef()

  async function handleImport() {
    if (!file) return
    setLoading(true); setErr(null); setResult(null)
    try {
      const r = await api.importCSV(file)
      setResult(r)
      onDone()
    } catch(e) { setErr(e.message) }
    finally { setLoading(false) }
  }

  async function handleReindex() {
    setLoading(true)
    try { await api.reindexAll(); alert('Reindexation terminee.') }
    catch(e) { setErr(e.message) }
    finally { setLoading(false) }
  }

  return (
    <div>
      <div className="alert alert-info" style={{ marginBottom:16 }}>
        Colonnes attendues : <code>supplier_id, supplier_name, category, description,
        products_sold, price_level, rating, delivery_time_days, minimum_order_quantity,
        country, city, status</code>
      </div>

      <div
        className={`dropzone ${file ? 'active' : ''}`}
        onClick={() => fileRef.current?.click()}
        onDrop={e => { e.preventDefault(); setFile(e.dataTransfer.files[0]) }}
        onDragOver={e => e.preventDefault()}
      >
        <div className="dropzone-icon">📄</div>
        <div className="dropzone-text">{file ? file.name : 'Glissez votre fichier CSV ici'}</div>
        <div className="dropzone-sub">ou cliquez pour parcourir</div>
        <input ref={fileRef} type="file" accept=".csv" style={{ display:'none' }}
          onChange={e => setFile(e.target.files[0])} />
      </div>

      <div className="flex gap-3 mt-4">
        <button className="btn btn-primary btn-lg"
          onClick={handleImport} disabled={!file || loading}>
          {loading ? 'Importation...' : 'Importer et indexer'}
        </button>
        <button className="btn btn-secondary" onClick={handleReindex} disabled={loading}>
          Reindexer tout
        </button>
      </div>

      {result && <div className="alert alert-success mt-4">
        {result.imported} fournisseur(s) importes.{result.errors > 0 && ` ${result.errors} ligne(s) ignorees.`}
      </div>}
      {err && <div className="alert alert-error mt-4">{err}</div>}
    </div>
  )
}

function TabAjouter({ onDone }) {
  const empty = {
    supplier_id:'', supplier_name:'', supplier_type:'Distributeur',
    category:'Informatique', description:'', country:'Maroc', city:'',
    contact_person:'', email:'', phone:'', products_sold:'',
    price_level:'moyen', rating:4.0, delivery_time_days:14,
    minimum_order_quantity:1, payment_terms:'30 jours net', status:'Actif'
  }
  const [form, setForm] = useState(empty)
  const [loading, setLoading] = useState(false)
  const [err, setErr] = useState(null)

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  async function handleSubmit(e) {
    e.preventDefault()
    if (!form.supplier_id || !form.supplier_name) {
      setErr('Identifiant et raison sociale obligatoires.'); return
    }
    setLoading(true); setErr(null)
    try { await api.createSupplier(form); setForm(empty); onDone() }
    catch(e) { setErr(e.message) }
    finally { setLoading(false) }
  }

  return (
    <form onSubmit={handleSubmit}>
      <div className="form-grid-2">
        <div>
          <div className="form-group"><label className="form-label">Identifiant *</label>
            <input className="form-input" value={form.supplier_id} onChange={e=>set('supplier_id',e.target.value)} placeholder="ex: F041"/></div>
          <div className="form-group"><label className="form-label">Raison sociale *</label>
            <input className="form-input" value={form.supplier_name} onChange={e=>set('supplier_name',e.target.value)}/></div>
          <div className="form-group"><label className="form-label">Type</label>
            <select className="form-select" value={form.supplier_type} onChange={e=>set('supplier_type',e.target.value)}>
              {['Fabricant','Distributeur','Grossiste','Prestataire'].map(t=><option key={t}>{t}</option>)}
            </select></div>
          <div className="form-group"><label className="form-label">Domaine</label>
            <select className="form-select" value={form.category} onChange={e=>set('category',e.target.value)}>
              {CATS.map(c=><option key={c}>{c}</option>)}
            </select></div>
          <div className="form-group"><label className="form-label">Description</label>
            <textarea className="form-textarea" value={form.description} onChange={e=>set('description',e.target.value)}/></div>
          <div className="form-group"><label className="form-label">Produits / Services</label>
            <textarea className="form-textarea" rows={2} value={form.products_sold} onChange={e=>set('products_sold',e.target.value)}/></div>
        </div>
        <div>
          <div className="form-group"><label className="form-label">Pays</label>
            <input className="form-input" value={form.country} onChange={e=>set('country',e.target.value)}/></div>
          <div className="form-group"><label className="form-label">Ville</label>
            <input className="form-input" value={form.city} onChange={e=>set('city',e.target.value)}/></div>
          <div className="form-group"><label className="form-label">Contact</label>
            <input className="form-input" value={form.contact_person} onChange={e=>set('contact_person',e.target.value)}/></div>
          <div className="form-group"><label className="form-label">Email</label>
            <input className="form-input" type="email" value={form.email} onChange={e=>set('email',e.target.value)}/></div>
          <div className="form-group"><label className="form-label">Telephone</label>
            <input className="form-input" value={form.phone} onChange={e=>set('phone',e.target.value)}/></div>
          <div className="form-group"><label className="form-label">Niveau de prix</label>
            <select className="form-select" value={form.price_level} onChange={e=>set('price_level',e.target.value)}>
              {['bas','moyen','élevé'].map(p=><option key={p}>{p}</option>)}
            </select></div>
          <div className="form-grid-3">
            <div className="form-group"><label className="form-label">Note</label>
              <input className="form-input" type="number" step="0.1" min="1" max="5" value={form.rating} onChange={e=>set('rating',+e.target.value)}/></div>
            <div className="form-group"><label className="form-label">Delai (j)</label>
              <input className="form-input" type="number" min="1" value={form.delivery_time_days} onChange={e=>set('delivery_time_days',+e.target.value)}/></div>
            <div className="form-group"><label className="form-label">MOQ</label>
              <input className="form-input" type="number" min="1" value={form.minimum_order_quantity} onChange={e=>set('minimum_order_quantity',+e.target.value)}/></div>
          </div>
          <div className="form-group"><label className="form-label">Conditions paiement</label>
            <select className="form-select" value={form.payment_terms} onChange={e=>set('payment_terms',e.target.value)}>
              {['30 jours net','15 jours net','45 jours net','Virement anticipe'].map(p=><option key={p}>{p}</option>)}
            </select></div>
        </div>
      </div>
      {err && <div className="alert alert-error mb-4">{err}</div>}
      <button className="btn btn-primary btn-lg" type="submit" disabled={loading}>
        {loading ? 'Enregistrement...' : 'Enregistrer et indexer'}
      </button>
    </form>
  )
}

function TabListe() {
  const [rows,   setRows]   = useState([])
  const [search, setSearch] = useState('')
  const [cat,    setCat]    = useState('')
  const [loading,setLoading]= useState(true)

  function load() {
    setLoading(true)
    const params = new URLSearchParams()
    if (search) params.set('search', search)
    if (cat)    params.set('category', cat)
    api.listSuppliers(params.toString() ? '?'+params : '')
      .then(r => setRows(r))
      .finally(() => setLoading(false))
  }
  useEffect(load, [])

  return (
    <div>
      <div className="flex gap-3 mb-4 items-center">
        <input className="form-input" style={{ maxWidth:260 }}
          placeholder="Rechercher..." value={search} onChange={e=>setSearch(e.target.value)}
          onKeyDown={e=>e.key==='Enter'&&load()} />
        <select className="form-select" style={{ maxWidth:200 }} value={cat} onChange={e=>setCat(e.target.value)}>
          <option value="">Tous les domaines</option>
          {CATS.map(c=><option key={c}>{c}</option>)}
        </select>
        <button className="btn btn-secondary btn-sm" onClick={load}>Rechercher</button>
        <span className="text-muted">{rows.length} fournisseur(s)</span>
      </div>
      {loading ? <div className="spinner"/> :
      <div className="table-wrapper">
        <table>
          <thead>
            <tr>{['ID','Nom','Domaine','Pays','Ville','Note','Prix','Delai (j)','Statut'].map(h=><th key={h}>{h}</th>)}</tr>
          </thead>
          <tbody>
            {rows.map(r => (
              <tr key={r.supplier_id}>
                <td><code style={{fontSize:11}}>{r.supplier_id}</code></td>
                <td style={{fontWeight:600}}>{r.supplier_name}</td>
                <td>{r.category}</td>
                <td>{r.country}</td>
                <td>{r.city}</td>
                <td>{r.rating}/5</td>
                <td>{r.price_level}</td>
                <td>{r.delivery_time_days}</td>
                <td><span className={`badge ${r.status==='Actif'?'badge-success':'badge-danger'}`}>{r.status}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>}
    </div>
  )
}

export default function Fournisseurs() {
  const [tab, setTab] = useState('liste')
  const [key, setKey] = useState(0)

  function refresh() { setKey(k=>k+1); setTab('liste') }

  return (
    <>
      <div className="page-header">
        <h1>Gestion des Fournisseurs</h1>
        <p>Importez, consultez et gerez votre base de fournisseurs</p>
      </div>
      <div className="tabs">
        {[['liste','Liste et recherche'],['import','Importer CSV'],['ajouter','Ajouter manuellement']].map(([id,lbl])=>
          <button key={id} className={`tab ${tab===id?'active':''}`} onClick={()=>setTab(id)}>{lbl}</button>
        )}
      </div>
      {tab==='liste'   && <TabListe key={key} />}
      {tab==='import'  && <TabImport onDone={refresh} />}
      {tab==='ajouter' && <TabAjouter onDone={refresh} />}
    </>
  )
}
