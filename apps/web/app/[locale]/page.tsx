import Link from "next/link";
import { notFound } from "next/navigation";
import { BrandLogo } from "../../components/brand-logo";
import { WorkspaceIcon } from "../../components/workspace/icon";
import { isLocale } from "../../lib/copy";
import { local } from "../../lib/workspace-copy";

export default async function Home({ params }: PageProps<"/[locale]">) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  const t = (bn: string, en: string) => local(locale, bn, en);
  const alternate = locale === "bn" ? "en" : "bn";
  const workspace = `/${locale}/workspace`;
  const capabilities = [
    [
      "stock",
      t("মজুত ও গুণমান", "Stock and condition"),
      t(
        "মজুতের ওজন, সংরক্ষণ ও পরিদর্শনের ইতিহাস রাখুন।",
        "Record weights, storage conditions, and inspection evidence by lot.",
      ),
    ],
    [
      "prices",
      t("বাজারদর ও সিদ্ধান্ত", "Market and decisions"),
      t(
        "উৎসসহ বাজারদর দেখুন এবং এখন বিক্রি করা বা অপেক্ষা করার হিসাব মিলিয়ে নিন।",
        "Compare sourced market prices and the likely cost of holding or selling.",
      ),
    ],
    [
      "orders",
      t("অফার ও সরবরাহ", "Offers and delivery"),
      t(
        "অফার থেকে পরিবহন, পণ্য গ্রহণ এবং অর্থপ্রদানের রেকর্ড পর্যন্ত দেখুন।",
        "Follow an offer through transport, receipt, and payment review.",
      ),
    ],
  ];
  return (
    <div className="public-site">
      <a className="skip-link" href="#main">
        {t("মূল অংশে যান", "Skip to main content")}
      </a>
      <header className="public-header">
        <Link className="brand-link" href={`/${locale}`}>
          <BrandLogo />
        </Link>
        <nav aria-label={t("প্রধান নেভিগেশন", "Main navigation")}>
          <a className="public-how" href="#how">
            {t("কীভাবে কাজ করে", "How it works")}
          </a>
          <Link className="language" href={`/${alternate}`} lang={alternate}>
            {t("English", "বাংলা")}
          </Link>
          <Link className="public-button" href={workspace}>
            {t("সাইন ইন", "Sign in")}
          </Link>
        </nav>
      </header>
      <main id="main" tabIndex={-1}>
        <section className="public-hero">
          <div className="public-hero-copy">
            <p className="public-kicker">
              {t("পাবনা থেকে ঢাকা", "Pabna to Dhaka")}
            </p>
            <h1>
              {t(
                "মজুত থেকে বাজারে পেঁয়াজের যাত্রা",
                "From onion stock to a confirmed sale.",
              )}
            </h1>
            <p>
              {t(
                "মজুত, পরিদর্শন, বাজারদর ও ক্রয়-বিক্রয় এক জায়গায়। কৃষক, ক্রেতা ও মাঠ সহায়তাকারীদের জন্য।",
                "One workspace for growers, buyers, and field agents to manage stock, compare prices, and follow every order.",
              )}
            </p>
            <div className="public-actions">
              <Link className="public-button" href={workspace}>
                {t("ওয়ার্কস্পেস খুলুন", "Open workspace")}
                <WorkspaceIcon name="arrow" />
              </Link>
              <a className="public-how" href="#how">
                {t("কীভাবে কাজ করে", "How it works")}
              </a>
            </div>
          </div>
          <div
            className="public-hero-photo"
            role="img"
            aria-label={t(
              "বাঁশের ঝুড়িতে লাল পেঁয়াজ",
              "Red onions in a woven basket",
            )}
          />
        </section>
        <section className="public-capabilities" id="how">
          <h2>
            {t(
              "মজুত থেকে সরবরাহ পর্যন্ত",
              "Track the trade from stock to delivery",
            )}
          </h2>
          <div>
            {capabilities.map(([icon, title, description]) => (
              <article key={icon}>
                <span className="dash-icon">
                  <WorkspaceIcon name={icon} />
                </span>
                <h3>{title}</h3>
                <p>{description}</p>
              </article>
            ))}
          </div>
        </section>
      </main>
      <footer className="public-footer">
        <BrandLogo />
        <Link className="work-link" href={workspace}>
          {t("ওয়ার্কস্পেস", "Workspace")}
        </Link>
      </footer>
    </div>
  );
}
