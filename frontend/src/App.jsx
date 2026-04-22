import React from 'react'
import { Routes, Route, NavLink, useLocation } from 'react-router-dom'
import Dashboard     from './pages/Dashboard.jsx'
import Fournisseurs  from './pages/Fournisseurs.jsx'
import NouvelleDemande from './pages/NouvelleDemande.jsx'
import Resultats     from './pages/Resultats.jsx'
import Historique    from './pages/Historique.jsx'
import QA            from './pages/QA.jsx'

const LINKS = [
  { to: '/',                  label: 'Tableau de bord' },
  { to: '/fournisseurs',      label: 'Fournisseurs'    },
  { to: '/nouvelle-demande',  label: 'Nouvelle demande'},
  { to: '/resultats',         label: 'Resultats'       },
  { to: '/historique',        label: 'Historique'      },
  { to: '/qa',                label: 'Q&A Documentaire'},
]

function Navbar() {
  const loc = useLocation()
  const now = new Date().toLocaleDateString('fr-FR')
  return (
    <nav className="navbar">
      <NavLink to="/" className="navbar-brand">
        <div className="navbar-logo">NV</div>
        <div>
          <div className="navbar-name">Novec</div>
          <div className="navbar-sub">Gestion des Achats</div>
        </div>
      </NavLink>
      <div className="navbar-links">
        {LINKS.map(l => (
          <NavLink
            key={l.to}
            to={l.to}
            className={({ isActive }) =>
              'navbar-link' + (isActive ? ' active' : '')
            }
            end={l.to === '/'}
          >{l.label}</NavLink>
        ))}
      </div>
      <div className="navbar-date">{now}</div>
    </nav>
  )
}

export default function App() {
  return (
    <div className="layout">
      <Navbar />
      <main className="main-content">
        <Routes>
          <Route path="/"               element={<Dashboard />} />
          <Route path="/fournisseurs"   element={<Fournisseurs />} />
          <Route path="/nouvelle-demande" element={<NouvelleDemande />} />
          <Route path="/resultats"      element={<Resultats />} />
          <Route path="/historique"     element={<Historique />} />
          <Route path="/qa"             element={<QA />} />
        </Routes>
      </main>
    </div>
  )
}
