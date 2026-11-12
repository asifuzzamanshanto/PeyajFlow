"use client";

import { useSyncExternalStore } from "react";
import type { Locale } from "../../lib/copy";
import { local } from "../../lib/workspace-copy";

function subscribe(update: () => void) {
  window.addEventListener("online", update);
  window.addEventListener("offline", update);
  return () => {
    window.removeEventListener("online", update);
    window.removeEventListener("offline", update);
  };
}

export function OfflineNotice({ locale }: { locale: Locale }) {
  const online = useSyncExternalStore(
    subscribe,
    () => navigator.onLine,
    () => true,
  );
  if (online) return null;
  return (
    <p className="work-panel offline-notice" role="status">
      {local(
        locale,
        "ইন্টারনেট সংযোগ নেই। কাজ পাঠানোর আগে সংযোগ ফিরে আসা পর্যন্ত অপেক্ষা করুন।",
        "You are offline. Reconnect before submitting a change.",
      )}
    </p>
  );
}
