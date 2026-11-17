"use client";

import { useEffect, useRef, useState } from "react";
import type { Locale } from "../../lib/copy";
import { local } from "../../lib/workspace-copy";

const findings: Record<string, [string, string]> = {
  rot: ["সম্ভাব্য পচন বা ছাঁচ", "Possible visible rot or mold"],
  sprouting: ["সম্ভাব্য অঙ্কুর", "Possible sprouting"],
  damage: ["সম্ভাব্য আঘাতের দাগ", "Possible physical damage"],
  clear: ["দৃশ্যমান ত্রুটি ধরা পড়েনি", "No visible defect flagged"],
  uncertain: [
    "মডেল নিশ্চিত ফল দিতে পারেনি",
    "The model could not make a confident suggestion",
  ],
};

export function PhotoModel({ locale, src }: { locale: Locale; src: string }) {
  const worker = useRef<Worker | null>(null);
  const request = useRef<AbortController | null>(null);
  const [status, setStatus] = useState<"idle" | "running" | "failed">("idle");
  const [result, setResult] = useState<string | null>(null);
  const t = (bn: string, en: string) => local(locale, bn, en);
  useEffect(
    () => () => {
      request.current?.abort();
      worker.current?.terminate();
    },
    [],
  );

  async function analyze() {
    if (request.current) return;
    const controller = new AbortController();
    request.current = controller;
    setResult(null);
    setStatus("running");
    let timeout: ReturnType<typeof setTimeout> | undefined;
    const finish = (finding?: string) => {
      window.clearTimeout(timeout);
      if (controller.signal.aborted) return;
      request.current = null;
      worker.current?.terminate();
      worker.current = null;
      setResult(finding ?? null);
      setStatus(finding ? "idle" : "failed");
    };
    try {
      const response = await fetch(src, { signal: controller.signal });
      if (!response.ok) throw new Error("Photo unavailable");
      const photo = await response.arrayBuffer();
      if (controller.signal.aborted) return;
      worker.current = new Worker("/condition-model.js", { type: "module" });
      worker.current.onmessage = ({ data }) =>
        finish(
          typeof data.result === "string" &&
            Object.hasOwn(findings, data.result)
            ? data.result
            : undefined,
        );
      worker.current.onerror = () => finish();
      timeout = setTimeout(() => finish(), 180_000);
      worker.current.postMessage(photo, [photo]);
    } catch {
      finish();
    }
  }

  return (
    <div className="work-form">
      <button
        type="button"
        className="pilot-secondary"
        onClick={analyze}
        disabled={status === "running"}
      >
        {status === "running"
          ? t("মডেল চালু হচ্ছে…", "Running photo model…")
          : t("ছবিটি মডেল দিয়ে দেখুন", "Analyze visible condition")}
      </button>
      <small>
        {t(
          "পরীক্ষামূলক ফল। মডেলটি ব্রাউজারে চলে এবং প্রথমবার ডাউনলোড হতে সময় লাগতে পারে।",
          "Experimental. The model runs in your browser. Its first download can take a few minutes.",
        )}
      </small>
      {(result || status === "failed") && (
        <p role="status">
          {result
            ? `${t(...findings[result])}. ${t("পর্যালোচনার আগে ছবিটি নিজে দেখুন।", "Review the photo before recording a finding.")}`
            : t(
                "মডেল চালানো যায়নি। ছবিটি নিজে পর্যালোচনা করুন।",
                "The model could not run. Review the photo manually.",
              )}
        </p>
      )}
    </div>
  );
}
