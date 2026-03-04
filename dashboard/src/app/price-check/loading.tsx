export default function PriceCheckLoading() {
    return (
        <div className="max-w-5xl mx-auto p-4 md:p-8">
            {/* Header skeleton */}
            <div className="flex items-center justify-between py-6 border-b border-[var(--border)] mb-8">
                <div className="flex items-center gap-4">
                    <div className="h-4 w-20 bg-[var(--card-bg)] rounded animate-pulse" />
                    <div className="h-7 w-48 bg-[var(--card-bg)] rounded animate-pulse" />
                </div>
                <div className="h-8 w-24 bg-[var(--card-bg)] rounded-full animate-pulse" />
            </div>

            {/* Stat cards skeleton */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
                {[...Array(4)].map((_, i) => (
                    <div
                        key={i}
                        className="bg-[var(--card-bg)] border border-[var(--border)] rounded-2xl p-5 text-center"
                    >
                        <div className="h-9 w-12 mx-auto bg-[var(--bg-primary)] rounded animate-pulse mb-2" />
                        <div className="h-3 w-16 mx-auto bg-[var(--bg-primary)] rounded animate-pulse" />
                    </div>
                ))}
            </div>

            {/* Item card skeletons */}
            <div className="space-y-4">
                {[...Array(3)].map((_, i) => (
                    <div
                        key={i}
                        className="border border-[var(--border)] bg-[var(--card-bg)] rounded-2xl p-5"
                        style={{ animationDelay: `${i * 150}ms` }}
                    >
                        <div className="flex items-center justify-between mb-4">
                            <div className="flex items-center gap-3">
                                <div className="h-5 w-5 bg-[var(--bg-primary)] rounded-full animate-pulse" />
                                <div>
                                    <div className="h-4 w-32 bg-[var(--bg-primary)] rounded animate-pulse mb-1" />
                                    <div className="h-3 w-16 bg-[var(--bg-primary)] rounded animate-pulse" />
                                </div>
                            </div>
                            <div className="h-5 w-24 bg-[var(--bg-primary)] rounded-full animate-pulse" />
                        </div>
                        <div className="grid grid-cols-3 gap-4 mb-4">
                            {[...Array(3)].map((_, j) => (
                                <div key={j} className="text-center">
                                    <div className="h-3 w-14 mx-auto bg-[var(--bg-primary)] rounded animate-pulse mb-2" />
                                    <div className="h-6 w-16 mx-auto bg-[var(--bg-primary)] rounded animate-pulse" />
                                </div>
                            ))}
                        </div>
                        <div className="h-2.5 bg-[var(--bg-primary)] rounded-full animate-pulse" />
                    </div>
                ))}
            </div>
        </div>
    );
}
