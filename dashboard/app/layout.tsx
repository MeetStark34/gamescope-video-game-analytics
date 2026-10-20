import type { Metadata } from "next";
import { AppHeader } from "@/components/layout/app-header";
import { Sidebar } from "@/components/navigation/sidebar";
import { GlobalFilterBar } from "@/components/filters/global-filter-bar";
import { DashboardProvider } from "@/lib/dashboard-context";
import "./globals.css";

export const metadata: Metadata = {
  title: "GameScope · Video Game Sales Intelligence",
  description: "Source-aware analytics for global video game sales, publishers, platforms, regions, and market trends.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <a className="skip-link" href="#main-content">Skip to content</a>
        <DashboardProvider>
        <div className="app-shell">
          <Sidebar />
          <div className="workspace">
            <AppHeader />
            <GlobalFilterBar />
            <main className="main-content" id="main-content" tabIndex={-1}>{children}</main>
            <footer className="app-footer"><span>GameScope · Global Video Game Sales Intelligence</span><span>Analytics prepared in Python · UI built with Next.js</span></footer>
          </div>
        </div>
        </DashboardProvider>
      </body>
    </html>
  );
}
