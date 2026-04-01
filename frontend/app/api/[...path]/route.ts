import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

async function proxyRequest(req: NextRequest) {
  const path = req.nextUrl.pathname.replace(/^\/api/, "");
  const url = `${BACKEND_URL}${path}${req.nextUrl.search}`;

  const headers = new Headers();
  headers.set("Content-Type", req.headers.get("Content-Type") || "application/json");

  // Forward cookies for auth
  const cookie = req.headers.get("cookie");
  if (cookie) {
    headers.set("cookie", cookie);
  }

  // Forward authorization header
  const auth = req.headers.get("authorization");
  if (auth) {
    headers.set("authorization", auth);
  }

  const fetchOptions: RequestInit = {
    method: req.method,
    headers,
  };

  // Forward body for non-GET requests
  if (req.method !== "GET" && req.method !== "HEAD") {
    const body = await req.text();
    if (body) {
      fetchOptions.body = body;
    }
  }

  try {
    const backendRes = await fetch(url, fetchOptions);
    const data = await backendRes.text();

    const response = new NextResponse(data, {
      status: backendRes.status,
      statusText: backendRes.statusText,
    });

    // Copy response headers
    response.headers.set("Content-Type", backendRes.headers.get("Content-Type") || "application/json");

    // Forward set-cookie headers from backend
    const setCookies = backendRes.headers.getSetCookie?.() || [];
    for (const c of setCookies) {
      response.headers.append("Set-Cookie", c);
    }

    return response;
  } catch {
    return NextResponse.json(
      { detail: "Backend server is not reachable. Make sure FastAPI is running on " + BACKEND_URL },
      { status: 502 }
    );
  }
}

export async function GET(req: NextRequest) {
  return proxyRequest(req);
}

export async function POST(req: NextRequest) {
  return proxyRequest(req);
}

export async function PUT(req: NextRequest) {
  return proxyRequest(req);
}

export async function DELETE(req: NextRequest) {
  return proxyRequest(req);
}

export async function PATCH(req: NextRequest) {
  return proxyRequest(req);
}
