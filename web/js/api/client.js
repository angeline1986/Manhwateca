export async function getJson(path) {
  try {
    const response = await fetch(path, { cache: "no-store" });
    return parseJsonResponse(response);
  } catch (error) {
    throw new ApiNetworkError("Não foi possível acessar o servidor da Manhwateca.", error);
  }
}

export async function postJson(path, payload = {}) {
  try {
    const response = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    return parseJsonResponse(response);
  } catch (error) {
    throw new ApiNetworkError("Não foi possível acessar o servidor da Manhwateca.", error);
  }
}

export async function parseJsonResponse(response) {
  const text = await response.text();
  if (!text.trim()) {
    throw new ApiResponseError(
      response,
      "O servidor da Manhwateca retornou uma resposta vazia."
    );
  }
  let payload;
  try {
    payload = JSON.parse(text);
  } catch (error) {
    throw new ApiResponseError(
      response,
      "O servidor da Manhwateca retornou JSON inválido.",
      error
    );
  }
  return { response, payload };
}

export class ApiNetworkError extends Error {
  constructor(message, cause) {
    super(message);
    this.name = "ApiNetworkError";
    this.cause = cause;
  }
}

export class ApiResponseError extends Error {
  constructor(response, message, cause) {
    super(message);
    this.name = "ApiResponseError";
    this.response = response;
    this.cause = cause;
  }
}
