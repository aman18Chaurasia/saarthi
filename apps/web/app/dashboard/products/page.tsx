"use client";

import { useQuery } from "@tanstack/react-query";

export default function ProductsPage() {
  const { data } = useQuery({
    queryKey: ["analytics", "by_product"],
    queryFn: async () => {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/analytics/by_product`);
      return res.json();
    },
  });

  return (
    <div>
      <h1 className="text-2xl font-semibold text-gray-900 mb-6">Products Analytics</h1>

      <div className="bg-white shadow overflow-hidden sm:rounded-lg">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Product</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Calls</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Qualified Rate</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Avg Duration</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {data?.map((p: any) => (
              <tr key={p.product}>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{p.product}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{p.call_count}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{p.qualified_rate}%</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{p.avg_duration}s</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
