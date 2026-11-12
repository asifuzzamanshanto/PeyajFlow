import Link from "next/link";
import { mutate } from "../../app/[locale]/workspace/actions";
import type { Locale } from "../../lib/copy";
import { api, type Profile } from "../../lib/workspace-api";
import { local } from "../../lib/workspace-copy";
import type {
  Offer,
  OfferDetail,
  Order,
  OrderDetail,
} from "../../lib/workspace-types";
import { timeLabel } from "../../lib/workspace-values";
import { DecimalField, Details, RequestKey } from "./fields";
import { WorkspaceForm } from "./form";
import { taka } from "./market";
import { kg } from "./stock";

const states: Record<string, [string, string]> = {
  sent: ["পাঠানো হয়েছে", "Sent"],
  countered: ["পাল্টা অফার", "Countered"],
  accepted: ["গ্রহণ করা হয়েছে", "Accepted"],
  rejected: ["প্রত্যাখ্যাত", "Rejected"],
  withdrawn: ["প্রত্যাহার করা হয়েছে", "Withdrawn"],
  expired: ["মেয়াদ শেষ", "Expired"],
  confirmed: ["নিশ্চিত", "Confirmed"],
  dispatched: ["পাঠানো হয়েছে", "Dispatched"],
  delivered: ["গ্রহণ করা হয়েছে", "Received"],
  cancelled: ["বাতিল", "Cancelled"],
  disputed: ["বিরোধ আছে", "Disputed"],
  dispute_resolved: ["বিরোধ নিষ্পত্তি", "Dispute resolved"],
};

function state(locale: Locale, status: string) {
  return local(locale, ...(states[status] ?? [status, status]));
}

function Terms({ locale, offer }: { locale: Locale; offer: Offer }) {
  const pairs = [
    [
      local(locale, "ক্রেতা", "Buyer"),
      `${offer.buyer_name} · ${offer.buyer_verified ? local(locale, "যাচাইকৃত", "Verified") : local(locale, "যাচাই হয়নি", "Unverified")}`,
    ],
    [local(locale, "বিক্রেতা", "Seller"), offer.seller_name],
    [local(locale, "পরিমাণ", "Quantity"), kg(locale, offer.quantity_kg)],
    [
      local(locale, "প্রতি কেজির দর", "Price per kg"),
      taka(locale, offer.price_bdt_kg),
    ],
    [local(locale, "মোট মূল্য", "Total value"), taka(locale, offer.total_bdt)],
    [local(locale, "সরবরাহ", "Delivery district"), offer.delivery_district],
    [
      local(locale, "সরবরাহের সময়", "Delivery window"),
      offer.delivery_from && offer.delivery_to
        ? offer.delivery_from === offer.delivery_to
          ? timeLabel(locale, offer.delivery_from)
          : `${timeLabel(locale, offer.delivery_from)} – ${timeLabel(locale, offer.delivery_to)}`
        : local(locale, "আলোচনা সাপেক্ষ", "By arrangement"),
    ],
    [
      local(locale, "পরিবহন", "Transport"),
      offer.transport === "buyer"
        ? local(locale, "ক্রেতার দায়িত্ব", "Buyer arranges")
        : local(locale, "বিক্রেতার দায়িত্ব", "Seller arranges"),
    ],
    [local(locale, "গ্রেড", "Grade"), offer.grade],
  ];
  return (
    <dl className="work-metrics">
      {pairs.map(([key, value]) => (
        <div key={key}>
          <dt>{key}</dt>
          <dd>{value}</dd>
        </div>
      ))}
    </dl>
  );
}

function OfferAction({
  locale,
  offer,
  action,
  label,
}: {
  locale: Locale;
  offer: Offer;
  action: "accept" | "reject" | "counter" | "withdraw";
  label: string;
}) {
  return (
    <Details label={label}>
      <WorkspaceForm
        locale={locale}
        action={mutate.bind(null, locale, "offer-reply", offer.id, action)}
        label={label}
      >
        <RequestKey />
        <input type="hidden" name="version" value={offer.version} />
        {action === "accept" && (
          <label className="checkbox">
            <input type="checkbox" name="confirm" required />
            {local(
              locale,
              "উপরের শর্ত পড়েছি এবং মজুত সংরক্ষণ নিশ্চিত করছি।",
              "I reviewed the terms and confirm the stock reservation.",
            )}
          </label>
        )}
        {action === "counter" && (
          <div className="work-grid">
            <DecimalField
              name="quantity_kg"
              label={local(locale, "নতুন পরিমাণ (কেজি)", "New quantity (kg)")}
              value={offer.quantity_kg}
            />
            <DecimalField
              name="price_bdt_kg"
              label={local(locale, "নতুন দর (৳/কেজি)", "New price (BDT/kg)")}
              value={offer.price_bdt_kg}
            />
          </div>
        )}
      </WorkspaceForm>
    </Details>
  );
}

function TradePagination({
  locale,
  base,
  offset,
  length,
}: {
  locale: Locale;
  base: string;
  offset: number;
  length: number;
}) {
  return (
    <div className="work-row">
      {offset > 0 && (
        <Link
          className="work-link"
          href={`${base}?offset=${Math.max(0, offset - 50)}`}
        >
          {local(locale, "আগের পৃষ্ঠা", "Previous page")}
        </Link>
      )}
      {length === 50 && (
        <Link className="work-link" href={`${base}?offset=${offset + 50}`}>
          {local(locale, "পরের পৃষ্ঠা", "Next page")}
        </Link>
      )}
    </div>
  );
}

export async function OffersPage({
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
  const offers = await api<Offer[]>(`/v1/offers?offset=${offset}`);
  return (
    <>
      <h1>{local(locale, "অফার", "Offers")}</h1>
      {!offers.length && (
        <p className="work-panel">
          {local(locale, "এই পৃষ্ঠায় কোনো অফার নেই।", "No offers on this page.")}
        </p>
      )}
      {offers.map((offer) => {
        const open =
          ["sent", "countered"].includes(offer.status) &&
          actor.role !== "admin";
        const proposer = actor.membership_id === offer.proposer_id;
        return (
          <article key={offer.id} className="work-panel">
            <div className="work-row">
              <h2>
                {offer.lot_label} · {offer.variety}
              </h2>
              <span className="work-tag">{state(locale, offer.status)}</span>
            </div>
            <Terms locale={locale} offer={offer} />
            <p>
              {local(locale, "অফারের মেয়াদ", "Offer expires")} ·{" "}
              {timeLabel(locale, offer.expires_at)}
            </p>
            {open &&
              (proposer ? (
                <OfferAction
                  locale={locale}
                  offer={offer}
                  action="withdraw"
                  label={local(locale, "অফার প্রত্যাহার", "Withdraw offer")}
                />
              ) : (
                <>
                  <OfferAction
                    locale={locale}
                    offer={offer}
                    action="accept"
                    label={local(locale, "অফার গ্রহণ করুন", "Accept offer")}
                  />
                  <OfferAction
                    locale={locale}
                    offer={offer}
                    action="counter"
                    label={local(locale, "পাল্টা অফার দিন", "Counter offer")}
                  />
                  <OfferAction
                    locale={locale}
                    offer={offer}
                    action="reject"
                    label={local(locale, "অফার প্রত্যাখ্যান", "Reject offer")}
                  />
                </>
              ))}
            <Link className="work-link" href={`${base}/offers/${offer.id}`}>
              {local(locale, "অফারের ইতিহাস", "Offer history")}
            </Link>
            {offer.status === "accepted" && (
              <Link className="work-link" href={`${base}/orders`}>
                {local(locale, "অর্ডার দেখুন", "View orders")}
              </Link>
            )}
          </article>
        );
      })}
      <TradePagination
        locale={locale}
        base={`${base}/offers`}
        offset={offset}
        length={offers.length}
      />
    </>
  );
}

export async function OfferHistoryPage({
  locale,
  base,
  id,
}: {
  locale: Locale;
  base: string;
  id: string;
}) {
  const offer = await api<OfferDetail>(`/v1/offers/${id}`);
  return (
    <>
      <Link className="work-link" href={`${base}/offers`}>
        {local(locale, "অফারে ফিরুন", "Back to offers")}
      </Link>
      <h1>{local(locale, "অফারের ইতিহাস", "Offer history")}</h1>
      <section className="work-panel">
        <div className="work-row">
          <h2>{offer.lot_label}</h2>
          <span className="work-tag">{state(locale, offer.status)}</span>
        </div>
        <Terms locale={locale} offer={offer} />
        <ul className="work-history">
          {offer.activity.map((entry) => (
            <li key={entry.version}>
              <strong>
                {state(locale, entry.action)} · {entry.by}
              </strong>
              {entry.quantity_kg !== null && entry.price_bdt_kg !== null && (
                <span>
                  {kg(locale, entry.quantity_kg)} ·{" "}
                  {taka(locale, entry.price_bdt_kg)}/
                  {local(locale, "কেজি", "kg")}
                </span>
              )}
              <time dateTime={entry.recorded_at}>
                {timeLabel(locale, entry.recorded_at)}
              </time>
            </li>
          ))}
        </ul>
      </section>
    </>
  );
}

export async function OrdersPage({
  locale,
  base,
  offset,
}: {
  locale: Locale;
  base: string;
  offset: number;
}) {
  const orders = await api<Order[]>(`/v1/orders?offset=${offset}`);
  return (
    <>
      <h1>{local(locale, "অর্ডার", "Orders")}</h1>
      {!orders.length && (
        <p className="work-panel">
          {local(locale, "এই পৃষ্ঠায় কোনো অর্ডার নেই।", "No orders on this page.")}
        </p>
      )}
      <div className="work-cards">
        {orders.map((order) => (
          <article key={order.id} className="work-panel">
            <h2>
              <Link className="work-link" href={`${base}/orders/${order.id}`}>
                {order.offer.lot_label}
              </Link>
            </h2>
            <p>
              {kg(locale, order.offer.quantity_kg)} ·{" "}
              {taka(locale, order.offer.total_bdt)}
            </p>
            <p>
              <span className="work-tag">{state(locale, order.status)}</span>
            </p>
          </article>
        ))}
      </div>
      <TradePagination
        locale={locale}
        base={`${base}/orders`}
        offset={offset}
        length={orders.length}
      />
    </>
  );
}

export async function OrderPage({
  locale,
  base,
  id,
  actor,
}: {
  locale: Locale;
  base: string;
  id: string;
  actor: Profile;
}) {
  const order = await api<OrderDetail>(`/v1/orders/${id}`);
  const actions = [];
  if (actor.role === "farmer" && order.status === "confirmed")
    actions.push(["dispatch", "পাঠানো নিশ্চিত করুন", "Confirm dispatch"]);
  if (actor.role === "buyer" && order.status === "dispatched")
    actions.push(["receive", "পণ্য গ্রহণ নিশ্চিত করুন", "Confirm receipt"]);
  if (actor.role !== "admin" && order.status === "confirmed")
    actions.push(["cancel", "অর্ডার বাতিল করুন", "Cancel order"]);
  if (
    actor.role !== "admin" &&
    ["dispatched", "delivered"].includes(order.status)
  )
    actions.push(["dispute", "বিরোধ জানান", "Report dispute"]);
  return (
    <>
      <Link className="work-link" href={`${base}/orders`}>
        {local(locale, "অর্ডারে ফিরুন", "Back to orders")}
      </Link>
      <h1>{local(locale, "অর্ডারের রসিদ", "Order receipt")}</h1>
      <Link className="work-link" href={`${base}/orders/${id}/logistics`}>
        {local(locale, "পরিবহন ও দর", "Transport and quotes")}
      </Link>
      <section className="work-panel">
        <div className="work-row">
          <h2>{order.offer.lot_label}</h2>
          <span className="work-tag">{state(locale, order.status)}</span>
        </div>
        <p>{id}</p>
        <Terms locale={locale} offer={order.offer} />
        {order.status === "confirmed" && (
          <p>
            {local(locale, "সংরক্ষণের শেষ সময়", "Reservation expires")} ·{" "}
            {timeLabel(locale, order.expires_at)}
          </p>
        )}
        {actions.map(([action, bn, en]) => (
          <Details key={action} label={local(locale, bn, en)}>
            <WorkspaceForm
              locale={locale}
              action={mutate.bind(null, locale, "order", id, action)}
              label={local(locale, bn, en)}
            >
              <RequestKey />
              <label className="checkbox">
                <input type="checkbox" name="confirm" required />
                {local(
                  locale,
                  "আমি এই পরিবর্তন নিশ্চিত করছি।",
                  "I confirm this change.",
                )}
              </label>
            </WorkspaceForm>
          </Details>
        ))}
      </section>
      <section className="work-panel">
        <h2>{local(locale, "অর্ডারের ইতিহাস", "Order history")}</h2>
        <ul className="work-history">
          {order.activity.map((event, index) => (
            <li key={`${event.recorded_at}-${index}`}>
              <strong>{state(locale, event.action)}</strong>
              <time dateTime={event.recorded_at}>
                {timeLabel(locale, event.recorded_at)}
              </time>
              {event.by_system && (
                <span>{local(locale, "স্বয়ংক্রিয়", "Automatic")}</span>
              )}
            </li>
          ))}
        </ul>
      </section>
    </>
  );
}
