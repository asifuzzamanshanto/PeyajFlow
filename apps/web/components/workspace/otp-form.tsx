"use client";

import { startTransition, useActionState } from "react";
import type { Locale } from "../../lib/copy";
import { errorText, local } from "../../lib/workspace-copy";
import type { FormAction } from "./form";

export function OtpSendForm({
  locale,
  action,
  label,
  children,
}: {
  locale: Locale;
  action: FormAction;
  label: string;
  children?: React.ReactNode;
}) {
  const [state, submit, pending] = useActionState(action, {});
  const error = state.error;

  return (
    <form
      action={async (formData: FormData) => {
        if (pending) return;
        startTransition(() => submit(formData));
      }}
      className="work-form"
    >
      {children}
      {error && (
        <p className="form-error" role="alert">
          {error.startsWith("otp_sent_dev:")
            ? local(
                locale,
                `ওটিপি পাঠানো হয়েছে: ${error.split(":")[1]} (শুধু ডেভ মোড)`,
                `OTP sent: ${error.split(":")[1]} (dev only)`,
              )
            : errorText(locale, error)}
        </p>
      )}
      <button type="submit" className="refresh" disabled={pending}>
        {pending ? local(locale, "অপেক্ষা করুন…", "Please wait…") : label}
      </button>
    </form>
  );
}
