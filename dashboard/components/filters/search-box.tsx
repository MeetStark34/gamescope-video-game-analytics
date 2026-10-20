import { Search } from "lucide-react";

export function SearchBox({ value, onChange, label = "Search records", placeholder = "Search…" }: {
  value: string;
  onChange: (value: string) => void;
  label?: string;
  placeholder?: string;
}) {
  return (
    <label className="search-box">
      <span className="sr-only">{label}</span>
      <Search size={16} aria-hidden="true" />
      <input type="search" value={value} onChange={(event) => onChange(event.target.value)} placeholder={placeholder} />
    </label>
  );
}
