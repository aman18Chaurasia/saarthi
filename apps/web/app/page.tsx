import Link from "next/link";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6 p-24">
      <div className="text-center">
        <h1 className="text-4xl font-bold tracking-tight">SAARTHI</h1>
        <p className="mt-2 text-lg text-muted-foreground">
          Self-Adaptive AI for Responsible Tele-conversational Human Interaction in BFSI
        </p>
      </div>
      <Link
        href="/call"
        className="px-6 py-3 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 font-medium text-lg"
      >
        Start Voice Call Demo
      </Link>
      <p className="text-xs text-muted-foreground">
        Phase 1: Personal Loan Qualification
      </p>
    </main>
  );
}
