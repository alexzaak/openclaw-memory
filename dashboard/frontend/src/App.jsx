import { Routes, Route } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import NeuralFeed from './pages/NeuralFeed'
import KnowledgeVault from './pages/KnowledgeVault'
import HealthMonitor from './pages/HealthMonitor'

export default function App() {
    return (
        <div className="flex min-h-screen bg-clawdi-bg">
            <Sidebar />
            <main className="flex-1 ml-64 p-6 overflow-y-auto">
                <Routes>
                    <Route path="/" element={<NeuralFeed />} />
                    <Route path="/knowledge" element={<KnowledgeVault />} />
                    <Route path="/health" element={<HealthMonitor />} />
                </Routes>
            </main>
        </div>
    )
}
