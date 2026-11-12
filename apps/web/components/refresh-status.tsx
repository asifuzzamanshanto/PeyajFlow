"use client";

import { useRouter } from "next/navigation";
import { useTransition } from "react";

export function RefreshStatus({
  label,
  pendingLabel,
}: {
  label: string;
  pendingLabel: string;
}) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();

  return (
    <button
      className="refresh"
      type="button"
      disabled={isPending}
      onClick={() => startTransition(() => router.refresh())}
    >
      {isPending ? pendingLabel : label}
    </button>
  );
}
