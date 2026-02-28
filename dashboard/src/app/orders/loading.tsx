export default function OrdersLoading() {
    return (
        <div className="max-w-5xl mx-auto p-4 md:p-8 animate-pulse">
            <div className="flex justify-between items-center py-6 border-b border-[var(--border)] mb-8">
                <div className="flex items-center gap-4">
                    <div className="w-9 h-9 bg-[var(--card-bg)] rounded-lg border border-[var(--border)]" />
                    <div className="h-7 w-24 bg-[var(--card-bg)] rounded-xl" />
                </div>
                <div className="flex gap-3">
                    <div className="h-8 w-28 bg-[var(--card-bg)] rounded-full" />
                    <div className="w-9 h-9 bg-[var(--card-bg)] rounded-lg border border-[var(--border)]" />
                </div>
            </div>
            <div className="space-y-4">
                {[1, 2, 3, 4].map(i => (
                    <div key={i} className="h-32 bg-[var(--card-bg)] rounded-2xl border border-[var(--border)]" />
                ))}
            </div>
        </div>
    );
}
