"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

export default function CallHistoryPage() {
  const [product, setProduct] = useState("");
  const [outcome, setOutcome] = useState("");

  const { data } = useQuery({
    queryKey: ["calls", product, outcome],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (product) params.set("product", product);
      if (outcome) params.set("outcome", outcome);
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/calls?${params}`);
      return res.json();
    },
  });

  return (
    <div>
      <h1 className="text-2xl font-semibold text-gray-900 mb-6">Call History</h1>

      <div className="mb-4 flex gap-4">
        <select value={product} onChange={(e) => setProduct(e.target.value)} className="rounded border-gray-300">
          <option value="">All Products</option>
          <option value="personal_loan">Personal Loan</option>
          <option value="home_loan">Home Loan</option>
          <option value="education_loan">Education Loan</option>
        </select>

        <select value={outcome} onChange={(e) => setOutcome(e.target.value)} className="rounded border-gray-300">
          <option value="">All Outcomes</option>
          <option value="qualified">Qualified</option>
          <option value="not_qualified">Not Qualified</option>
          <option value="dropped">Dropped</option>
        </select>
      </div>

      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <div className="px-4 py-3 text-sm text-gray-500">
          {data?.total ?? 0} calls found
        </div>
      </div>
    </div>
  );
}
