import { useState, useCallback } from 'react'
import { apiFetch } from '../hooks/useApi'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorBox from '../components/ErrorBox'

function MemoryCard({ memory, index }) {
    const isUser = memory.sender === 'user'
    const date = memory.timestamp ? new Date(memory.timestamp) : null
    const scorePercent = memory.score ? Math.round(memory.score * 100) : null

    return (
        <div
            className="bg-clawdi-card border border-clawdi-border rounded-xl p-4 hover:border-clawdi-blue/30 transition-all duration-300 group animate-fade-in"
            style={{ animationDelay: `${index * 0.05}s` }}
        >
            {/* Header */}
            <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-mono font-medium ${isUser
                        ? 'bg-clawdi-amber/10 text-clawdi-amber border border-clawdi-amber/20'
                        : 'bg-clawdi-blue/10 text-clawdi-blue border border-clawdi-blue/20'
                        }`}>
                        {isUser ? '👤 User' : '🤖 Clawdi'}
                    </span>
                    {memory.session_id && (
                        <span className="text-[10px] text-clawdi-text-muted font-mono">
                            #{memory.session_id.slice(0, 8)}
                        </span>
                    )}
                </div>
                {date && (
                    <span className="text-xs text-clawdi-text-muted font-mono">
                        {date.toLocaleDateString('de-DE')} · {date.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })}
                    </span>
                )}
            </div>

            {/* Content */}
            <p className="text-sm text-clawdi-text leading-relaxed whitespace-pre-wrap line-clamp-6 group-hover:line-clamp-none transition-all">
                {memory.text}
            </p>

            {/* Score bar */}
            {scorePercent !== null && (
                <div className="mt-3 flex items-center gap-2">
                    <div className="flex-1 h-1 rounded-full bg-clawdi-border overflow-hidden">
                        <div
                            className="h-full rounded-full bg-gradient-to-r from-clawdi-blue to-clawdi-purple transition-all duration-500"
                            style={{ width: `${scorePercent}%` }}
                        />
                    </div>
                    <span className="text-[10px] text-clawdi-text-dim font-mono">{scorePercent}%</span>
                </div>
            )}
        </div>
    )
}

export default function NeuralFeed() {
    const [query, setQuery] = useState('')
    const [results, setResults] = useState(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const [recentData, setRecentData] = useState(null)
    const [recentLoading, setRecentLoading] = useState(false)

    const handleSearch = useCallback(async (e) => {
        e?.preventDefault()
        if (!query.trim()) return

        setLoading(true)
        setError(null)
        try {
            const data = await apiFetch(`/api/neural-feed/search?q=${encodeURIComponent(query)}&limit=20`)
            setResults(data)
        } catch (err) {
            setError(err.message)
        } finally {
            setLoading(false)
        }
    }, [query])

    const loadRecent = useCallback(async () => {
        setRecentLoading(true)
        try {
            const data = await apiFetch('/api/neural-feed/recent?limit=30')
            setRecentData(data)
        } catch (err) {
            setError(err.message)
        } finally {
            setRecentLoading(false)
        }
    }, [])

    return (
        <div className="max-w-4xl mx-auto">
            {/* Header */}
            <div className="mb-5 md:mb-8">
                <h2 className="text-2xl font-bold text-clawdi-text flex items-center gap-3">
                    <span className="w-10 h-10 rounded-xl bg-gradient-to-br from-clawdi-blue/20 to-clawdi-purple/20 flex items-center justify-center text-lg border border-clawdi-blue/20">
                        ✨
                    </span>
                    Neural Feed
                </h2>
                <p className="mt-2 text-sm text-clawdi-text-dim">
                    Semantic search through Clawdi's memory – powered by Qdrant + Ollama Embeddings
                </p>
            </div>

            {/* Search Bar */}
            <form onSubmit={handleSearch} className="mb-8">
                <div className="relative group">
                    <div className="absolute -inset-0.5 bg-gradient-to-r from-clawdi-blue/20 to-clawdi-purple/20 rounded-2xl opacity-0 group-focus-within:opacity-100 transition-opacity duration-500 blur-sm" />
                    <div className="relative flex items-center glass-surface rounded-xl overflow-hidden">
                        <div className="pl-4 text-clawdi-text-muted">
                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
                            </svg>
                        </div>
                        <input
                            id="neural-search-input"
                            type="text"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            placeholder={'Search Clawdi\u2019s memory\u2026 e.g. \u201cWhen was the last doctor appointment?\u201d'}
                            className="flex-1 px-4 py-4 bg-transparent text-clawdi-text placeholder-clawdi-text-muted text-sm focus:outline-none"
                        />
                        <button
                            type="submit"
                            disabled={loading || !query.trim()}
                            className="px-5 py-2 mr-2 text-sm font-medium rounded-lg bg-clawdi-blue/10 text-clawdi-blue border border-clawdi-blue/20 hover:bg-clawdi-blue/20 disabled:opacity-30 disabled:cursor-not-allowed transition-all cursor-pointer"
                        >
                            {loading ? 'Searching…' : 'Search'}
                        </button>
                    </div>
                </div>
            </form>

            {/* Results or Recent Feed */}
            {loading && <LoadingSpinner label="Searching memories…" />}
            {error && <ErrorBox message={error} onRetry={results ? handleSearch : loadRecent} />}

            {results && !loading && (
                <div>
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-sm font-medium text-clawdi-text-dim">
                            {results.count} results for "{results.query}"
                        </h3>
                        <button
                            onClick={() => { setResults(null); setQuery('') }}
                            className="text-xs text-clawdi-text-muted hover:text-clawdi-blue transition-colors cursor-pointer"
                        >
                            Reset
                        </button>
                    </div>
                    <div className="space-y-3 stagger-children">
                        {results.results.map((memory, i) => (
                            <MemoryCard key={memory.id} memory={memory} index={i} />
                        ))}
                    </div>
                </div>
            )}

            {!results && !loading && (
                <div>
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-sm font-medium text-clawdi-text-dim">Recent Memories</h3>
                        <button
                            onClick={loadRecent}
                            disabled={recentLoading}
                            className="text-xs text-clawdi-blue hover:text-clawdi-amber transition-colors cursor-pointer"
                        >
                            {recentLoading ? 'Loading…' : 'Refresh'}
                        </button>
                    </div>

                    {recentLoading && <LoadingSpinner label="Loading latest entries…" size="sm" />}

                    {recentData?.points?.length > 0 ? (
                        <div className="space-y-3 stagger-children">
                            {recentData.points.map((memory, i) => (
                                <MemoryCard key={memory.id} memory={memory} index={i} />
                            ))}
                        </div>
                    ) : !recentLoading ? (
                        <div className="text-center py-16">
                            <div className="text-4xl mb-4">🔍</div>
                            <p className="text-clawdi-text-dim text-sm">
                                Start a search above or click "Refresh" to load the latest memories.
                            </p>
                        </div>
                    ) : null}
                </div>
            )}
        </div>
    )
}
