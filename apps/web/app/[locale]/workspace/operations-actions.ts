"use server";

import { redirect } from "next/navigation";
import type { FormState } from "../../../components/workspace/form";
import { isLocale, type Locale } from "../../../lib/copy";
import { api, ApiError, json } from "../../../lib/workspace-api";

type Operation =
  "read-alert" | "read-all" | "preferences" | "verify" | "resolve";

export async function operate(
  locale: Locale,
  operation: Operation,
  id: string,
  _state: FormState,
  form: FormData,
): Promise<FormState> {
  if (!isLocale(locale)) return { error: "invalid_input" };
  const resource = encodeURIComponent(id);
  const value = (name: string) => String(form.get(name) ?? "").trim();
  let destination = "alerts";
  try {
    switch (operation) {
      case "read-alert":
        await api(`/v1/notifications/${resource}/read`, { method: "POST" });
        break;
      case "read-all":
        await api("/v1/notifications/read-all", { method: "POST" });
        break;
      case "preferences":
        await api(
          "/v1/notifications/preferences",
          json(
            {
              sms_enabled: form.has("sms_enabled"),
              quiet_start: Number(value("quiet_start")),
              quiet_end: Number(value("quiet_end")),
            },
            "PUT",
          ),
        );
        break;
      case "verify":
        if (!form.has("confirm")) return { error: "confirmation_required" };
        await api(
          `/v1/admin/verifications/${resource}`,
          json({ verified: value("verified") === "true" }, "PUT"),
        );
        destination = "operations?view=accounts";
        break;
      case "resolve":
        if (!form.has("confirm")) return { error: "confirmation_required" };
        await api(
          `/v1/admin/disputes/${resource}/resolve`,
          json({ note: value("note"), confirmed: true }),
        );
        destination = "operations?view=disputes";
        break;
      default:
        return { error: "invalid_input" };
    }
  } catch (error) {
    if (!(error instanceof ApiError)) throw error;
    return { error: error.code };
  }
  redirect(
    `/${locale}/workspace/${destination}${destination.includes("?") ? "&" : "?"}saved=1`,
  );
}
