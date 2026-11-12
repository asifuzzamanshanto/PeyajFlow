const databaseStatuses = [
  "ready",
  "unconfigured",
  "unreachable",
  "migration_required",
] as const;

type DatabaseStatus = (typeof databaseStatuses)[number];

type Health = {
  api: "online" | "offline";
  database: DatabaseStatus | "unknown";
};

const unavailable: Health = { api: "offline", database: "unknown" };

function isDatabaseStatus(value: unknown): value is DatabaseStatus {
  return databaseStatuses.some((status) => status === value);
}

export async function readHealth(
  baseUrl: string,
  request = fetch,
): Promise<Health> {
  try {
    const response = await request(new URL("/health/ready", baseUrl), {
      cache: "no-store",
      signal: AbortSignal.timeout(4000),
    });
    if (response.status !== 200 && response.status !== 503) return unavailable;

    const payload: unknown = await response.json();
    if (
      typeof payload !== "object" ||
      payload === null ||
      !("database" in payload)
    ) {
      return unavailable;
    }
    const status = payload.database;
    if (!isDatabaseStatus(status) || response.ok !== (status === "ready"))
      return unavailable;

    return { api: "online", database: status };
  } catch {
    return unavailable;
  }
}
