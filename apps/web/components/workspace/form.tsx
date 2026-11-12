"use client";

import { startTransition, useActionState, type ReactNode } from "react";
import type { Locale } from "../../lib/copy";
import { errorText, local } from "../../lib/workspace-copy";

export type FormState = { error?: string };
export type FormAction = (
  state: FormState,
  form: FormData,
) => Promise<FormState>;

export function WorkspaceForm({
  locale,
  action,
  label,
  children,
}: {
  locale: Locale;
  action: FormAction;
  label: string;
  children?: ReactNode;
}) {
  const [state, submit, pending] = useActionState(action, {});
  return (
    <form
      action={submit}
      className="work-form"
      onSubmit={(event) => {
        event.preventDefault();
        const data = new FormData(event.currentTarget);
        startTransition(() => submit(data));
      }}
    >
      {children}
      {state.error && (
        <p className="form-error" role="alert">
          {errorText(locale, state.error)}
        </p>
      )}
      <button type="submit" className="refresh" disabled={pending}>
        {pending ? local(locale, "অপেক্ষা করুন…", "Please wait…") : label}
      </button>
    </form>
  );
}
