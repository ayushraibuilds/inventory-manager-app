export default function Loading() {
    return (
        <div className="max-w-7xl mx-auto p-4 md:p-8 animate-pulse">
            <div className="h-10 w-48 bg-[var(--card-hover)] rounded-md mb-8"></div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                {[1, 2, 3].map(i => (
                    <div key={i} className="h-24 bg-[var(--card-bg)] border border-[var(--border)] rounded-2xl"></div>
                ))}
            </div>
            <div className="h-96 bg-[var(--card-bg)] border border-[var(--border)] rounded-2xl"></div>
        </div>
    );
}
