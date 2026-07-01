export async function getJson(path) {
  const response = await fetch(path, { cache: "no-store" });
  return parseJsonResponse(response);
}

export async function postJson(path, payload = {}) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return parseJsonResponse(response);
}

export async function parseJsonResponse(response) {
  const payload = await response.json();
  return { response, payload };
}
