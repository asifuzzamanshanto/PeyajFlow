import Link from "next/link";
import { operate } from "../../app/[locale]/workspace/operations-actions";
import type { Locale } from "../../lib/copy";
import { api } from "../../lib/workspace-api";
import { local } from "../../lib/workspace-copy";
import type { Payment, Settlement } from "../../lib/workspace-types";
import { timeLabel } from "../../lib/workspace-values";
import { Details, Field, RequestKey } from "./fields";
import { WorkspaceForm } from "./form";
import { taka } from "./market";

const statuses = {
  pending: ["অর্থপ্রদানের তথ্যের অপেক্ষায়", "Awaiting payment report"],
  reported: ["অর্থপ্রদানের তথ্য জমা হয়েছে", "Payment reported"],
  verified: ["অর্থপ্রদান যাচাই হয়েছে", "Payment verified"],
  rejected: ["প্রতিবেদন প্রত্যাখ্যাত", "Report rejected"],
} as const;

export function OrderSettlement({
  locale,
  id,
  data,
  mayReport,
}: {
  locale: Locale;
  id: string;
  data: Settlement;
  mayReport: boolean;
}) {
  const t = (bn: string, en: string) => local(locale, bn, en);
  const [statusBn, statusEn] = statuses[data.status];
  return (
    <section className="work-panel">
      <h2>{t("অর্থপ্রদানের রেকর্ড", "Settlement")}</h2>
      <p className="work-tag">{t(statusBn, statusEn)}</p>
      <p>
        {t("পণ্যের মূল্য", "Goods total")} · {taka(locale, data.total_bdt)}
      </p>
      <p>
        {t(
          "অর্ডারের বাইরে পরিশোধ করা অর্থের তথ্য এখানে নথিভুক্ত হয়। যাচাই করেন একজন অপারেটর।",
          "This records an off-platform payment for the order. An operator verifies the evidence.",
        )}
      </p>
      {mayReport && data.status === "pending" && (
        <Details label={t("অর্থপ্রদানের তথ্য দিন", "Report payment")}>
          <WorkspaceForm
            locale={locale}
            action={operate.bind(null, locale, "report-payment", id)}
            label={t("প্রতিবেদন জমা দিন", "Submit payment report")}
          >
            <RequestKey />
            <Field label={t("লেনদেনের রেফারেন্স", "Transaction reference")}>
              <input name="reference" minLength={3} maxLength={100} required />
            </Field>
            <label className="checkbox">
              <input type="checkbox" name="confirm" required />
              {t(
                "এই অর্ডারের সম্পূর্ণ পণ্যমূল্য পরিশোধের তথ্য দিচ্ছি।",
                "I am reporting payment for the full goods total.",
              )}
            </label>
          </WorkspaceForm>
        </Details>
      )}
      {data.reports.length > 0 && (
        <ul className="work-history">
          {data.reports.map((report) => (
            <li key={report.id}>
              <strong>{report.reference}</strong>
              {report.status === "rejected" && (
                <span>{t(...statuses.rejected)}</span>
              )}
              <time dateTime={report.reported_at}>
                {timeLabel(locale, report.reported_at)}
              </time>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

type QueueEntry = Payment & {
  order_id: string;
  lot_label: string;
  total_bdt: string;
};

export async function SettlementQueue({
  locale,
  base,
  offset,
}: {
  locale: Locale;
  base: string;
  offset: number;
}) {
  const rows = await api<QueueEntry[]>(
    `/v1/admin/settlements?offset=${offset}`,
  );
  const t = (bn: string, en: string) => local(locale, bn, en);
  return (
    <section className="work-panel">
      <h2>{t("অর্থপ্রদান যাচাই", "Review payment reports")}</h2>
      {!rows.length && (
        <p>
          {t(
            "এই পৃষ্ঠায় যাচাই বাকি নেই।",
            "No payment reports await review on this page.",
          )}
        </p>
      )}
      <ul className="work-history">
        {rows.map((row) => (
          <li key={row.id}>
            <Link className="work-link" href={`${base}/orders/${row.order_id}`}>
              {row.lot_label}
            </Link>
            <p>
              {taka(locale, row.total_bdt)} · {row.reference}
            </p>
            <Details label={t("প্রতিবেদন পর্যালোচনা করুন", "Review report")}>
              <WorkspaceForm
                locale={locale}
                action={operate.bind(
                  null,
                  locale,
                  "review-payment",
                  row.order_id,
                )}
                label={t("সিদ্ধান্ত সংরক্ষণ করুন", "Save payment review")}
              >
                <input type="hidden" name="payment_id" value={row.id} />
                <Field label={t("সিদ্ধান্ত", "Review decision")}>
                  <select name="decision" required defaultValue="">
                    <option value="" disabled>
                      {t("বেছে নিন", "Choose a decision")}
                    </option>
                    <option value="verified">
                      {t("যাচাই হয়েছে", "Verified")}
                    </option>
                    <option value="rejected">
                      {t("প্রত্যাখ্যাত", "Rejected")}
                    </option>
                  </select>
                </Field>
                <Field
                  label={t(
                    "স্বতন্ত্র প্রমাণের রেফারেন্স",
                    "Independent evidence reference",
                  )}
                >
                  <input
                    name="evidence_reference"
                    minLength={3}
                    maxLength={100}
                    required
                  />
                </Field>
                <label className="checkbox">
                  <input type="checkbox" name="confirm" required />
                  {t(
                    "ক্রেতার প্রতিবেদনের বাইরে প্রমাণ মিলিয়ে দেখেছি।",
                    "I reviewed evidence independently of the buyer’s report.",
                  )}
                </label>
              </WorkspaceForm>
            </Details>
          </li>
        ))}
      </ul>
      <div className="work-row">
        {offset > 0 && (
          <Link
            className="work-link"
            href={`${base}/operations?view=settlements&offset=${Math.max(0, offset - 50)}`}
          >
            {t("আগের পৃষ্ঠা", "Previous page")}
          </Link>
        )}
        {rows.length === 50 && (
          <Link
            className="work-link"
            href={`${base}/operations?view=settlements&offset=${offset + 50}`}
          >
            {t("পরের পৃষ্ঠা", "Next page")}
          </Link>
        )}
      </div>
    </section>
  );
}
