import type { Locale } from "./copy";

export function asciiDigits(value: string): string {
  return value.replace(/[০-৯]/g, (digit) =>
    String(digit.charCodeAt(0) - 0x09e6),
  );
}

export function dhakaToday(): string {
  return new Intl.DateTimeFormat("sv-SE", { timeZone: "Asia/Dhaka" }).format(
    new Date(),
  );
}

export function timeLabel(locale: Locale, value: string): string {
  const options: Intl.DateTimeFormatOptions = {
    dateStyle: "medium",
    timeZone: "Asia/Dhaka",
  };
  if (value.includes("T"))
    Object.assign(options, { timeStyle: "short", hourCycle: "h23" });
  return new Intl.DateTimeFormat(
    locale === "bn" ? "bn-BD" : "en-GB",
    options,
  ).format(new Date(value.includes("T") ? value : `${value}T00:00:00+06:00`));
}

export function numberLabel(
  locale: Locale,
  value: string | number,
  money = false,
): string {
  const [whole, fraction = ""] = String(value).split(".");
  const integer = BigInt(whole);
  const sign = integer === 0n && whole.startsWith("-") ? "-" : "";
  const grouped =
    sign +
    new Intl.NumberFormat(locale === "bn" ? "bn-BD" : "en-BD").format(integer);
  const digits = money ? fraction.padEnd(2, "0") : fraction.replace(/0+$/, "");
  if (!digits) return grouped;
  const localized =
    locale === "bn"
      ? digits.replace(/\d/g, (digit) => "০১২৩৪৫৬৭৮৯"[Number(digit)])
      : digits;
  return `${grouped}.${localized}`;
}
