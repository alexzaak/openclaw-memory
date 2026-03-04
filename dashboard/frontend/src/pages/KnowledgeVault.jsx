import { useState, useCallback, useEffect } from 'react'
import { apiFetch } from '../hooks/useApi'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorBox from '../components/ErrorBox'

/* ── Label Colors ──────────────────────────────────────────────── */
const labelColors = {
    Person: { bg: 'bg-red-500/10', text: 'text-red-400', border: 'border-red-500/20', icon: '👤' },
    Project: { bg: 'bg-clawdi-amber/10', text: 'text-clawdi-amber', border: 'border-clawdi-amber/20', icon: '📁' },
    Task: { bg: 'bg-clawdi-blue/10', text: 'text-clawdi-blue', border: 'border-clawdi-blue/20', icon: '✅' },
    Event: { bg: 'bg-clawdi-purple/10', text: 'text-clawdi-purple', border: 'border-clawdi-purple/20', icon: '📅' },
    Location: { bg: 'bg-green-500/10', text: 'text-green-400', border: 'border-green-500/20', icon: '📍' },
    Hardware: { bg: 'bg-orange-500/10', text: 'text-orange-400', border: 'border-orange-500/20', icon: '🖥️' },
}

function getLabelStyle(label) {
    return labelColors[label] || { bg: 'bg-clawdi-blue/10', text: 'text-clawdi-blue', border: 'border-clawdi-blue/20', icon: '🔹' }
}

/* ── Entity Card ───────────────────────────────────────────────── */
function EntityCard({ entity, onClick, index }) {
    const style = getLabelStyle(entity.label)
    const name = entity.properties?.name || entity.properties?.ext_id || `Node #${entity.id}`

    return (
        <button
            onClick={() => onClick(entity.id)}
            className="w-full text-left bg-clawdi-card border border-clawdi-border rounded-xl p-4 hover:border-clawdi-blue/30 hover:bg-clawdi-hover transition-all duration-300 group cursor-pointer animate-fade-in"
            style={{ animationDelay: `${index * 0.05}s` }}
        >
            <div className="flex items-start gap-3">
                <div className={`w-10 h-10 rounded-lg ${style.bg} ${style.border} border flex items-center justify-center text-lg shrink-0`}>
                    {style.icon}
                </div>
                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                        <h3 className="text-sm font-semibold text-clawdi-text truncate group-hover:text-clawdi-blue transition-colors">
                            {name}
                        </h3>
                        <span className={`inline-flex px-1.5 py-0.5 rounded text-[10px] font-mono ${style.bg} ${style.text} ${style.border} border`}>
                            {entity.label}
                        </span>
                    </div>

                    {/* Quick properties preview */}
                    <div className="mt-1.5 flex flex-wrap gap-1.5">
                        {Object.entries(entity.properties || {})
                            .filter(([k]) => k !== 'name' && k !== 'ext_id')
                            .slice(0, 3)
                            .map(([key, value]) => (
                                <span key={key} className="text-[10px] text-clawdi-text-muted font-mono bg-clawdi-surface px-1.5 py-0.5 rounded">
                                    {key}: {String(value).slice(0, 30)}
                                </span>
                            ))}
                    </div>

                    {/* Connection count */}
                    <div className="mt-2 flex items-center gap-1 text-xs text-clawdi-text-dim">
                        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13.19 8.688a4.5 4.5 0 011.242 7.244l-4.5 4.5a4.5 4.5 0 01-6.364-6.364l1.757-1.757m9.012-3.072a4.5 4.5 0 00-1.242-7.244l-4.5-4.5a4.5 4.5 0 00-6.364 6.364l1.757 1.757" />
                        </svg>
                        {entity.connection_count} Connections
                    </div>
                </div>
            </div>
        </button>
    )
}

/* ── Entity Detail Panel ───────────────────────────────────────── */
function EntityDetail({ entityId, onClose, onNavigate }) {
    const [data, setData] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    useEffect(() => {
        async function load() {
            setLoading(true)
            try {
                const detail = await apiFetch(`/api/knowledge/entities/${entityId}`)
                setData(detail)
            } catch (err) {
                setError(err.message)
            } finally {
                setLoading(false)
            }
        }
        load()
    }, [entityId])

    if (loading) return <div className="p-6"><LoadingSpinner label="Loading entity…" /></div>
    if (error) return <div className="p-6"><ErrorBox message={error} /></div>
    if (!data) return null

    const style = getLabelStyle(data.label)
    const name = data.properties?.name || `Node #${data.id}`

    // Group connections by relationship type
    const connectionsByType = {}
        ; (data.connections || []).forEach((conn) => {
            const key = `${conn.relationship} (${conn.direction === 'outgoing' ? '→' : '←'})`
            if (!connectionsByType[key]) connectionsByType[key] = []
            connectionsByType[key].push(conn)
        })

    return (
        <div className="fixed inset-0 z-50 flex justify-end" onClick={onClose}>
            {/* Backdrop */}
            <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" />

            {/* Panel */}
            <div
                className="relative w-full max-w-lg bg-clawdi-surface border-l border-clawdi-border overflow-y-auto animate-slide-in"
                onClick={(e) => e.stopPropagation()}
            >
                {/* Header */}
                <div className="sticky top-0 z-10 bg-clawdi-surface/90 backdrop-blur-md border-b border-clawdi-border p-5">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className={`w-11 h-11 rounded-xl ${style.bg} ${style.border} border flex items-center justify-center text-xl`}>
                                {style.icon}
                            </div>
                            <div>
                                <h2 className="text-lg font-bold text-clawdi-text">{name}</h2>
                                <span className={`inline-flex px-2 py-0.5 rounded text-xs font-mono ${style.bg} ${style.text}`}>
                                    {data.label}
                                </span>
                            </div>
                        </div>
                        <button
                            onClick={onClose}
                            className="w-8 h-8 rounded-lg bg-clawdi-card border border-clawdi-border flex items-center justify-center text-clawdi-text-dim hover:text-clawdi-text hover:bg-clawdi-hover transition-all cursor-pointer"
                        >
                            ✕
                        </button>
                    </div>
                </div>

                {/* Properties */}
                <div className="p-5 border-b border-clawdi-border">
                    <h3 className="text-xs font-semibold text-clawdi-text-dim uppercase tracking-wider mb-3">Properties</h3>
                    <div className="grid grid-cols-2 gap-2">
                        {Object.entries(data.properties || {}).map(([key, value]) => (
                            <div key={key} className="bg-clawdi-card rounded-lg p-2.5 border border-clawdi-border">
                                <span className="text-[10px] text-clawdi-text-muted font-mono uppercase">{key}</span>
                                <p className="text-sm text-clawdi-text mt-0.5 truncate">{String(value)}</p>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Connections */}
                <div className="p-5">
                    <h3 className="text-xs font-semibold text-clawdi-text-dim uppercase tracking-wider mb-3">
                        Connections ({data.connections?.length || 0})
                    </h3>

                    {Object.entries(connectionsByType).map(([relType, conns]) => (
                        <div key={relType} className="mb-4">
                            <h4 className="text-xs text-clawdi-blue font-mono mb-2">{relType}</h4>
                            <div className="space-y-1.5">
                                {conns.map((conn) => {
                                    const connStyle = getLabelStyle(conn.node.label)
                                    const connName = conn.node.properties?.name || `Node #${conn.node.id}`
                                    return (
                                        <button
                                            key={conn.node.id}
                                            onClick={() => onNavigate(conn.node.id)}
                                            className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg bg-clawdi-card border border-clawdi-border hover:border-clawdi-blue/30 hover:bg-clawdi-hover transition-all text-left cursor-pointer group"
                                        >
                                            <span className="text-sm">{connStyle.icon}</span>
                                            <span className="text-sm text-clawdi-text group-hover:text-clawdi-blue transition-colors flex-1 truncate">
                                                {connName}
                                            </span>
                                            <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${connStyle.bg} ${connStyle.text}`}>
                                                {conn.node.label}
                                            </span>
                                            <svg className="w-3.5 h-3.5 text-clawdi-text-muted group-hover:text-clawdi-blue transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                            </svg>
                                        </button>
                                    )
                                })}
                            </div>
                        </div>
                    ))}

                    {(!data.connections || data.connections.length === 0) && (
                        <p className="text-sm text-clawdi-text-muted py-4 text-center">No connections found.</p>
                    )}
                </div>
            </div>
        </div>
    )
}

/* ── Stats Bar ─────────────────────────────────────────────────── */
function StatsBar({ stats }) {
    if (!stats || stats.error) return null

    return (
        <div className="flex flex-wrap gap-2 md:gap-3 mb-6">
            <div className="bg-clawdi-card border border-clawdi-border rounded-lg px-4 py-2.5 flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-clawdi-blue" />
                <span className="text-sm font-mono text-clawdi-text">{stats.node_count}</span>
                <span className="text-xs text-clawdi-text-dim">Nodes</span>
            </div>
            <div className="bg-clawdi-card border border-clawdi-border rounded-lg px-4 py-2.5 flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-clawdi-amber" />
                <span className="text-sm font-mono text-clawdi-text">{stats.edge_count}</span>
                <span className="text-xs text-clawdi-text-dim">Edges</span>
            </div>
            {Object.entries(stats.labels || {}).map(([label, count]) => {
                const style = getLabelStyle(label)
                return (
                    <div key={label} className="bg-clawdi-card border border-clawdi-border rounded-lg px-3 py-2.5 flex items-center gap-1.5">
                        <span className="text-xs">{style.icon}</span>
                        <span className="text-sm font-mono text-clawdi-text">{count}</span>
                        <span className="text-[10px] text-clawdi-text-dim">{label}</span>
                    </div>
                )
            })}
        </div>
    )
}

/* ── Main Page ─────────────────────────────────────────────────── */
export default function KnowledgeVault() {
    const [entities, setEntities] = useState([])
    const [stats, setStats] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [activeLabel, setActiveLabel] = useState(null)
    const [searchTerm, setSearchTerm] = useState('')
    const [selectedEntity, setSelectedEntity] = useState(null)

    const loadEntities = useCallback(async () => {
        setLoading(true)
        setError(null)
        try {
            const params = new URLSearchParams()
            if (activeLabel) params.set('label', activeLabel)
            if (searchTerm) params.set('search', searchTerm)
            params.set('limit', '100')

            const [entData, statsData] = await Promise.all([
                apiFetch(`/api/knowledge/entities?${params}`),
                apiFetch('/api/knowledge/stats'),
            ])
            setEntities(entData.entities || [])
            setStats(statsData)
        } catch (err) {
            setError(err.message)
        } finally {
            setLoading(false)
        }
    }, [activeLabel, searchTerm])

    useEffect(() => {
        loadEntities()
    }, [loadEntities])

    const availableLabels = stats?.labels ? Object.keys(stats.labels) : []

    return (
        <div className="max-w-6xl mx-auto">
            {/* Header */}
            <div className="mb-6">
                <h2 className="text-2xl font-bold text-clawdi-text flex items-center gap-3">
                    <span className="w-10 h-10 rounded-xl bg-gradient-to-br from-clawdi-amber/20 to-red-500/20 flex items-center justify-center text-lg border border-clawdi-amber/20">
                        🏛️
                    </span>
                    Knowledge Vault
                </h2>
                <p className="mt-2 text-sm text-clawdi-text-dim">
                    Knowledge Graph Explorer – People, Projects, Tasks and their connections
                </p>
            </div>

            {/* Stats */}
            <StatsBar stats={stats} />

            {/* Filters */}
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 mb-6">
                {/* Search */}
                <div className="relative flex-1 sm:max-w-sm">
                    <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-clawdi-text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
                    </svg>
                    <input
                        id="knowledge-search-input"
                        type="text"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        placeholder="Search entities…"
                        className="w-full pl-9 pr-4 py-2 text-sm bg-clawdi-card border border-clawdi-border rounded-lg text-clawdi-text placeholder-clawdi-text-muted focus:outline-none focus:border-clawdi-blue/40"
                    />
                </div>

                {/* Label filter chips */}
                <div className="flex flex-wrap gap-1.5">
                    <button
                        onClick={() => setActiveLabel(null)}
                        className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer ${!activeLabel
                            ? 'bg-clawdi-blue/15 text-clawdi-blue border border-clawdi-blue/30'
                            : 'bg-clawdi-card text-clawdi-text-dim border border-clawdi-border hover:border-clawdi-blue/20'
                            }`}
                    >
                        Alle
                    </button>
                    {availableLabels.map((label) => {
                        const style = getLabelStyle(label)
                        return (
                            <button
                                key={label}
                                onClick={() => setActiveLabel(activeLabel === label ? null : label)}
                                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer flex items-center gap-1 ${activeLabel === label
                                    ? `${style.bg} ${style.text} border ${style.border}`
                                    : 'bg-clawdi-card text-clawdi-text-dim border border-clawdi-border hover:border-clawdi-blue/20'
                                    }`}
                            >
                                <span className="text-xs">{style.icon}</span>
                                {label}
                            </button>
                        )
                    })}
                </div>
            </div>

            {/* Entity Grid */}
            {loading && <LoadingSpinner label="Loading knowledge graph…" />}
            {error && <ErrorBox message={error} onRetry={loadEntities} />}

            {!loading && !error && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 stagger-children">
                    {entities.map((entity, i) => (
                        <EntityCard
                            key={entity.id}
                            entity={entity}
                            index={i}
                            onClick={setSelectedEntity}
                        />
                    ))}
                </div>
            )}

            {!loading && !error && entities.length === 0 && (
                <div className="text-center py-16">
                    <div className="text-4xl mb-4">🕸️</div>
                    <p className="text-clawdi-text-dim text-sm">No entities found.</p>
                </div>
            )}

            {/* Detail Panel */}
            {selectedEntity && (
                <EntityDetail
                    entityId={selectedEntity}
                    onClose={() => setSelectedEntity(null)}
                    onNavigate={(id) => setSelectedEntity(id)}
                />
            )}
        </div>
    )
}
