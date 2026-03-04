import { useState, useEffect, useCallback } from 'react'
import { apiFetch } from '../hooks/useApi'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorBox from '../components/ErrorBox'
import DailyContextWidget from '../components/DailyContextWidget'

/* ── Sparkline Mini-Chart ──────────────────────────────────────── */
function Sparkline({ data, color = '#00b4d8', height = 40 }) {
    if (!data || data.length === 0) return null

    const values = data.map((d) => parseFloat(d.value || d.mood_score || 0))
    const min = Math.min(...values)
    const max = Math.max(...values)
    const range = max - min || 1
    const width = 200

    const points = values.map((v, i) => {
        const x = (i / (values.length - 1)) * width
        const y = height - ((v - min) / range) * (height - 8) - 4
        return `${x},${y}`
    }).join(' ')

    const areaPoints = `0,${height} ${points} ${width},${height}`

    return (
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full" preserveAspectRatio="none">
            <defs>
                <linearGradient id={`grad-${color.replace('#', '')}`} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={color} stopOpacity="0.3" />
                    <stop offset="100%" stopColor={color} stopOpacity="0" />
                </linearGradient>
            </defs>
            <polygon points={areaPoints} fill={`url(#grad-${color.replace('#', '')})`} />
            <polyline points={points} fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            {/* Last point dot */}
            {values.length > 0 && (
                <circle
                    cx={(values.length - 1) / (values.length - 1) * width}
                    cy={height - ((values[values.length - 1] - min) / range) * (height - 8) - 4}
                    r="3"
                    fill={color}
                />
            )}
        </svg>
    )
}

/* ── Metric Widget ─────────────────────────────────────────────── */
function MetricWidget({ title, value, unit, icon, color, sparkData }) {
    return (
        <div className="bg-clawdi-card border border-clawdi-border rounded-xl p-4 hover:border-clawdi-blue/20 transition-all">
            <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                    <span className="text-lg">{icon}</span>
                    <span className="text-xs font-medium text-clawdi-text-dim uppercase tracking-wider">{title}</span>
                </div>
            </div>
            <div className="flex items-end justify-between">
                <div>
                    <span className="text-2xl font-bold text-clawdi-text font-mono">{value}</span>
                    {unit && <span className="text-sm text-clawdi-text-dim ml-1">{unit}</span>}
                </div>
            </div>
            {sparkData && (
                <div className="mt-3">
                    <Sparkline data={sparkData} color={color} />
                </div>
            )}
        </div>
    )
}

/* ── State Key-Value Card ──────────────────────────────────────── */
function StateCard({ stateKey, data }) {
    const icons = {
        konsti_temperature: '🌡️',
        system_status: '⚙️',
        watcher_running: '👁️',
        qdrant_points_count: '🗃️',
        last_rem_sleep: '🌙',
        graph_node_count: '🔵',
        graph_edge_count: '🔗',
    }
    const icon = icons[stateKey] || '📊'

    return (
        <div className="bg-clawdi-card border border-clawdi-border rounded-lg px-4 py-3 flex items-center justify-between hover:border-clawdi-blue/20 transition-all">
            <div className="flex items-center gap-2.5">
                <span className="text-sm">{icon}</span>
                <span className="text-xs font-mono text-clawdi-text-dim">{stateKey}</span>
            </div>
            <div className="text-right">
                <span className="text-sm font-semibold text-clawdi-text font-mono">{data.value}</span>
                {data.updated_at && (
                    <p className="text-[10px] text-clawdi-text-muted mt-0.5">
                        {new Date(data.updated_at).toLocaleString('de-DE', { hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit' })}
                    </p>
                )}
            </div>
        </div>
    )
}

/* ── Learning Log Entry ────────────────────────────────────────── */
function LearningEntry({ entry, index }) {
    const date = entry.timestamp ? new Date(entry.timestamp) : null

    return (
        <div
            className="relative pl-6 pb-6 last:pb-0 animate-fade-in"
            style={{ animationDelay: `${index * 0.05}s` }}
        >
            {/* Timeline line */}
            <div className="absolute left-[7px] top-3 bottom-0 w-px bg-clawdi-border" />
            {/* Dot */}
            <div className="absolute left-0 top-1.5 w-[15px] h-[15px] rounded-full bg-clawdi-surface border-2 border-clawdi-blue flex items-center justify-center">
                <div className="w-1.5 h-1.5 rounded-full bg-clawdi-blue" />
            </div>

            <div className="bg-clawdi-card border border-clawdi-border rounded-lg p-3 hover:border-clawdi-blue/20 transition-all">
                <p className="text-sm text-clawdi-text leading-relaxed">{entry.content}</p>
                <div className="flex items-center gap-3 mt-2">
                    {date && (
                        <span className="text-[10px] text-clawdi-text-muted font-mono">
                            {date.toLocaleDateString('de-DE')} · {date.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })}
                        </span>
                    )}
                    {entry.mood_score && (
                        <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${entry.mood_score >= 7 ? 'bg-green-500/10 text-green-400' :
                            entry.mood_score >= 4 ? 'bg-clawdi-amber/10 text-clawdi-amber' :
                                'bg-red-500/10 text-red-400'
                            }`}>
                            Mood: {entry.mood_score}/10
                        </span>
                    )}
                </div>
            </div>
        </div>
    )
}

/* ── Main Page ─────────────────────────────────────────────────── */
export default function HealthMonitor() {
    const [state, setState] = useState(null)
    const [logs, setLogs] = useState(null)
    const [learningLog, setLearningLog] = useState(null)
    const [moodTimeline, setMoodTimeline] = useState(null)
    const [tempLogs, setTempLogs] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    const loadData = useCallback(async () => {
        setLoading(true)
        setError(null)
        try {
            const [stateData, lrnData, moodData, tempData] = await Promise.all([
                apiFetch('/api/health/state'),
                apiFetch('/api/health/learning-log?limit=15'),
                apiFetch('/api/health/mood-timeline?days=7'),
                apiFetch('/api/health/logs?category=TEMP&limit=20'),
            ])
            setState(stateData.state || {})
            setLearningLog(lrnData.entries || [])
            setMoodTimeline(moodData.timeline || [])
            setTempLogs(tempData.logs || [])
        } catch (err) {
            setError(err.message)
        } finally {
            setLoading(false)
        }
    }, [])

    useEffect(() => {
        loadData()
    }, [loadData])

    if (loading) return <LoadingSpinner label="Loading Health Monitor…" />
    if (error) return <ErrorBox message={error} onRetry={loadData} />

    // Parse temperature from TEMP logs for sparkline
    const tempValues = (tempLogs || []).reverse().map((log) => {
        const match = log.content?.match(/([\d.]+)°C/)
        return { value: match ? parseFloat(match[1]) : 0, timestamp: log.timestamp }
    })

    const latestTemp = tempValues.length > 0 ? tempValues[tempValues.length - 1].value : '—'

    return (
        <div className="max-w-6xl mx-auto">
            {/* Header */}
            <div className="mb-6">
                <h2 className="text-2xl font-bold text-clawdi-text flex items-center gap-3">
                    <span className="w-10 h-10 rounded-xl bg-gradient-to-br from-green-500/20 to-clawdi-blue/20 flex items-center justify-center text-lg border border-green-500/20">
                        📊
                    </span>
                    Health & Learning Monitor
                </h2>
                <p className="mt-2 text-sm text-clawdi-text-dim">
                    System status, metrics and self-improvement log
                </p>
            </div>

            {/* Metric Widgets */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 mb-8">
                <MetricWidget
                    title="Konsti Temperatur"
                    value={latestTemp}
                    unit="°C"
                    icon="🌡️"
                    color={latestTemp > 38 ? '#ef4444' : latestTemp > 37.5 ? '#f5a623' : '#22c55e'}
                    sparkData={tempValues}
                />
                <MetricWidget
                    title="Mood Score"
                    value={moodTimeline?.length > 0 ? moodTimeline[moodTimeline.length - 1].mood_score : '—'}
                    unit="/10"
                    icon="💭"
                    color="#a78bfa"
                    sparkData={moodTimeline?.map(m => ({ value: m.mood_score }))}
                />
                <MetricWidget
                    title="Qdrant Punkte"
                    value={state?.qdrant_points_count?.value || '—'}
                    icon="🗃️"
                    color="#00b4d8"
                />
            </div>

            {/* Daily Context */}
            <div className="mb-8 bg-clawdi-surface border border-clawdi-border rounded-xl p-5">
                <DailyContextWidget />
            </div>

            {/* Two-column: System State + Learning Log */}
            <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
                {/* System State */}
                <div className="lg:col-span-2">
                    <h3 className="text-sm font-semibold text-clawdi-text-dim uppercase tracking-wider mb-3 flex items-center gap-2">
                        <span className="w-5 h-5 rounded bg-clawdi-blue/10 flex items-center justify-center text-xs">⚙️</span>
                        System State
                    </h3>
                    <div className="space-y-2">
                        {Object.entries(state || {}).map(([key, data]) => (
                            <StateCard key={key} stateKey={key} data={data} />
                        ))}
                    </div>
                </div>

                {/* Learning Log */}
                <div className="lg:col-span-3">
                    <h3 className="text-sm font-semibold text-clawdi-text-dim uppercase tracking-wider mb-3 flex items-center gap-2">
                        <span className="w-5 h-5 rounded bg-clawdi-purple/10 flex items-center justify-center text-xs">🧠</span>
                        Learning Log (Self-Improvement)
                    </h3>
                    <div className="relative">
                        {learningLog && learningLog.length > 0 ? (
                            learningLog.map((entry, i) => (
                                <LearningEntry key={entry.id} entry={entry} index={i} />
                            ))
                        ) : (
                            <p className="text-sm text-clawdi-text-muted py-4 text-center">No learning log entries found.</p>
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
}
