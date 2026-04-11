"use strict";

const http = require("http");
const { URL } = require("url");

const PORT = Number(process.env.PORT || 8080);
const PYTHON_MODEL_SERVICE_URL = process.env.PYTHON_MODEL_SERVICE_URL || "http://localhost:5000/predict";
const MODEL_NAME = process.env.MODEL_NAME || "dropoff_classifier";
const MODEL_VERSION = process.env.MODEL_VERSION || "v1";

function sendJson(res, statusCode, payload) {
  const body = JSON.stringify(payload);
  res.writeHead(statusCode, {
    "Content-Type": "application/json",
    "Content-Length": Buffer.byteLength(body),
  });
  res.end(body);
}

function readJsonBody(req) {
  return new Promise((resolve, reject) => {
    let raw = "";
    req.on("data", (chunk) => {
      raw += chunk;
      if (raw.length > 1_000_000) {
        reject(new Error("Payload too large"));
      }
    });
    req.on("end", () => {
      try {
        resolve(raw ? JSON.parse(raw) : {});
      } catch (err) {
        reject(new Error("Invalid JSON payload"));
      }
    });
    req.on("error", reject);
  });
}

function validatePublicRequest(body) {
  if (!body || typeof body !== "object") {
    return "Request body must be a JSON object";
  }

  const requiredTopLevel = ["request_id", "user", "session", "features"];
  for (const field of requiredTopLevel) {
    if (!(field in body)) {
      return `Missing required field: ${field}`;
    }
  }

  return null;
}

function mapPublicToPythonPayload(body) {
  return {
    days_signup_age: body.features.days_signup_age,
    recency_days: body.features.recency_days,
    frequency_total: body.features.frequency_total,
    session_duration_avg: body.features.session_duration_avg,
    feature_count_used: body.features.feature_count_used,
    device_type: body.session.device_type,
    os_type: body.session.os_type,
    user_segment: body.user.segment,
    region: body.user.region,
  };
}

function mapPythonToPublicResponse(requestId, pythonResp, latencyMs) {
  return {
    request_id: requestId,
    prediction: {
      dropoff_probability: pythonResp.dropoff_probability,
      risk_label: pythonResp.risk_level,
      predicted_label: pythonResp.predicted_label,
      threshold_used: pythonResp.threshold_used,
      top_reasons: [],
    },
    model: {
      model_name: MODEL_NAME,
      model_version: MODEL_VERSION,
    },
    meta: {
      inference_timestamp_utc: new Date().toISOString(),
      latency_ms: latencyMs,
    },
  };
}

async function handlePredict(req, res) {
  const started = Date.now();
  let body;

  try {
    body = await readJsonBody(req);
  } catch (err) {
    return sendJson(res, 400, {
      request_id: "",
      error: {
        code: "VALIDATION_ERROR",
        message: err.message,
        details: [],
      },
    });
  }

  const validationError = validatePublicRequest(body);
  if (validationError) {
    return sendJson(res, 422, {
      request_id: String(body.request_id || ""),
      error: {
        code: "VALIDATION_ERROR",
        message: validationError,
        details: [],
      },
    });
  }

  const requestId = String(body.request_id);
  const pythonPayload = mapPublicToPythonPayload(body);

  let upstreamResp;
  try {
    upstreamResp = await fetch(PYTHON_MODEL_SERVICE_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Request-Id": requestId,
      },
      body: JSON.stringify(pythonPayload),
    });
  } catch (err) {
    return sendJson(res, 502, {
      request_id: requestId,
      error: {
        code: "UPSTREAM_ERROR",
        message: `Failed to reach Python model service: ${err.message}`,
        details: [],
      },
    });
  }

  let upstreamJson = {};
  try {
    upstreamJson = await upstreamResp.json();
  } catch (err) {
    return sendJson(res, 502, {
      request_id: requestId,
      error: {
        code: "UPSTREAM_ERROR",
        message: "Python model service returned non-JSON response",
        details: [],
      },
    });
  }

  if (!upstreamResp.ok) {
    return sendJson(res, 400, {
      request_id: requestId,
      error: {
        code: "VALIDATION_ERROR",
        message: String(upstreamJson.error || "Prediction failed"),
        details: [],
      },
    });
  }

  const latencyMs = Date.now() - started;
  return sendJson(res, 200, mapPythonToPublicResponse(requestId, upstreamJson, latencyMs));
}

const server = http.createServer(async (req, res) => {
  const parsedUrl = new URL(req.url, `http://${req.headers.host}`);

  if (req.method === "GET" && parsedUrl.pathname === "/health") {
    return sendJson(res, 200, {
      status: "ok",
      service: "node-gateway-adapter",
      python_model_service_url: PYTHON_MODEL_SERVICE_URL,
    });
  }

  if (req.method === "POST" && parsedUrl.pathname === "/v1/dropoff/predict") {
    return handlePredict(req, res);
  }

  return sendJson(res, 404, {
    error: {
      code: "NOT_FOUND",
      message: "Route not found",
    },
  });
});

server.listen(PORT, () => {
  console.log(`Gateway adapter listening on http://localhost:${PORT}`);
  console.log(`Forwarding predictions to ${PYTHON_MODEL_SERVICE_URL}`);
});
