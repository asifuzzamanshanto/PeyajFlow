import Link from "next/link";
import { notFound } from "next/navigation";
import { BrandLogo } from "../../components/brand-logo";
import { RefreshStatus } from "../../components/refresh-status";
import { copy, isLocale } from "../../lib/copy";
import { readHealth } from "../../lib/health";

export const dynamic = "force-dynamic";

function Connection({
  title,
  description,
  status,
  positive,
}: {
  title: string;
  description: string;
  status: string;
  positive: boolean;
}) {
  return (
    <div className="connection">
      <dt>{title}</dt>
      <dd className="connection-body">
        <p className={positive ? "state state-ready" : "state state-pending"}>
          <span aria-hidden="true" />
          {status}
        </p>
        <p className="description">{description}</p>
      </dd>
    </div>
  );
}

export default async function Workspace({ params }: PageProps<"/[locale]">) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  const words = copy[locale];
  const alternate = locale === "bn" ? "en" : "bn";
  const health = await readHealth(
    process.env.API_INTERNAL_BASE_URL ?? "http://127.0.0.1:8000",
  );
  const checkedAt = new Date();
  const localTime = new Intl.DateTimeFormat(
    locale === "bn" ? "bn-BD" : "en-GB",
    {
      dateStyle: "medium",
      timeStyle: "short",
      hourCycle: "h23",
      timeZone: "Asia/Dhaka",
    },
  ).format(checkedAt);
  const overall =
    words.overall[health.database === "ready" ? "ready" : "pending"];

  return (
    <div className="workspace">
      <a className="skip-link" href="#main">
        {words.skip}
      </a>
      <header className="rail">
        <Link className="brand-link" href={`/${locale}`}>
          <BrandLogo />
        </Link>
        <nav aria-label={words.navigation}>
          <Link
            className="current-page"
            href={`/${locale}`}
            aria-current="page"
          >
            {words.overview}
          </Link>
        </nav>
        <Link
          className="language mobile-language"
          href={`/${alternate}`}
          lang={alternate}
          hrefLang={alternate}
        >
          {words.languageLabel}
        </Link>
      </header>
      <div className="workspace-body">
        <div className="toolbar">
          <Link
            className="language"
            href={`/${alternate}`}
            lang={alternate}
            hrefLang={alternate}
          >
            {words.languageLabel}
          </Link>
        </div>
        <main id="main" className="content">
          <div className="page-heading">
            <div>
              <h1>{words.heading}</h1>
              <p className="description">{words.introduction}</p>
            </div>
            <RefreshStatus
              label={words.refresh}
              pendingLabel={words.refreshing}
            />
          </div>
          <Link className="work-link" href={`/${locale}/workspace`}>
            {locale === "bn" ? "ওয়ার্কস্পেস খুলুন" : "Open workspace"}
          </Link>
          <div aria-live="polite">
            <section className="summary" aria-labelledby="summary-heading">
              <div>
                <h2 id="summary-heading">{overall[0]}</h2>
                <p>{overall[1]}</p>
              </div>
              <p className="checked">
                {words.checked}
                <time dateTime={checkedAt.toISOString()}>
                  {localTime} · {words.timeZone}
                </time>
              </p>
            </section>
            <section
              className="connections"
              aria-labelledby="connection-heading"
            >
              <h2 id="connection-heading">{words.connection}</h2>
              <dl>
                <Connection
                  title={words.api}
                  status={words.statuses[health.api][0]}
                  description={words.statuses[health.api][1]}
                  positive={health.api === "online"}
                />
                <Connection
                  title={words.database}
                  status={words.statuses[health.database][0]}
                  description={words.statuses[health.database][1]}
                  positive={health.database === "ready"}
                />
              </dl>
            </section>
          </div>
        </main>
      </div>
    </div>
  );
}
