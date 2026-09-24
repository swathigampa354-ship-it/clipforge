import React from 'react'
import { Outlet, NavLink } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { useQuery } from '@tanstack/react-query'
import api from '../lib/api'

export default function Layout() {
  const { user, logout, token } = useAuth()

  const navItems = [
    { to: '/', label: 'Dashboard', icon: '🏠' },
    { to: '/projects', label: 'Projects', icon: '📁' },
    { to: '/settings', label: 'Settings', icon: '⚙️' },
    { to: '/billing', label: 'Billing', icon: '💳' },
  ]

  return (
    <div className="flex min-h-screen bg-gray-950">
      <aside className="w-16 bg-gray-900 border-r border-gray-800 flex flex-col items-center py-4 gap-2">
        <div className="text-2xl font-bold text-indigo-400 mb-8">CF</div>
        {navItems.map(item => (
          <NavLink
            key={item.to}
            to={item.to}
            title={item.label}
            className={({ isActive }) =>
              `w-12 h-12 flex items-center justify-center rounded-lg text-lg transition-colors ${
                isActive ? 'bg-indigo-600 text-white' : 'text-gray-400 hover:bg-gray-800'
              }`
            }
          >
            {item.icon}
          </NavLink>
        ))}
      </aside>
      <div className="flex-1 flex flex-col">
        <header className="h-16 bg-gray-900 border-b border-gray-800 flex items-center justify-between px-6">
          <h1 className="text-lg font-semibold">ClipForge</h1>
          <div className="flex items-center gap-4">
            {user && <span className="text-gray-400">{user.name}</span>}
            {user && (
              <button onClick={logout} className="btn-secondary text-sm py-1 px-4">
                Logout
              </button>
            )}
          </div>
        </header>
        <main className="flex-1 p-6 overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
