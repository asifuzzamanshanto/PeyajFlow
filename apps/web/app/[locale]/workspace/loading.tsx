"use client";

import { usePathname } from "next/navigation";

export default function WorkspaceLoading() {
  const locale = usePathname().split("/")[1];
  return (
    <main className="work-main" aria-busy="true">
      <p className="work-panel" role="status">
        {locale === "en" ? "Loading workspace…" : "ওয়ার্কস্পেস লোড হচ্ছে…"}
      </p>
    </main>
  );
}
