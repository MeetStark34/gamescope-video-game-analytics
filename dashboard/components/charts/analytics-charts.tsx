"use client";

import {
  Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, ComposedChart,
  Line, LineChart, ReferenceLine, ResponsiveContainer, Scatter, ScatterChart,
  Tooltip, XAxis, YAxis,
} from "recharts";
import type { CriticPoint, GenreAffinity, PlatformEvolution, RegionalSales, RegionalYearDivergence } from "@/lib/types";
import { formatNumber } from "@/lib/analytics-data";
import { useReducedMotion } from "@/lib/use-reduced-motion";

const palette = ["var(--chart-1)", "var(--chart-2)", "var(--chart-3)", "var(--chart-4)"];
const tooltipStyle = { borderRadius: 10, border: "1px solid var(--color-line)", backgroundColor: "var(--color-surface)", color: "var(--color-ink)", boxShadow: "0 8px 24px rgb(20 24 32 / 10%)", fontSize: 12 };
const axisStyle = { fill: "var(--color-muted)", fontSize: 11 };
const compact = (value: number) => formatNumber(value, value >= 1000 ? 0 : 1);

export function TrendChart<T extends object>({ data, titleKey = "year", salesKey = "global_sales_total", countKey = "games_released", salesLabel = "Global sales", countLabel = "Game records", onSelectYear }: {
  data: T[];
  titleKey?: string;
  salesKey?: string;
  countKey?: string;
  salesLabel?: string;
  countLabel?: string;
  onSelectYear?: (year: number) => void;
}) {
  const reducedMotion = useReducedMotion();
  const handleSelect = (state: unknown) => {
    const label = (state as { activeLabel?: unknown } | null)?.activeLabel;
    const year = Number(label);
    if (label != null && Number.isFinite(year)) onSelectYear?.(year);
  };
  return (
    <div className={onSelectYear ? "selectable-chart" : ""}><ResponsiveContainer width="100%" height="100%">
      <ComposedChart data={data} onClick={handleSelect} margin={{ top: 10, right: 14, left: 0, bottom: 0 }}>
        <defs><linearGradient id="salesFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor={palette[0]} stopOpacity={0.2} /><stop offset="95%" stopColor={palette[0]} stopOpacity={0.015} /></linearGradient></defs>
        <CartesianGrid stroke="var(--chart-grid)" vertical={false} />
        <XAxis dataKey={titleKey} tick={axisStyle} tickLine={false} axisLine={false} minTickGap={20} />
        <YAxis yAxisId="sales" tick={axisStyle} tickLine={false} axisLine={false} tickFormatter={compact} width={46} />
        <YAxis yAxisId="count" orientation="right" tick={axisStyle} tickLine={false} axisLine={false} tickFormatter={compact} width={40} />
        <Tooltip contentStyle={tooltipStyle} formatter={(value, name) => [formatNumber(Number(value), 2), name === salesKey ? salesLabel : countLabel]} labelFormatter={(label) => `Year ${label}`} />
        <Area yAxisId="sales" type="monotone" dataKey={salesKey} stroke={palette[0]} strokeWidth={2.5} fill="url(#salesFill)" connectNulls isAnimationActive={!reducedMotion} animationDuration={350} />
        <Line yAxisId="count" type="monotone" dataKey={countKey} stroke={palette[1]} strokeWidth={2} dot={false} connectNulls isAnimationActive={!reducedMotion} animationDuration={350} />
      </ComposedChart>
    </ResponsiveContainer></div>
  );
}

export function RankedBarChart({ data, categoryKey, valueKey, color = "var(--chart-1)", height = 320, horizontal = true, onSelect, selectedValue, categoryLabel, valueLabel }: {
  data: Array<Record<string, string | number | null>>;
  categoryKey: string;
  valueKey: string;
  color?: string;
  height?: number;
  horizontal?: boolean;
  onSelect?: (value: string) => void;
  selectedValue?: string;
  categoryLabel?: string;
  valueLabel?: string;
}) {
  const reducedMotion = useReducedMotion();
  const handleBarClick = (item: unknown) => {
    const entry = item && typeof item === "object" ? item as Record<string, unknown> : {};
    const row = entry.payload && typeof entry.payload === "object" ? entry.payload as Record<string, unknown> : entry;
    const value = row[categoryKey];
    if (value != null) onSelect?.(String(value));
  };
  const cells = data.map((row, index) => <Cell key={`${String(row[categoryKey])}-${index}`} fill={color} fillOpacity={selectedValue && selectedValue !== String(row[categoryKey]) ? 0.28 : 0.86} />);
  const tooltipProps = {
    contentStyle: tooltipStyle,
    formatter: (value: unknown): [string, string] => [formatNumber(Number(value), 2), valueLabel ?? valueKey],
    labelFormatter: (label: unknown) => `${categoryLabel ?? "Category"}: ${String(label)}`,
  };
  const chart = horizontal ? (
    <BarChart data={data} layout="vertical" margin={{ top: 2, right: 20, left: 12, bottom: 2 }}>
      <CartesianGrid stroke="var(--chart-grid)" horizontal={false} />
      <XAxis type="number" tick={axisStyle} tickLine={false} axisLine={false} tickFormatter={compact} />
      <YAxis type="category" dataKey={categoryKey} width={118} tick={axisStyle} tickLine={false} axisLine={false} />
      <Tooltip {...tooltipProps} />
      <Bar dataKey={valueKey} fill={color} radius={[0, 5, 5, 0]} maxBarSize={22} onClick={handleBarClick} cursor={onSelect ? "pointer" : "default"} isAnimationActive={!reducedMotion} animationDuration={350}>{cells}</Bar>
    </BarChart>
  ) : (
    <BarChart data={data} margin={{ top: 8, right: 6, left: 0, bottom: 35 }}>
      <CartesianGrid stroke="var(--chart-grid)" vertical={false} />
      <XAxis dataKey={categoryKey} tick={axisStyle} tickLine={false} axisLine={false} angle={-25} textAnchor="end" interval={0} />
      <YAxis tick={axisStyle} tickLine={false} axisLine={false} tickFormatter={compact} width={48} />
      <Tooltip {...tooltipProps} />
      <Bar dataKey={valueKey} fill={color} radius={[5, 5, 0, 0]} maxBarSize={34} onClick={handleBarClick} cursor={onSelect ? "pointer" : "default"} isAnimationActive={!reducedMotion} animationDuration={350}>{cells}</Bar>
    </BarChart>
  );
  return <ResponsiveContainer width="100%" height={height}>{chart}</ResponsiveContainer>;
}

export function RegionalSalesChart({ data, onSelect, selectedRegion }: { data: RegionalSales[]; onSelect?: (region: string) => void; selectedRegion?: string }) {
  const reducedMotion = useReducedMotion();
  const colors: Record<string, string> = { "North America": palette[0], Europe: palette[2], Japan: palette[1], Other: palette[3] };
  return <ResponsiveContainer width="100%" height="100%"><BarChart data={data} margin={{ top: 8, right: 15, left: 3, bottom: 2 }}>
    <CartesianGrid stroke="var(--chart-grid)" vertical={false} /><XAxis dataKey="region" tick={axisStyle} tickLine={false} axisLine={false} />
    <YAxis tick={axisStyle} tickLine={false} axisLine={false} tickFormatter={compact} width={48} />
    <Tooltip contentStyle={tooltipStyle} formatter={(value) => [formatNumber(Number(value), 2), "Regional sales"]} labelFormatter={(label) => `${label} sales`} />
    <Bar dataKey="sales_total" radius={[5, 5, 0, 0]} maxBarSize={60} cursor={onSelect ? "pointer" : "default"} isAnimationActive={!reducedMotion} animationDuration={350} onClick={(item: unknown) => {
      const entry = item && typeof item === "object" ? item as Record<string, unknown> : {};
      const payload = entry.payload && typeof entry.payload === "object" ? entry.payload as Record<string, unknown> : entry;
      if (payload.region != null) onSelect?.(String(payload.region));
    }}>{data.map((item) => <Cell key={item.region} fill={colors[item.region] ?? palette[0]} fillOpacity={selectedRegion && selectedRegion !== item.region ? 0.3 : 0.86} />)}</Bar>
  </BarChart></ResponsiveContainer>;
}

export function PlatformTrendChart({ data }: { data: PlatformEvolution[] }) {
  const reducedMotion = useReducedMotion();
  return <ResponsiveContainer width="100%" height="100%"><LineChart data={data} margin={{ top: 8, right: 14, left: 0, bottom: 0 }}>
    <CartesianGrid stroke="var(--chart-grid)" vertical={false} /><XAxis dataKey="year" tick={axisStyle} tickLine={false} axisLine={false} />
    <YAxis yAxisId="sales" tick={axisStyle} tickLine={false} axisLine={false} tickFormatter={compact} width={44} />
    <YAxis yAxisId="count" orientation="right" tick={axisStyle} tickLine={false} axisLine={false} tickFormatter={compact} width={38} />
    <Tooltip contentStyle={tooltipStyle} formatter={(value) => formatNumber(Number(value), 2)} labelFormatter={(label) => `Year ${label}`} />
    <Line type="monotone" dataKey="global_sales_total" name="Global sales" yAxisId="sales" stroke={palette[0]} strokeWidth={2.5} dot={false} connectNulls isAnimationActive={!reducedMotion} animationDuration={350} />
    <Line type="monotone" dataKey="games_released" name="Releases" yAxisId="count" stroke={palette[1]} strokeWidth={2} dot={false} isAnimationActive={!reducedMotion} animationDuration={350} />
  </LineChart></ResponsiveContainer>;
}

export function YearDivergenceChart({ data, onSelectYear }: { data: RegionalYearDivergence[]; onSelectYear?: (year: number) => void }) {
  const reducedMotion = useReducedMotion();
  const handleSelect = (state: unknown) => {
    const label = (state as { activeLabel?: unknown } | null)?.activeLabel;
    const year = Number(label);
    if (label != null && Number.isFinite(year)) onSelectYear?.(year);
  };
  return <div className={onSelectYear ? "selectable-chart" : ""}><ResponsiveContainer width="100%" height="100%"><LineChart data={data} onClick={handleSelect} margin={{ top: 8, right: 14, left: 0, bottom: 0 }}>
    <CartesianGrid stroke="var(--chart-grid)" vertical={false} /><XAxis dataKey="year" tick={axisStyle} tickLine={false} axisLine={false} />
    <YAxis domain={[0, 1]} tick={axisStyle} tickLine={false} axisLine={false} width={38} />
    <Tooltip contentStyle={tooltipStyle} formatter={(value) => formatNumber(Number(value), 3)} labelFormatter={(label) => `Year ${label}`} />
    <Line type="monotone" dataKey="mean_pairwise_divergence" name="Mean pairwise divergence" stroke={palette[1]} strokeWidth={2.5} dot={false} connectNulls isAnimationActive={!reducedMotion} animationDuration={350} />
  </LineChart></ResponsiveContainer></div>;
}

export function CriticSalesScatter({ data }: { data: CriticPoint[] }) {
  const reducedMotion = useReducedMotion();
  return <ResponsiveContainer width="100%" height="100%"><ScatterChart margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
    <CartesianGrid stroke="var(--chart-grid)" /><XAxis type="number" dataKey="critic_score" name="Critic score" domain={[0, 10]} tick={axisStyle} tickLine={false} axisLine={false} />
    <YAxis type="number" dataKey="total_sales" name="Total sales" tick={axisStyle} tickLine={false} axisLine={false} tickFormatter={compact} width={45} />
    <Tooltip contentStyle={tooltipStyle} cursor={{ strokeDasharray: "3 3" }} formatter={(value, name) => [formatNumber(Number(value), 2), name]} />
    <Scatter data={data} fill={palette[0]} fillOpacity={0.42} name="Game records" isAnimationActive={!reducedMotion} animationDuration={350} />
    <ReferenceLine x={8} stroke={palette[1]} strokeDasharray="4 4" />
  </ScatterChart></ResponsiveContainer>;
}

export function AffinityHeatmap({ data }: { data: GenreAffinity[] }) {
  const regions = [...new Set(data.map((item) => item.region))];
  const genres = [...new Set(data.map((item) => item.genre))];
  const byKey = new Map(data.map((item) => [`${item.genre}|${item.region}`, item]));
  return (
    <div className="heatmap-scroll"><table className="heatmap-table"><thead><tr><th>Genre</th>{regions.map((region) => <th key={region}>{region}</th>)}</tr></thead>
      <tbody>{genres.map((genre) => <tr key={genre}><th>{genre}</th>{regions.map((region) => {
        const value = byKey.get(`${genre}|${region}`)?.affinity_index ?? null;
        const bounded = value == null ? 0 : Math.max(-1, Math.min(1, (value - 1) / 2));
        const background = value == null ? "#f2f4f7" : bounded >= 0
          ? `rgba(39, 155, 126, ${0.1 + Math.abs(bounded) * 0.62})`
          : `rgba(218, 119, 82, ${0.1 + Math.abs(bounded) * 0.62})`;
        return <td key={region} style={{ backgroundColor: background }} title={`${genre} · ${region} · affinity ${value?.toFixed(2) ?? "unavailable"}`}>{value == null ? "—" : value.toFixed(2)}</td>;
      })}</tr>)}</tbody>
    </table><div className="heatmap-legend"><span><i className="legend-under" /> Under-indexed</span><span><i className="legend-neutral" /> Baseline = 1</span><span><i className="legend-over" /> Over-indexed</span></div></div>
  );
}
