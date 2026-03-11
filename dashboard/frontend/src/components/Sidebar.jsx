import { NavLink } from 'react-router-dom'

const navItems = [
    {
        to: '/',
        label: 'Neural Feed',
        icon: (
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z" />
            </svg>
        ),
    },
    {
        to: '/knowledge',
        label: 'Knowledge Vault',
        icon: (
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375m16.5 0v3.75m-16.5-3.75v3.75m16.5 0v3.75C20.25 16.153 16.556 18 12 18s-8.25-1.847-8.25-4.125v-3.75m16.5 0c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125" />
            </svg>
        ),
    },
    {
        to: '/memory',
        label: 'Short-Term Memory',
        icon: (
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
            </svg>
        ),
    },
]

export default function Sidebar({ isOpen, onClose }) {
    return (
        <>
            {/* Backdrop – mobile only */}
            {isOpen && (
                <div
                    className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 md:hidden"
                    onClick={onClose}
                />
            )}

            <aside
                className={`
                    w-64 h-screen fixed left-0 top-0
                    bg-clawdi-surface border-r border-clawdi-border
                    flex flex-col z-50
                    transition-transform duration-300 ease-in-out
                    ${isOpen ? 'translate-x-0' : '-translate-x-full'}
                    md:translate-x-0
                `}
            >
                {/* Logo */}
                <div className="p-5 border-b border-clawdi-border flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-clawdi-blue to-clawdi-purple flex items-center justify-center text-lg animate-glow">
                            🧠
                        </div>
                        <div>
                            <h1 className="text-base font-semibold text-clawdi-text tracking-tight">Clawdi Brain</h1>
                            <p className="text-[11px] text-clawdi-text-muted font-mono">OpenClaw Memory v1.0</p>
                        </div>
                    </div>

                    {/* Close button – mobile only */}
                    <button
                        onClick={onClose}
                        className="w-8 h-8 rounded-lg bg-clawdi-card border border-clawdi-border flex items-center justify-center text-clawdi-text-dim hover:text-clawdi-text hover:bg-clawdi-hover transition-all cursor-pointer md:hidden"
                        aria-label="Close menu"
                    >
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                {/* Navigation */}
                <nav className="flex-1 p-3 space-y-1">
                    {navItems.map((item) => (
                        <NavLink
                            key={item.to}
                            to={item.to}
                            onClick={onClose}
                            className={({ isActive }) =>
                                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 group ${isActive
                                    ? 'bg-clawdi-blue/10 text-clawdi-blue border border-clawdi-blue/20'
                                    : 'text-clawdi-text-dim hover:text-clawdi-text hover:bg-clawdi-hover border border-transparent'
                                }`
                            }
                        >
                            <span className="transition-transform group-hover:scale-110">{item.icon}</span>
                            {item.label}
                        </NavLink>
                    ))}
                </nav>

                {/* Footer */}
                <div className="p-4 border-t border-clawdi-border">
                    <div className="flex items-center gap-2 text-xs text-clawdi-text-muted">
                        <div className="w-2 h-2 rounded-full bg-clawdi-green animate-pulse" />
                        System Online
                    </div>
                </div>
            </aside>
        </>
    )
}
