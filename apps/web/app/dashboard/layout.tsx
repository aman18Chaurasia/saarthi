import { BarChart3, History, LayoutDashboard } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";

const links = [
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
  { href: "/dashboard/calls", label: "Calls", icon: History },
  { href: "/dashboard/products", label: "Products", icon: BarChart3 },
];

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-[#eef2ef] text-[#111816]">
      <header className="border-b border-[#cbd6d0] bg-[#11231f] text-white">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-5 sm:px-6 lg:flex-row lg:items-center lg:justify-between lg:px-8">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-[#99c8b5]">
              SAARTHI Command
            </p>
            <h1 className="mt-1 text-2xl font-semibold tracking-tight">BFSI Voice Analytics</h1>
          </div>
          <nav className="flex flex-wrap gap-2">
            {links.map(({ href, label, icon: Icon }) => (
              <Link
                key={href}
                href={href}
                className="inline-flex h-10 items-center gap-2 rounded-md border border-white/15 px-3 text-sm font-medium text-white/85 transition hover:bg-white/10 hover:text-white"
              >
                <Icon className="h-4 w-4" aria-hidden="true" />
                {label}
              </Link>
            ))}
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">{children}</main>
    </div>
  );
}
