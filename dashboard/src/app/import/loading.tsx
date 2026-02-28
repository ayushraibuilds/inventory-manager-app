export default function ImportLoading() {
    return (
        <div className="max-w-3xl mx-auto p-4 md:p-8 animate-pulse">
            <div className="flex items-center gap-4 py-6 border-b border-[var(--border)] mb-8">
                <div className="w-9 h-9 bg-[var(--card-bg)] rounded-lg border border-[var(--border)]" />
                <div className="h-7 w-36 bg-[var(--card-bg)] rounded-xl" />
            </div>
            <div className="h-16 bg-[var(--card-bg)] rounded-xl border border-[var(--border)] mb-6" />
            <div className="space-y-3">
                {[1, 2, 3].map(i => (
                    <div key={i} className="h-40 bg-[var(--card-bg)] rounded-xl border border-[var(--border)]" />
                ))}
            </div>
            <div className="h-14 bg-[var(--card-bg)] rounded-xl border border-[var(--border)] mt-6" />
        </div>
    );
}
