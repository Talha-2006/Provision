const DEFAULT_API_URL = "http://127.0.0.1:8000";

export async function POST(request: Request) {
  let payload: unknown;

  try {
    payload = await request.json();
  } catch {
    return Response.json({ detail: "Invalid JSON request." }, { status: 400 });
  }

  const apiUrl = (process.env.PROVISION_API_URL ?? DEFAULT_API_URL).replace(
    /\/+$/,
    "",
  );

  try {
    const response = await fetch(`${apiUrl}/ask`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
      cache: "no-store",
    });

    const responseBody = await response.text();

    return new Response(responseBody, {
      status: response.status,
      headers: {
        "Content-Type":
          response.headers.get("Content-Type") ?? "application/json",
      },
    });
  } catch {
    return Response.json(
      {
        detail:
          "Could not reach the Provision API. Make sure the backend is running on port 8000.",
      },
      { status: 503 },
    );
  }
}
