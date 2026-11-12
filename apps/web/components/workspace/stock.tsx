import Link from "next/link";
import { mutate } from "../../app/[locale]/workspace/actions";
import type { Locale } from "../../lib/copy";
import { api, type Profile } from "../../lib/workspace-api";
import { local } from "../../lib/workspace-copy";
import type { Lot, LotDetail } from "../../lib/workspace-types";
import { dhakaToday, numberLabel, timeLabel } from "../../lib/workspace-values";
import { DecimalField, Details, Field, GradeField, RequestKey } from "./fields";
import { WorkspaceForm } from "./form";

const movements: Record<string, [string, string]> = {
  HARVEST_ADDED: ["মজুত নিবন্ধন", "Stock registered"],
  WEIGHED_ADJUSTMENT: ["ওজন সমন্বয়", "Weight adjustment"],
  LOSS_REPORTED: ["ক্ষতি নথিভুক্ত", "Loss recorded"],
  RESERVED: ["সংরক্ষিত", "Reserved"],
  RESERVATION_RELEASED: ["সংরক্ষণ মুক্ত", "Reservation released"],
  DISPATCHED: ["পাঠানো হয়েছে", "Dispatched"],
  DELIVERED: ["পৌঁছেছে", "Received"],
};

export function kg(locale: Locale, value: string) {
  return `${numberLabel(locale, value)} ${local(locale, "কেজি", "kg")}`;
}

function UnitFields({ locale }: { locale: Locale }) {
  return (
    <div className="work-grid">
      <DecimalField
        label={local(locale, "পরিমাণ", "Quantity")}
        name="quantity"
      />
      <Field label={local(locale, "একক", "Unit")}>
        <select name="unit">
          <option value="kg">{local(locale, "কেজি", "kg")}</option>
          <option value="maund">{local(locale, "মণ", "maund")}</option>
        </select>
      </Field>
      <DecimalField
        label={local(
          locale,
          "মণ হলে প্রতি মণে কেজি",
          "If using maunds, kg per maund",
        )}
        name="kg_per_maund"
        optional
      />
    </div>
  );
}

function LotFields({
  locale,
  district,
  lot,
}: {
  locale: Locale;
  district: string;
  lot?: Lot;
}) {
  const date = dhakaToday();
  return (
    <>
      <div className="work-grid">
        <Field label={local(locale, "মজুতের নাম", "Lot name")}>
          <input
            name="label"
            defaultValue={lot?.label}
            maxLength={100}
            required
          />
        </Field>
        <Field label={local(locale, "জেলা", "District")}>
          <input
            name="district"
            defaultValue={lot?.district ?? district}
            maxLength={100}
            required
          />
        </Field>
        <Field label={local(locale, "জাত", "Variety")}>
          <input
            name="variety"
            defaultValue={lot?.variety}
            maxLength={100}
            required
          />
        </Field>
        <Field label={local(locale, "সংরক্ষণের ধরন", "Storage type")}>
          <input
            name="storage_type"
            defaultValue={lot?.storage_type}
            maxLength={100}
            required
          />
        </Field>
        <Field label={local(locale, "ফসল তোলার তারিখ", "Harvest date")}>
          <input
            type="date"
            name="harvest_on"
            max={date}
            defaultValue={lot?.harvest_on ?? date}
            required
          />
        </Field>
        <Field
          label={local(locale, "সংরক্ষণ শুরুর তারিখ", "Date put into storage")}
        >
          <input
            type="date"
            name="stored_on"
            max={date}
            defaultValue={lot?.stored_on ?? date}
            required
          />
        </Field>
        <GradeField locale={locale} value={lot?.grade} />
      </div>
      <label className="checkbox">
        <input
          type="checkbox"
          name="listed"
          defaultChecked={lot?.listed ?? false}
        />
        {local(
          locale,
          "ক্রেতাদের জন্য তালিকাভুক্ত করুন",
          "List this lot for buyers",
        )}
      </label>
    </>
  );
}

function LotBalances({ locale, lot }: { locale: Locale; lot: Lot }) {
  const stats = [
    [
      local(locale, "বর্তমান মজুত", "Recorded stock"),
      kg(locale, lot.available_kg),
    ],
    [local(locale, "সংরক্ষিত", "Reserved"), kg(locale, lot.reserved_kg)],
    [local(locale, "খালি মজুত", "Unreserved"), kg(locale, lot.sellable_kg)],
    [
      local(locale, "যাচাই করা", "Verified"),
      lot.verified_kg === null
        ? local(locale, "নিজস্ব প্রতিবেদন", "Self-reported")
        : kg(locale, lot.verified_kg),
    ],
  ];
  return (
    <dl className="work-metrics">
      {stats.map(([label, value]) => (
        <div key={label}>
          <dt>{label}</dt>
          <dd>{value}</dd>
        </div>
      ))}
    </dl>
  );
}

export async function StockPage({
  locale,
  actor,
  base,
  offset,
}: {
  locale: Locale;
  actor: Profile;
  base: string;
  offset: number;
}) {
  const lots = await api<Lot[]>(`/v1/lots?offset=${offset}`);
  return (
    <>
      <h1>
        {actor.role === "farmer"
          ? local(locale, "আমার মজুত", "My stock")
          : local(locale, "মজুত", "Stock")}
      </h1>
      {actor.role === "farmer" && (
        <section className="work-panel">
          <Details label={local(locale, "নতুন মজুত নিবন্ধন", "Register a lot")}>
            <WorkspaceForm
              locale={locale}
              action={mutate.bind(null, locale, "lot-create", "", "")}
              label={local(locale, "মজুত সংরক্ষণ করুন", "Save lot")}
            >
              <RequestKey />
              <LotFields locale={locale} district={actor.district} />
              <UnitFields locale={locale} />
            </WorkspaceForm>
          </Details>
        </section>
      )}
      {!lots.length && (
        <p className="work-panel">
          {local(
            locale,
            "এই পৃষ্ঠায় কোনো মজুত নেই।",
            "There are no lots on this page.",
          )}
        </p>
      )}
      <div className="work-cards">
        {lots.map((lot) => (
          <article key={lot.id} className="work-panel">
            <h2>
              <Link className="work-link" href={`${base}/stock/${lot.id}`}>
                {lot.label}
              </Link>
            </h2>
            <p>
              {lot.variety} · {lot.district}
            </p>
            <LotBalances locale={locale} lot={lot} />
          </article>
        ))}
      </div>
      <div className="work-row">
        {offset > 0 && (
          <Link
            className="work-link"
            href={`${base}/stock?offset=${Math.max(0, offset - 50)}`}
          >
            {local(locale, "আগের পৃষ্ঠা", "Previous page")}
          </Link>
        )}
        {lots.length === 50 && (
          <Link
            className="work-link"
            href={`${base}/stock?offset=${offset + 50}`}
          >
            {local(locale, "পরের পৃষ্ঠা", "Next page")}
          </Link>
        )}
      </div>
    </>
  );
}

export async function LotPage({
  locale,
  actor,
  base,
  id,
}: {
  locale: Locale;
  actor: Profile;
  base: string;
  id: string;
}) {
  const lot = await api<LotDetail>(`/v1/lots/${id}`);
  return (
    <>
      <Link className="work-link" href={`${base}/stock`}>
        {local(locale, "মজুতে ফিরুন", "Back to stock")}
      </Link>
      <h1>{lot.label}</h1>
      <section className="work-panel">
        <h2>{local(locale, "মজুতের পরিমাণ", "Stock balance")}</h2>
        <p>
          {lot.district} · {lot.variety} · {lot.storage_type}
        </p>
        <LotBalances locale={locale} lot={lot} />
        <p>
          {local(locale, "প্রথম নিবন্ধিত পরিমাণ", "Initial quantity")} ·{" "}
          {kg(locale, lot.initial_kg)}
        </p>
        {lot.verified_at && (
          <p>
            {local(locale, "শেষ যাচাই", "Last weighed")} ·{" "}
            {timeLabel(locale, lot.verified_at)}
          </p>
        )}
        <div className="work-row">
          <Link className="work-link" href={`${base}/stock/${id}/inspections`}>
            {local(locale, "পরিদর্শন ও ছবি", "Inspections and photos")}
          </Link>
          <Link className="work-link" href={`${base}/stock/${id}/risk`}>
            {local(locale, "সংরক্ষণের ঝুঁকি", "Storage risk")}
          </Link>
        </div>
      </section>
      {actor.role === "farmer" && (
        <section className="work-panel">
          <Details label={local(locale, "মজুতের তথ্য বদলান", "Edit lot details")}>
            <WorkspaceForm
              locale={locale}
              action={mutate.bind(null, locale, "lot-edit", id, "")}
              label={local(locale, "তথ্য সংরক্ষণ করুন", "Save details")}
            >
              <LotFields locale={locale} district={actor.district} lot={lot} />
            </WorkspaceForm>
          </Details>
        </section>
      )}
      {actor.role !== "admin" && (
        <section className="work-panel">
          <Details
            label={local(
              locale,
              "ওজন বা ক্ষতি নথিভুক্ত করুন",
              "Record a weight change or loss",
            )}
          >
            <WorkspaceForm
              locale={locale}
              action={mutate.bind(null, locale, "movement", id, "")}
              label={local(locale, "পরিবর্তন সংরক্ষণ করুন", "Save stock change")}
            >
              <RequestKey />
              <Field label={local(locale, "পরিবর্তনের ধরন", "Change type")}>
                <select name="event_type">
                  <option value="WEIGHED_ADJUSTMENT">
                    {local(
                      locale,
                      "ওজন সমন্বয় (+/−)",
                      "Weight adjustment (+/−)",
                    )}
                  </option>
                  <option value="LOSS_REPORTED">
                    {local(locale, "ক্ষতি", "Loss")}
                  </option>
                </select>
              </Field>
              <UnitFields locale={locale} />
              <Field label={local(locale, "কারণ", "Reason")}>
                <input name="reason" maxLength={200} required />
              </Field>
            </WorkspaceForm>
          </Details>
        </section>
      )}
      {(actor.role === "agent" || actor.role === "admin") && (
        <section className="work-panel">
          <Details
            label={local(locale, "ওজন যাচাই করুন", "Verify measured stock")}
          >
            <WorkspaceForm
              locale={locale}
              action={mutate.bind(null, locale, "verify", id, "")}
              label={local(locale, "যাচাই সংরক্ষণ করুন", "Save verification")}
            >
              <DecimalField
                name="verified_kg"
                label={local(locale, "যাচাইকৃত কেজি", "Verified kg")}
                value={lot.verified_kg}
              />
            </WorkspaceForm>
          </Details>
        </section>
      )}
      <section className="work-panel">
        <h2>{local(locale, "মজুতের ইতিহাস", "Stock history")}</h2>
        <ul className="work-history">
          {lot.events.map((event) => (
            <li key={event.id}>
              <strong>
                {local(
                  locale,
                  ...(movements[event.event_type] ?? [
                    event.event_type,
                    event.event_type,
                  ]),
                )}
              </strong>
              <span>
                {kg(locale, event.delta_kg)} ·{" "}
                {local(locale, "সংরক্ষিত পরিবর্তন", "Reservation change")}{" "}
                {kg(locale, event.reserved_delta_kg)}
              </span>
              {event.submitted_unit === "maund" && event.kg_per_maund && (
                <span>
                  {local(locale, "প্রতি মণে", "Per maund")}{" "}
                  {kg(locale, event.kg_per_maund)}
                </span>
              )}
              {["WEIGHED_ADJUSTMENT", "LOSS_REPORTED"].includes(
                event.event_type,
              ) && <span>{event.reason}</span>}
              <time dateTime={event.recorded_at}>
                {timeLabel(locale, event.recorded_at)}
              </time>
            </li>
          ))}
        </ul>
      </section>
    </>
  );
}
