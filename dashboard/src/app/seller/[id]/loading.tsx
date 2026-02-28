export default function Loading() {
    return (
        <div className="max-w-3xl mx-auto p-4 md:p-8 animate-pulse">
            <div className="h-8 w-32 bg-[var(--card-hover)] rounded-md mb-8"></div>
            <div className="h-[500px] bg-[var(--card-bg)] border border-[var(--border)] rounded-2xl flex flex-col gap-6 p-8">
                <div className="h-10 w-48 bg-[var(--card-hover)] rounded-md"></div>
                <div className="h-12 bg-[var(--card-hover)] opacity-50 rounded-lg"></div>
                <div className="h-24 bg-[var(--card-hover)] opacity-50 rounded-lg"></div>
                <div className="grid grid-cols-2 gap-6 mt-4">
                    <div className="h-12 bg-[var(--card-hover)] opacity-50 rounded-lg"></div>
                    <div className="h-12 bg-[var(--card-hover)] opacity-50 rounded-lg"></div>
                </div>
                <div className="h-12 bg-[var(--card-hover)] opacity-50 rounded-lg mt-auto"></div>
            </div>
        </div>
    );
}
