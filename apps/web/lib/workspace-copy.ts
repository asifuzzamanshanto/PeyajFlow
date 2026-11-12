import type { Locale } from "./copy";
import type { Role } from "./workspace-api";

export function local(locale: Locale, bn: string, en: string) {
  return locale === "bn" ? bn : en;
}

export const roles: Record<Role, [string, string]> = {
  farmer: ["কৃষক", "Farmer"],
  buyer: ["ক্রেতা", "Buyer"],
  agent: ["সহায়তাকারী", "Agent"],
  admin: ["পরিচালক", "Operator"],
};

const errors: Record<string, [string, string]> = {
  conversion_required: [
    "মণ হলে প্রতি মণে কেজি লিখুন।",
    "Enter kg per maund when using maunds.",
  ],
  invalid_quantity: [
    "পরিমাণটি অনুমোদিত সীমায় লিখুন।",
    "Enter a quantity within the allowed range.",
  ],
  demand_terms_mismatch: [
    "অফারের শর্ত চাহিদার সঙ্গে মেলে না।",
    "The offer terms do not match the linked demand.",
  ],
  inspection_date_invalid: [
    "পরিদর্শনের তারিখ সংরক্ষণের শুরুর পরের দিন বা সেই দিন হতে হবে।",
    "Use an inspection date within the current storage period.",
  ],
  review_locked: [
    "মানুষের পর্যালোচনা সম্পন্ন হয়েছে।",
    "A reviewer has already assessed this inspection.",
  ],
  photo_storage_unavailable: [
    "ছবির সংরক্ষণসেবা এখন পাওয়া যাচ্ছে না।",
    "Photo storage is unavailable. Try again.",
  ],
  invalid_input: [
    "তথ্য যাচাই করে আবার চেষ্টা করুন।",
    "Check the fields and try again.",
  ],
  service_unavailable: [
    "সেবা এখন পাওয়া যাচ্ছে না।",
    "The service is unavailable. Try again.",
  ],
  database_unavailable: [
    "ডেটাবেস এখন পাওয়া যাচ্ছে না।",
    "The database is unavailable.",
  ],
  sign_in_required: ["আবার সাইন ইন করুন।", "Sign in again."],
  session_expired: [
    "সেশনের মেয়াদ শেষ। আবার সাইন ইন করুন।",
    "Your session expired. Sign in again.",
  ],
  role_forbidden: [
    "এই কাজ করার অনুমতি নেই।",
    "Your role does not allow this action.",
  ],
  demo_disabled: [
    "এই পরিবেশে ডেমো সাইন-ইন বন্ধ।",
    "Demo sign-in is disabled in this environment.",
  ],
  demo_seed_required: [
    "ডেমো অ্যাকাউন্ট প্রস্তুত করা হয়নি।",
    "The demo accounts have not been seeded.",
  ],
  not_found: ["তথ্যটি পাওয়া যায়নি।", "This record was not found."],
  insufficient_stock: [
    "এই পরিমাণ মজুত খালি নেই।",
    "That quantity is no longer available.",
  ],
  invalid_transition: [
    "বর্তমান অবস্থায় কাজটি করা যাবে না।",
    "This action is unavailable in the current state. Refresh the page.",
  ],
  idempotency_conflict: [
    "তথ্য বদলেছে। পৃষ্ঠাটি রিফ্রেশ করুন।",
    "The details changed. Refresh the page and try again.",
  ],
  offer_expired: ["অফারের মেয়াদ শেষ।", "The offer has expired."],
  confirmation_required: ["চুক্তির শর্ত নিশ্চিত করুন।", "Confirm the terms first."],
  image_invalid: [
    "সঠিক JPEG, PNG বা WebP ছবি দিন।",
    "Choose a valid JPEG, PNG or WebP image.",
  ],
  image_too_large: [
    "ছবির আকার অনুমোদিত সীমা ছাড়িয়েছে।",
    "The image exceeds the allowed size.",
  ],
  photos_required: ["দুই থেকে চারটি ছবি যোগ করুন।", "Attach two to four photos."],
};

export function errorText(locale: Locale, code: string) {
  return local(locale, ...(errors[code] ?? errors.invalid_input));
}
