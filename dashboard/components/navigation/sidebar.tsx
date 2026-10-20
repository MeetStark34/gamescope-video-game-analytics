"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity, BarChart3, Building2, Database, Gamepad2, Gauge, LayoutDashboard,
  Map, PanelsTopLeft, Radar, Tags, TrendingUp,
} from "lucide-react";

const sections = [
  {
    title: "Workspace",
    links: [
      { href: "/overview", label: "Overview", icon: LayoutDashboard },
      { href: "/trends", label: "Market trends", icon: TrendingUp },
      { href: "/genres", label: "Genre analysis", icon: Tags },
      { href: "/platforms", label: "Platform analysis", icon: Gamepad2 },
      { href: "/regions", label: "Regional intelligence", icon: Map },
      { href: "/publishers", label: "Publishers", icon: Building2 },
    ],
  },
  {
    title: "Deep dives",
    links: [
      { href: "/market-power", label: "Market power", icon: Gauge },
      { href: "/divergence", label: "Regional divergence", icon: Radar },
      { href: "/advanced", label: "Advanced analysis", icon: Activity },
      { href: "/data-quality", label: "Data quality", icon: Database },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="sidebar" aria-label="Main navigation">
      <Link href="/overview" className="brand-lockup" aria-label="GameScope home">
        <span className="brand-mark"><PanelsTopLeft size={19} strokeWidth={2.2} /></span>
        <span><strong>GameScope</strong><small>SALES INTELLIGENCE</small></span>
      </Link>
      <div className="source-pill"><span className="status-dot" /> Primary source <b>vgsales</b></div>
      <nav className="sidebar-nav">
        {sections.map((section) => (
          <div className="nav-group" key={section.title}>
            <p className="nav-group-title">{section.title}</p>
            {section.links.map(({ href, label, icon: Icon }) => {
              const active = pathname === href || (href === "/overview" && pathname === "/");
              return (
                <Link key={href} href={href} className={`nav-link${active ? " active" : ""}`} aria-current={active ? "page" : undefined}>
                  <Icon size={17} strokeWidth={1.8} aria-hidden="true" />
                  <span>{label}</span>
                  {active && <span className="nav-active-mark" aria-hidden="true" />}
                </Link>
              );
            })}
          </div>
        ))}
      </nav>
      <div className="sidebar-foot">
        <Gamepad2 size={17} aria-hidden="true" />
        <span>Global games market<br /><b>Intelligence workspace</b></span>
      </div>
    </aside>
  );
}
