export default function LoadingSpinner({ size = 'md', label = 'Loading…' }) {
    const sizes = {
        sm: 'w-5 h-5',
        md: 'w-8 h-8',
        lg: 'w-12 h-12',
    }

    return (
        <div className="flex flex-col items-center justify-center gap-3 py-12">
            <div className={`${sizes[size]} relative`}>
                <div className="absolute inset-0 rounded-full border-2 border-clawdi-border" />
                <div className="absolute inset-0 rounded-full border-2 border-transparent border-t-clawdi-blue animate-spin" />
                <div className="absolute inset-1 rounded-full bg-clawdi-blue/10 animate-neural-pulse" />
            </div>
            <span className="text-sm text-clawdi-text-dim">{label}</span>
        </div>
    )
}
