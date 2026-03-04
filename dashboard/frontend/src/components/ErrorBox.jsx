export default function ErrorBox({ message, onRetry }) {
    return (
        <div className="flex flex-col items-center gap-4 py-12 text-center">
            <div className="w-12 h-12 rounded-full bg-clawdi-red/10 flex items-center justify-center">
                <svg className="w-6 h-6 text-clawdi-red" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
            </div>
            <div>
                <p className="text-clawdi-text font-medium">Connection Error</p>
                <p className="text-sm text-clawdi-text-dim mt-1">{message}</p>
            </div>
            {onRetry && (
                <button
                    onClick={onRetry}
                    className="px-4 py-2 text-sm font-medium rounded-lg bg-clawdi-blue/10 text-clawdi-blue border border-clawdi-blue/20 hover:bg-clawdi-blue/20 transition-colors cursor-pointer"
                >
                    Retry
                </button>
            )}
        </div>
    )
}
