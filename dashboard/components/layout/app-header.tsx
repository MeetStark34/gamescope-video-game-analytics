import { CircleHelp, Database } from "lucide-react";

export function AppHeader() {
  return (
    <header className="app-header">
      <div className="breadcrumb"><span>GameScope</span><span className="crumb-divider">/</span><b>Analytics workspace</b></div>
      <div className="header-meta">
        <span className="header-chip"><Database size={14} /> Python-prepared data</span>
        <a className="help-link" href="/data-quality" aria-label="View data quality notes"><CircleHelp size={17} /></a>
      </div>
    </header>
  );
}
