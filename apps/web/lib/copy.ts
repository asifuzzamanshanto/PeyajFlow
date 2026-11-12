export const copy = {
  bn: {
    skip: "মূল অংশে যান",
    navigation: "ওয়ার্কস্পেস নেভিগেশন",
    languageLabel: "English",
    overview: "সংক্ষিপ্ত চিত্র",
    heading: "ওয়ার্কস্পেসের অবস্থা",
    introduction: "পেয়াজফ্লোর সেবা ও ডেটাবেস সংযোগের বর্তমান অবস্থা দেখুন।",
    refresh: "আবার দেখুন",
    refreshing: "যাচাই চলছে…",
    overall: {
      ready: ["সিস্টেম প্রস্তুত", "অ্যাপের সেবা ও ডেটাবেস সক্রিয় আছে।"],
      pending: ["সেটআপ প্রয়োজন", "নিচে দেখুন কোন সংযোগটি পরীক্ষা করতে হবে।"],
    },
    connection: "সিস্টেমের সংযোগ",
    api: "অ্যাপের সেবা",
    database: "ডেটাবেস",
    statuses: {
      online: ["সক্রিয়", "অ্যাপের সেবা থেকে সাড়া পাওয়া গেছে।"],
      offline: [
        "সংযোগ নেই",
        "অ্যাপের সেবা চালু আছে কি না দেখুন, তারপর আবার চেষ্টা করুন।",
      ],
      ready: ["প্রস্তুত", "ডেটাবেসে সর্বশেষ স্কিমা প্রয়োগ করা আছে।"],
      unconfigured: [
        "কনফিগার করা হয়নি",
        "অ্যাপের সেবায় ডেটাবেসের ঠিকানা যোগ করুন।",
      ],
      unreachable: [
        "সংযোগ নেই",
        "ডেটাবেস চালু আছে কি না এবং সংযোগ সেটিংস ঠিক আছে কি না দেখুন।",
      ],
      migration_required: ["আপডেট প্রয়োজন", "ডেটাবেসে সর্বশেষ স্কিমা প্রয়োগ করুন।"],
      unknown: [
        "যাচাই হয়নি",
        "অ্যাপের সেবা থেকে সাড়া পাওয়া গেলে ডেটাবেস পরীক্ষা করা যাবে।",
      ],
    },
    checked: "শেষ যাচাই",
    timeZone: "ঢাকা সময়",
  },
  en: {
    skip: "Skip to main content",
    navigation: "Workspace navigation",
    languageLabel: "বাংলা",
    overview: "Overview",
    heading: "Workspace status",
    introduction:
      "Check the connections that keep the PeyajFlow workspace running.",
    refresh: "Refresh status",
    refreshing: "Checking…",
    overall: {
      ready: [
        "System ready",
        "The application service and database are available.",
      ],
      pending: [
        "Setup required",
        "Review the connections below to see what needs attention.",
      ],
    },
    connection: "System connections",
    api: "Application service",
    database: "Database",
    statuses: {
      online: ["Online", "The application service responded."],
      offline: [
        "Unavailable",
        "Check that the application service is running and try again.",
      ],
      ready: ["Ready", "The database has the latest schema."],
      unconfigured: [
        "Unconfigured",
        "Set the database address in the application service.",
      ],
      unreachable: [
        "Unreachable",
        "Check that PostgreSQL is running and verify the connection settings.",
      ],
      migration_required: [
        "Update required",
        "Apply the latest database migration.",
      ],
      unknown: [
        "Unchecked",
        "The database can be checked once the application service responds.",
      ],
    },
    checked: "Last checked",
    timeZone: "Dhaka time",
  },
} as const;

export type Locale = keyof typeof copy;

export function isLocale(value: string): value is Locale {
  return value === "bn" || value === "en";
}
