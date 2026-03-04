import { useState } from 'react'
import { Routes, Route } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import NeuralFeed from './pages/NeuralFeed'
import KnowledgeVault from './pages/KnowledgeVault'
import HealthMonitor from './pages/HealthMonitor'

export default function App() {
    const [sidebarOpen, setSidebarOpen] = useState(false)

    return (
        <div className="flex min-h-screen bg-clawdi-bg">
            <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

            {/* Hamburger button – visible only on mobile */}
            <button
                id="sidebar-toggle"
                onClick={() => setSidebarOpen(true)}
                className="fixed top-4 left-4 z-40 md:hidden w-10 h-10 rounded-lg bg-clawdi-surface border border-clawdi-border flex items-center justify-center text-clawdi-text-dim hover:text-clawdi-text hover:bg-clawdi-hover transition-all cursor-pointer"
                aria-label="Menü öffnen"
            >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
            </button>

            <main className="flex-1 md:ml-64 p-4 md:p-6 pt-16 md:pt-6 overflow-y-auto">
                <Routes>
                    <Route path="/" element={<NeuralFeed />} />
                    <Route path="/knowledge" element={<KnowledgeVault />} />
                    <Route path="/health" element={<HealthMonitor />} />
                </Routes>
            </main>
        </div>
    )
}
