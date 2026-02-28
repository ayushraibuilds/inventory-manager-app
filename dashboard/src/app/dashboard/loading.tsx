export default function DashboardLoading() {
    return (
        <div className="max-w-7xl mx-auto p-4 md:p-8 animate-pulse">
            {/* Header skeleton */}
            <div className="flex justify-between items-center py-6 border-b border-[var(--border)] mb-8">
                <div className="h-8 w-56 bg-[var(--card-bg)] rounded-xl" />
                <div className="flex gap-3">
                    <div className="h-8 w-24 bg-[var(--card-bg)] rounded-full" />
                    <div className="h-8 w-24 bg-[var(--card-bg)] rounded-full" />
                    <div className="h-8 w-20 bg-[var(--card-bg)] rounded-full" />
                </div>
            </div>
            {/* Stat cards */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mb-8">
                {[1, 2, 3].map(i => <div key={i} className="h-28 bg-[var(--card-bg)] rounded-2xl border border-[var(--border)]" />)}
            </div>
            {/* Table + Sidebar */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div className="lg:col-span-2 h-96 bg-[var(--card-bg)] rounded-2xl border border-[var(--border)]" />
                <div className="space-y-6">
                    <div className="h-64 bg-[var(--card-bg)] rounded-2xl border border-[var(--border)]" />
                    <div className="h-36 bg-[var(--card-bg)] rounded-2xl border border-[var(--border)]" />
                </div>
            </div>
        </div>
    );
}
