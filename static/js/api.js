

async function apiRequest(url, { method = "GET", json = null } = {}) {
  const options = {
    method,
    credentials: "same-origin", // IMPORTANT: sends Flask session cookie
    headers: {},
  };

  // Attach JSON payload if provided
  if (json !== null) {
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(json);
  }

  const response = await fetch(url, options);

  // Try to parse JSON response
  let data = {};
  try {
    data = await response.json();
  } catch (_) {
    data = {};
  }

  // Standardised error handling
  if (!response.ok) {
    const message =
      data?.error ||
      data?.message ||
      `Request failed (${response.status})`;
    throw new Error(message);
  }

  return data;
}

