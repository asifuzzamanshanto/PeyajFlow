"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export default function WorkspaceError({ reset }: { reset: () => void }) {
  const locale = usePathname().split("/")[1] === "en" ? "en" : "bn";
  return (
    <main className="work-main">
      <section className="work-panel" role="alert">
        <h1>
          {locale === "en"
            ? "Workspace unavailable"
            : "ওয়ার্কস্পেস এখন পাওয়া যাচ্ছে না"}
        </h1>
        <div className="work-row">
          <button className="refresh" type="button" onClick={reset}>
            {locale === "en" ? "Try again" : "আবার চেষ্টা করুন"}
          </button>
          <Link className="work-link" href={`/${locale}/workspace`}>
            {locale === "en" ? "Back to workspace" : "ওয়ার্কস্পেসে ফিরুন"}
          </Link>
        </div>
      </section>
    </main>
  );
}
