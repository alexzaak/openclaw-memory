import { useState, useEffect, useCallback } from 'react'
import { apiFetch } from '../hooks/useApi'
import LoadingSpinner from './LoadingSpinner'

const SCOPES = [
    { key: null, label: 'Alle', icon: '🔮', bg: 'bg-clawdi-blue/10', text: 'text-clawdi-blue', border: 'border-clawdi-blue/20' },
    { key: 'alex', label: 'Alex', icon: '👤', bg: 'bg-blue-500/10', text: 'text-blue-400', border: 'border-blue-500/20' },
    { key: 'laura', label: 'Laura', icon: '💜', bg: 'bg-fuchsia-500/10', text: 'text-fuchsia-400', border: 'border-fuchsia-500/20' },
    { key: 'family', label: 'Family', icon: '🏠', bg: 'bg-green-500/10', text: 'text-green-400', border: 'border-green-500/20' },
    { key: 'system', label: 'System', icon: '⚙️', bg: 'bg-orange-500/10', text: 'text-orange-400', border: 'border-orange-500/20' },
]

function getScopeStyle(scope) {
    return SCOPES.find((s) => s.key === scope) || SCOPES[0]
}

function formatTimestamp(ts) {
    const date = new Date(ts)
    const now = new Date()
    const isToday = date.toDateString() === now.toDateString()

    const yesterday = new Date(now)
    yesterday.setDate(yesterday.getDate() - 1)
    const isYesterday = date.toDateString() === yesterday.toDateString()

    const time = date.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })

    if (isToday) return `Today, ${time}`
    if (isYesterday) return `Yesterday, ${time}`
    return `${date.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit' })} ${time}`
}

function ContextEntry({ entry, index }) {
    const style = getScopeStyle(entry.scope)

    return (
        <div
            className="bg-clawdi-card border border-clawdi-border rounded-lg p-3.5 hover:border-clawdi-blue/20 transition-all duration-200 animate-fade-in"
            style={{ animationDelay: `${index * 0.04}s` }}
        >
            <div className="flex items-start gap-3">
                {/* Scope badge */}
                <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-mono font-medium shrink-0 mt-0.5 ${style.bg} ${style.text} border ${style.border}`}>
                    {style.icon} {entry.scope}
                </span>

                {/* Content + time */}
                <div className="flex-1 min-w-0">
                    <p className="text-sm text-clawdi-text leading-relaxed">{entry.content}</p>
                    <span className="text-[10px] text-clawdi-text-muted font-mono mt-1.5 inline-block">
                        {formatTimestamp(entry.timestamp)}
                    </span>
                </div>
            </div>
        </div>
    )
}

export default function DailyContextWidget() {
    const [entries, setEntries] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [activeScope, setActiveScope] = useState(null)

    const loadData = useCallback(async () => {
        setLoading(true)
        setError(null)
        try {
            const params = new URLSearchParams({ limit: '50' })
            if (activeScope) params.set('scope', activeScope)
            const data = await apiFetch(`/api/memory/daily-context?${params}`)
            setEntries(data.entries || [])
        } catch (err) {
            setError(err.message)
        } finally {
            setLoading(false)
        }
    }, [activeScope])

    useEffect(() => {
        loadData()
    }, [loadData])

    return (
        <div>
            {/* Header */}
            <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-clawdi-text-dim uppercase tracking-wider flex items-center gap-2">
                    <span className="w-5 h-5 rounded bg-clawdi-amber/10 flex items-center justify-center text-xs">📝</span>
                    Daily Context
                </h3>
                <span className="text-[10px] text-clawdi-text-muted font-mono">{entries.length} entries</span>
            </div>

            {/* Scope filter chips */}
            <div className="flex gap-1.5 mb-3 flex-wrap">
                {SCOPES.map((scope) => (
                    <button
                        key={scope.label}
                        onClick={() => setActiveScope(scope.key)}
                        className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-all cursor-pointer flex items-center gap-1 ${activeScope === scope.key
                            ? `${scope.bg} ${scope.text} border ${scope.border}`
                            : 'bg-clawdi-card text-clawdi-text-dim border border-clawdi-border hover:border-clawdi-blue/20'
                            }`}
                    >
                        <span className="text-xs">{scope.icon}</span>
                        {scope.label}
                    </button>
                ))}
            </div>

            {/* Content */}
            {loading && <LoadingSpinner size="sm" label="Loading daily context…" />}

            {error && (
                <div className="text-center py-6">
                    <p className="text-xs text-clawdi-text-muted">{error}</p>
                    <button onClick={loadData} className="text-xs text-clawdi-blue mt-2 hover:underline cursor-pointer">Retry</button>
                </div>
            )}

            {!loading && !error && entries.length === 0 && (
                <div className="text-center py-8">
                    <div className="text-2xl mb-2">📭</div>
                    <p className="text-xs text-clawdi-text-muted">No daily context available.</p>
                </div>
            )}

            {!loading && !error && entries.length > 0 && (
                <div className="space-y-2 max-h-[500px] overflow-y-auto pr-1">
                    {entries.map((entry, i) => (
                        <ContextEntry key={entry.id} entry={entry} index={i} />
                    ))}
                </div>
            )}
        </div>
    )
}
