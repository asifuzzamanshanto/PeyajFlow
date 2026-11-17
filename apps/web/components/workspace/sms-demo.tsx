"use client";

import { useState } from "react";
import type { Locale } from "../../lib/copy";
import { local } from "../../lib/workspace-copy";

export function SmsDemo({ locale }: { locale: Locale }) {
  const [preview, setPreview] = useState(false);
  const t = (bn: string, en: string) => local(locale, bn, en);
  return (
    <div className="work-form">
      <button
        type="button"
        className="pilot-secondary"
        onClick={() => setPreview(!preview)}
      >
        {preview
          ? t("নমুনা বন্ধ করুন", "Close SMS demo")
          : t("এসএমএসের নমুনা দেখুন", "Preview demo SMS")}
      </button>
      {preview && (
        <div role="status">
          <strong>{t("নমুনা এসএমএস", "Simulated SMS")}</strong>
          <p>
            {t(
              "PeyajFlow: আপনার নতুন বিজ্ঞপ্তি আছে। অ্যাপে দেখুন।",
              "PeyajFlow: You have a new alert. Open your workspace to view it.",
            )}
          </p>
        </div>
      )}
    </div>
  );
}
