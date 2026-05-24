const DEFAULT_ATTEMPTS = 3;
const BASE_DELAY_MS = 400;

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/** Retry only on network failures (not HTTP 4xx/5xx). */
export async function fetchWithRetry(
  input: RequestInfo | URL,
  init?: RequestInit,
  attempts: number = DEFAULT_ATTEMPTS,
): Promise<Response> {
  let lastError: unknown;
  for (let i = 0; i < attempts; i++) {
    try {
      return await fetch(input, init);
    } catch (err) {
      lastError = err;
      if (i < attempts - 1) {
        await sleep(BASE_DELAY_MS * (i + 1));
      }
    }
  }
  throw lastError instanceof Error ? lastError : new Error("Network request failed");
}
