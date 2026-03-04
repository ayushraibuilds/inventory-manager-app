"use client";

import { motion } from "framer-motion";

interface SparklineProps {
    data: number[];
    color?: string;
    height?: number;
    width?: number;
}

export default function Sparkline({ data, color = "#58a6ff", height = 32, width = 120 }: SparklineProps) {
    if (!data || data.length < 2) {
        return (
            <div style={{ width, height }} className="flex items-center justify-center">
                <span className="text-[10px] text-[var(--text-muted)]">No data</span>
            </div>
        );
    }

    const max = Math.max(...data);
    const min = Math.min(...data);
    const range = max - min || 1;
    const padding = 2;
    const usableHeight = height - padding * 2;
    const stepX = (width - padding * 2) / (data.length - 1);

    const points = data.map((v, i) => ({
        x: padding + i * stepX,
        y: padding + usableHeight - ((v - min) / range) * usableHeight,
    }));

    const pathD = points.map((p, i) => (i === 0 ? `M ${p.x} ${p.y}` : `L ${p.x} ${p.y}`)).join(" ");

    // Gradient fill path
    const fillD = `${pathD} L ${points[points.length - 1].x} ${height} L ${points[0].x} ${height} Z`;

    const trend = data[data.length - 1] - data[0];
    const trendColor = trend > 0 ? "#22c55e" : trend < 0 ? "#ef4444" : color;

    return (
        <motion.svg
            width={width}
            height={height}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="block"
        >
            <defs>
                <linearGradient id={`spark-grad-${color.replace("#", "")}`} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={trendColor} stopOpacity={0.3} />
                    <stop offset="100%" stopColor={trendColor} stopOpacity={0.02} />
                </linearGradient>
            </defs>
            <path d={fillD} fill={`url(#spark-grad-${color.replace("#", "")})`} />
            <path d={pathD} fill="none" stroke={trendColor} strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" />
            <circle cx={points[points.length - 1].x} cy={points[points.length - 1].y} r={2.5} fill={trendColor} />
        </motion.svg>
    );
}
