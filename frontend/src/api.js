
const BASE = (
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"
).replace(/\/$/, "");

async function request(path, options = {}) {
  let res;

  try {
    res = await fetch(BASE + path, options);
  } catch {
    throw new Error(
      `Cannot reach ${BASE}. Start FastAPI and check CORS settings.`
    );
  }

  const ct = res.headers.get("content-type") || "";
  const data = ct.includes("application/json")
    ? await res.json()
    : await res.text();

  if (!res.ok) {
    throw new Error(
      typeof data === "object"
        ? data.detail || data.message || JSON.stringify(data)
        : data || `Request failed (${res.status})`
    );
  }

  return data;
}

export const api = {
  health: () => request("/health"),

  // Upload one PDF (existing functionality).
  upload: (file) => {
    const form = new FormData();
    form.append("file", file);

    return request("/documents/upload", {
      method: "POST",
      body: form,
    });
  },

  // Upload multiple PDFs using the existing endpoint.
  // Each PDF is uploaded separately.
  uploadMany: async (files) => {
    const results = [];

    for (const file of files) {
      results.push(await api.upload(file));
    }

    return results;
  },

  ask: (body) =>
    request("/ask/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),

  search: (body) =>
    request("/search/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
};
