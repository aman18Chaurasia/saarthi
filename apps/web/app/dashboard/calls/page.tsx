"use client";

import { useQuery } from "@tanstack/react-query";
import { Search, ChevronLeft, ChevronRight } from "lucide-react";
import type { ReactNode } from "react";
import { useMemo, useState } from "react";
import { type CallDetail, type CallsResponse, fetchJson, productLabel } from "@/lib/api";

const products = [
  "personal_loan",
  "home_loan",
  "education_loan",
  "gold_loan",
  "credit_card",
  "unsecured_loan",
  "loan_against_property",
  "commercial_vehicle_loan",
  "four_wheeler_loan",
  "msme_business_loan",
];

const ITEMS_PER_PAGE = 10;

export default function CallHistoryPage() {
  const [product, setProduct] = useState("");
  const [outcome, setOutcome] = useState("");
  const [selectedCallId, setSelectedCallId] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);

  const queryPath = useMemo(() => {
    const params = new URLSearchParams();
    if (product) params.set("product", product);
    if (outcome) params.set("outcome", outcome);
    return `/api/calls${params.toString() ? `?${params}` : ""}`;
  }, [product, outcome]);

  const { data, isLoading } = useQuery({
    queryKey: ["calls", product, outcome],
    queryFn: () => fetchJson<CallsResponse>(queryPath),
  });

  const { data: detail, isLoading: detailLoading } = useQuery({
    queryKey: ["call-detail", selectedCallId],
    queryFn: () => fetchJson<CallDetail>(`/api/calls/${selectedCallId}`),
    enabled: Boolean(selectedCallId),
  });

  // Pagination logic
  const totalCalls = data?.calls.length ?? 0;
  const totalPages = Math.ceil(totalCalls / ITEMS_PER_PAGE);
  const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
  const endIndex = startIndex + ITEMS_PER_PAGE;
  const paginatedCalls = data?.calls.slice(startIndex, endIndex) ?? [];

  // Reset to page 1 when filters change
  useMemo(() => {
    setCurrentPage(1);
  }, [product, outcome]);

  const handlePrevPage = () => {
    setCurrentPage((prev) => Math.max(1, prev - 1));
  };

  const handleNextPage = () => {
    setCurrentPage((prev) => Math.min(totalPages, prev + 1));
  };

  const handlePageClick = (page: number) => {
    setCurrentPage(page);
  };

  // Generate page numbers to display
  const getPageNumbers = () => {
    const pages: (number | string)[] = [];

    if (totalPages <= 7) {
      // Show all pages if 7 or fewer
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      // Always show first page
      pages.push(1);

      if (currentPage > 3) {
        pages.push('...');
      }

      // Show pages around current page
      for (let i = Math.max(2, currentPage - 1); i <= Math.min(totalPages - 1, currentPage + 1); i++) {
        pages.push(i);
      }

      if (currentPage < totalPages - 2) {
        pages.push('...');
      }

      // Always show last page
      pages.push(totalPages);
    }

    return pages;
  };

  return (
    <div className="space-y-5">
      <section className="rounded-md border border-[#c9d6cf] bg-white p-4 shadow-sm">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="text-xl font-semibold">Call History</h2>
            <p className="text-sm text-[#5d6b65]">
              {totalCalls > 0
                ? `Showing ${startIndex + 1}-${Math.min(endIndex, totalCalls)} of ${totalCalls} calls`
                : '0 matching calls'
              }
            </p>
          </div>
          <div className="flex flex-col gap-3 sm:flex-row">
            <FilterSelect value={product} onChange={setProduct} label="Product">
              <option value="">All products</option>
              {products.map((item) => (
                <option key={item} value={item}>
                  {productLabel(item)}
                </option>
              ))}
            </FilterSelect>
            <FilterSelect value={outcome} onChange={setOutcome} label="Outcome">
              <option value="">All outcomes</option>
              <option value="qualified">Qualified</option>
              <option value="not_qualified">Not qualified</option>
              <option value="dropped">Dropped</option>
              <option value="no_consent">No consent</option>
              <option value="callback_requested">Callback requested</option>
            </FilterSelect>
          </div>
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_380px]">
        <div className="overflow-hidden rounded-md border border-[#c9d6cf] bg-white shadow-sm">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-[#d7e0db] text-sm">
              <thead className="bg-[#f5f7f5] text-left text-xs uppercase tracking-[0.12em] text-[#5d6b65]">
                <tr>
                  <th className="px-4 py-3">Call</th>
                  <th className="px-4 py-3">Product</th>
                  <th className="px-4 py-3">Outcome</th>
                  <th className="px-4 py-3">Duration</th>
                  <th className="px-4 py-3">Turns</th>
                  <th className="px-4 py-3">Started</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#edf1ee]">
                {paginatedCalls.map((call) => {
                  const isSelected = selectedCallId === call.call_id;
                  return (
                    <tr
                      key={call.call_id}
                      className={isSelected ? "bg-emerald-50" : "hover:bg-[#f8faf8]"}
                    >
                      <td className="px-4 py-3 font-medium text-[#111816]">
                        <button
                          type="button"
                          onClick={() => setSelectedCallId(call.call_id)}
                          className="text-left hover:text-emerald-700"
                        >
                          {call.call_id}
                        </button>
                      </td>
                      <td className="px-4 py-3 text-[#5d6b65]">{productLabel(call.product)}</td>
                      <td className="px-4 py-3">
                        <span className="rounded-sm bg-[#e7f0eb] px-2 py-1 text-xs font-medium text-[#22533d]">
                          {call.outcome ?? "unknown"}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-[#5d6b65]">{call.duration_s ?? 0}s</td>
                      <td className="px-4 py-3 text-[#5d6b65]">{call.turn_count}</td>
                      <td className="px-4 py-3 text-[#5d6b65]">
                        {new Date(call.started_at).toLocaleString()}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {!isLoading && data?.calls.length === 0 && (
            <div className="flex items-center justify-center gap-2 px-4 py-10 text-sm text-[#5d6b65]">
              <Search className="h-4 w-4" aria-hidden="true" />
              No calls match the current filters.
            </div>
          )}

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between border-t border-[#d7e0db] px-4 py-3">
              <button
                onClick={handlePrevPage}
                disabled={currentPage === 1}
                className="flex items-center gap-1 px-3 py-2 text-sm font-medium text-[#5d6b65] hover:text-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="h-4 w-4" />
                Previous
              </button>

              <div className="flex items-center gap-1">
                {getPageNumbers().map((page, idx) => (
                  typeof page === 'number' ? (
                    <button
                      key={idx}
                      onClick={() => handlePageClick(page)}
                      className={`px-3 py-1 text-sm font-medium rounded ${
                        currentPage === page
                          ? 'bg-emerald-600 text-white'
                          : 'text-[#5d6b65] hover:bg-[#f5f7f5]'
                      }`}
                    >
                      {page}
                    </button>
                  ) : (
                    <span key={idx} className="px-2 text-[#5d6b65]">
                      {page}
                    </span>
                  )
                ))}
              </div>

              <button
                onClick={handleNextPage}
                disabled={currentPage === totalPages}
                className="flex items-center gap-1 px-3 py-2 text-sm font-medium text-[#5d6b65] hover:text-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          )}
        </div>

        <aside className="rounded-md border border-[#c9d6cf] bg-white p-5 shadow-sm">
          {!selectedCallId && (
            <p className="text-sm text-slate-500">
              Select a call to inspect lead score, objections, follow-up guidance, and transcript.
            </p>
          )}

          {selectedCallId && detailLoading && <p className="text-sm text-slate-500">Loading call detail...</p>}

          {detail && (
            <div className="space-y-5">
              <div>
                <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Selected Call</p>
                <h3 className="mt-2 text-lg font-semibold text-slate-900">{detail.call_id}</h3>
                <p className="text-sm text-slate-500">{productLabel(detail.product)}</p>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <Metric label="Lead Score" value={detail.intelligence.lead_score} />
                <Metric label="Priority" value={detail.intelligence.priority} />
                <Metric label="Sentiment" value={detail.intelligence.sentiment} />
                <Metric label="Turns" value={detail.turn_count} />
              </div>

              <div className="space-y-2">
                <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Recommended Action</p>
                <p className="text-sm text-slate-800">{detail.intelligence.follow_up_action}</p>
                {detail.intelligence.recommended_callback_window && (
                  <p className="text-sm text-emerald-700">
                    Callback window: {detail.intelligence.recommended_callback_window}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Summary</p>
                <p className="text-sm text-slate-800">{detail.intelligence.summary}</p>
              </div>

              <div className="space-y-2">
                <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Detected Objections</p>
                <div className="flex flex-wrap gap-2">
                  {detail.intelligence.objections.length ? (
                    detail.intelligence.objections.map((item) => (
                      <span
                        key={item}
                        className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700"
                      >
                        {item.replaceAll("_", " ")}
                      </span>
                    ))
                  ) : (
                    <span className="text-sm text-slate-500">No strong objections detected.</span>
                  )}
                </div>
              </div>

              <div className="space-y-2">
                <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Transcript Snapshot</p>
                <div className="max-h-72 space-y-2 overflow-y-auto rounded-md bg-slate-50 p-3">
                  {detail.transcript_redacted.slice(-8).map((turn, index) => (
                    <div key={`${turn.turn_index}-${index}`} className="text-sm">
                      <span className="font-medium text-slate-700">{turn.speaker}:</span>{" "}
                      <span className="text-slate-600">{turn.text}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </aside>
      </section>
    </div>
  );
}

function FilterSelect({
  value,
  onChange,
  label,
  children,
}: {
  value: string;
  onChange: (value: string) => void;
  label: string;
  children: ReactNode;
}) {
  return (
    <label className="flex flex-col gap-1 text-xs font-medium uppercase tracking-[0.12em] text-[#5d6b65]">
      {label}
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="h-10 min-w-44 rounded-md border border-[#c9d6cf] bg-white px-3 text-sm normal-case tracking-normal text-[#111816]"
      >
        {children}
      </select>
    </label>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-md border border-slate-200 bg-slate-50 p-3">
      <p className="text-xs uppercase tracking-[0.14em] text-slate-500">{label}</p>
      <p className="mt-2 text-lg font-semibold text-slate-900">{value}</p>
    </div>
  );
}
