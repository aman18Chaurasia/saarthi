import {
  BarChart3,
  BrainCircuit,
  History,
  LayoutDashboard,
  Home as HomeIcon,
  Phone,
  Radar,
  Route,
  SatelliteDish,
} from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";

const links = [
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
  { href: "/dashboard/calls", label: "Calls", icon: History },
  { href: "/dashboard/products", label: "Products", icon: BarChart3 },
  { href: "/dashboard/ops", label: "Ops", icon: BrainCircuit },
  { href: "/dashboard/supervisor", label: "Supervisor", icon: SatelliteDish },
  { href: "/dashboard/recommend", label: "Recommend", icon: Route },
  { href: "/dashboard/evals", label: "Evals", icon: Radar },
];

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-100">
      <header className="border-b border-slate-200 bg-white shadow-sm">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-5 sm:px-6 lg:flex-row lg:items-center lg:justify-between lg:px-8">
          <div className="flex items-center gap-4">
            <Link href="/" className="p-2 hover:bg-slate-100 rounded-lg transition-colors">
              <HomeIcon className="h-5 w-5 text-slate-700" />
            </Link>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-primary">
                SAARTHI Dashboard
              </p>
              <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900">
                Voice Analytics & Insights
              </h1>
            </div>
          </div>
          <div className="flex gap-2">
            <nav className="flex flex-wrap gap-2">
              {links.map(({ href, label, icon: Icon }) => (
                <Link
                  key={href}
                  href={href}
                  className="inline-flex h-10 items-center gap-2 rounded-lg border border-slate-200 px-4 text-sm font-medium text-slate-700 transition hover:bg-slate-50 hover:text-slate-900 hover:border-primary"
                >
                  <Icon className="h-4 w-4" aria-hidden="true" />
                  {label}
                </Link>
              ))}
            </nav>
            <Link
              href="/call?product=personal_loan"
              className="inline-flex h-10 items-center gap-2 rounded-lg bg-primary text-primary-foreground px-4 text-sm font-semibold transition hover:bg-primary/90"
            >
              <Phone className="h-4 w-4" />
              Test Call
            </Link>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">{children}</main>
    </div>
  );
}
