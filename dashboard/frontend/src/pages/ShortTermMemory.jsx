import { useState, useEffect, useCallback } from 'react'
import { apiFetch } from '../hooks/useApi'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorBox from '../components/ErrorBox'
import DailyContextWidget from '../components/DailyContextWidget'

/* ── Category Badge Colors ────────────────────────────────────── */
const CATEGORY_STYLES = {
    general: { bg: 'bg-clawdi-blue/10', text: 'text-clawdi-blue', border: 'border-clawdi-blue/20', icon: '📝' },
    preference: { bg: 'bg-fuchsia-500/10', text: 'text-fuchsia-400', border: 'border-fuchsia-500/20', icon: '💜' },
    fact: { bg: 'bg-green-500/10', text: 'text-green-400', border: 'border-green-500/20', icon: '✅' },
    system: { bg: 'bg-orange-500/10', text: 'text-orange-400', border: 'border-orange-500/20', icon: '⚙️' },
}

function getCategoryStyle(category) {
    return CATEGORY_STYLES[category] || CATEGORY_STYLES.general
}

function formatTimestamp(ts) {
    const date = new Date(ts)
    const now = new Date()
    const isToday = date.toDateString() === now.toDateString()

    const yesterday = new Date(now)
    yesterday.setDate(yesterday.getDate() - 1)
    const isYesterday = date.toDateString() === yesterday.toDateString()

    const time = date.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })

    if (isToday) return `Today, ${time}`
    if (isYesterday) return `Yesterday, ${time}`
    return `${date.toLocaleDateString('en-GB', { day: '2-digit', month: '2-digit' })} ${time}`
}

/* ── Learning Entry ────────────────────────────────────────────── */
function LearningEntry({ entry, index }) {
    const style = getCategoryStyle(entry.category)

    return (
        <div
            className="relative pl-6 pb-5 last:pb-0 animate-fade-in"
            style={{ animationDelay: `${index * 0.04}s` }}
        >
            {/* Timeline line */}
            <div className="absolute left-[7px] top-3 bottom-0 w-px bg-clawdi-border" />
            {/* Dot */}
            <div className={`absolute left-0 top-1.5 w-[15px] h-[15px] rounded-full bg-clawdi-surface border-2 flex items-center justify-center ${style.border}`}>
                <div className={`w-1.5 h-1.5 rounded-full ${style.text === 'text-clawdi-blue' ? 'bg-clawdi-blue' : style.text === 'text-fuchsia-400' ? 'bg-fuchsia-400' : style.text === 'text-green-400' ? 'bg-green-400' : 'bg-orange-400'}`} />
            </div>

            <div className="bg-clawdi-card border border-clawdi-border rounded-lg p-3 hover:border-clawdi-blue/20 transition-all">
                <p className="text-sm text-clawdi-text leading-relaxed">{entry.content}</p>
                <div className="flex items-center gap-2 mt-2 flex-wrap">
                    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-mono font-medium ${style.bg} ${style.text} border ${style.border}`}>
                        {style.icon} {entry.category}
                    </span>
                    {entry.source && (
                        <span className="text-[10px] text-clawdi-text-muted font-mono">
                            ← {entry.source}
                        </span>
                    )}
                    <span className="text-[10px] text-clawdi-text-muted font-mono ml-auto">
                        {formatTimestamp(entry.timestamp)}
                    </span>
                    {entry.processed === 1 && (
                        <span className="text-[10px] text-green-400 font-mono" title="Ingested into knowledge graph">
                            ✓ synced
                        </span>
                    )}
                </div>
            </div>
        </div>
    )
}

/* ── Main Page ─────────────────────────────────────────────────── */
export default function ShortTermMemory() {
    const [learnings, setLearnings] = useState(null)
    const [categories, setCategories] = useState([])
    const [activeCategory, setActiveCategory] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    const loadData = useCallback(async () => {
        setLoading(true)
        setError(null)
        try {
            const params = new URLSearchParams({ limit: '50' })
            if (activeCategory) params.set('category', activeCategory)

            const [learningData, categoryData] = await Promise.all([
                apiFetch(`/api/memory/learnings?${params}`),
                apiFetch('/api/memory/learnings/categories'),
            ])
            setLearnings(learningData.entries || [])
            setCategories(categoryData.categories || [])
        } catch (err) {
            setError(err.message)
        } finally {
            setLoading(false)
        }
    }, [activeCategory])

    useEffect(() => {
        loadData()
    }, [loadData])

    if (loading) return <LoadingSpinner label="Loading short-term memory…" />
    if (error) return <ErrorBox message={error} onRetry={loadData} />

    return (
        <div className="max-w-6xl mx-auto">
            {/* Header */}
            <div className="mb-6">
                <h2 className="text-2xl font-bold text-clawdi-text flex items-center gap-3">
                    <span className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500/20 to-clawdi-purple/20 flex items-center justify-center text-lg border border-amber-500/20">
                        🧠
                    </span>
                    Short-Term Memory
                </h2>
                <p className="mt-2 text-sm text-clawdi-text-dim">
                    Daily context and learnings – compressed nightly by REM Sleep
                </p>
            </div>

            {/* Daily Context */}
            <div className="mb-8 bg-clawdi-surface border border-clawdi-border rounded-xl p-5">
                <DailyContextWidget />
            </div>

            {/* Learnings */}
            <div className="bg-clawdi-surface border border-clawdi-border rounded-xl p-5">
                <div className="flex items-center justify-between mb-3">
                    <h3 className="text-sm font-semibold text-clawdi-text-dim uppercase tracking-wider flex items-center gap-2">
                        <span className="w-5 h-5 rounded bg-clawdi-purple/10 flex items-center justify-center text-xs">📚</span>
                        Learnings
                    </h3>
                    <span className="text-[10px] text-clawdi-text-muted font-mono">{learnings?.length || 0} entries</span>
                </div>

                {/* Category filter chips */}
                {categories.length > 0 && (
                    <div className="flex gap-1.5 mb-4 flex-wrap">
                        <button
                            onClick={() => setActiveCategory(null)}
                            className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-all cursor-pointer flex items-center gap-1 ${activeCategory === null
                                    ? 'bg-clawdi-blue/10 text-clawdi-blue border border-clawdi-blue/20'
                                    : 'bg-clawdi-card text-clawdi-text-dim border border-clawdi-border hover:border-clawdi-blue/20'
                                }`}
                        >
                            <span className="text-xs">🔮</span> All
                        </button>
                        {categories.map((cat) => {
                            const style = getCategoryStyle(cat)
                            return (
                                <button
                                    key={cat}
                                    onClick={() => setActiveCategory(cat)}
                                    className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-all cursor-pointer flex items-center gap-1 ${activeCategory === cat
                                            ? `${style.bg} ${style.text} border ${style.border}`
                                            : 'bg-clawdi-card text-clawdi-text-dim border border-clawdi-border hover:border-clawdi-blue/20'
                                        }`}
                                >
                                    <span className="text-xs">{style.icon}</span> {cat}
                                </button>
                            )
                        })}
                    </div>
                )}

                {/* Learning entries with timeline */}
                <div className="relative max-h-[600px] overflow-y-auto pr-1">
                    {learnings && learnings.length > 0 ? (
                        learnings.map((entry, i) => (
                            <LearningEntry key={entry.id} entry={entry} index={i} />
                        ))
                    ) : (
                        <div className="text-center py-8">
                            <div className="text-2xl mb-2">📭</div>
                            <p className="text-xs text-clawdi-text-muted">No learnings recorded yet.</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
