import { apiResponse, ApiError } from "../../../../../../lib/workspace-api";

export async function GET(
  _request: Request,
  { params }: RouteContext<"/[locale]/workspace/photos/[lot]/[photo]">,
) {
  const { lot, photo } = await params;
  try {
    const response = await apiResponse(
      `/v1/lots/${encodeURIComponent(lot)}/inspection-photos/${encodeURIComponent(photo)}`,
    );
    return new Response(response.body, {
      headers: {
        "Content-Type": "image/jpeg",
        "Cache-Control": "private, no-store",
        "X-Content-Type-Options": "nosniff",
      },
    });
  } catch (error) {
    if (!(error instanceof ApiError)) throw error;
    return new Response(null, {
      status: error.status,
      headers: { "Cache-Control": "no-store" },
    });
  }
}
