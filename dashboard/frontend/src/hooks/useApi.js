import { useState, useEffect, useCallback } from 'react'

const API_BASE = ''

export function useApi(url, options = {}) {
    const [data, setData] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    const { enabled = true, deps = [] } = options

    const fetchData = useCallback(async () => {
        if (!enabled) return
        setLoading(true)
        setError(null)
        try {
            const res = await fetch(`${API_BASE}${url}`)
            if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
            const json = await res.json()
            setData(json)
        } catch (err) {
            setError(err.message)
        } finally {
            setLoading(false)
        }
    }, [url, enabled, ...deps])

    useEffect(() => {
        fetchData()
    }, [fetchData])

    return { data, loading, error, refetch: fetchData }
}

export async function apiFetch(url) {
    const res = await fetch(`${API_BASE}${url}`)
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
    return res.json()
}
