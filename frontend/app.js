
"use strict";

/* ============================================
   WATTMINDS 2.0 - BENTO DARK EDITION
   Frontend: HTML / CSS / Vanilla JavaScript
   ============================================ */

// ---------- Helpers ----------

const $ = (id) => document.getElementById(id);

const money = (value) =>
  "₹" + Number(value || 0).toLocaleString("en-IN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });

const number = (value, digits = 2) =>
  Number(value || 0).toLocaleString("en-IN", {
    maximumFractionDigits: digits
  });

const safe = (value) =>
  String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;"
  })[char]);

function first(object, keys, fallback = undefined) {
  if (!object || typeof object !== "object") return fallback;

  for (const key of keys) {
    if (object[key] !== undefined && object[key] !== null) {
      return object[key];
    }
  }

  return fallback;
}

function numeric(value) {
  if (value === "" || value === null || value === undefined) {
    return null;
  }

  const result = Number(value);
  return Number.isFinite(result) ? result : null;
}

let toastTimer;

function toast(message, error = false) {
  const element = $("toast");
  if (!element) return;

  element.textContent = message;
  element.className = "toast show" + (error ? " error" : "");

  clearTimeout(toastTimer);

  toastTimer = setTimeout(() => {
    element.className = "toast";
  }, 4700);
}

// ---------- API ----------

async function api(path, options = {}) {
  let response;

  try {
    response = await fetch("/api/" + path, options);
  } catch {
    throw new Error(
      "Cannot connect to FastAPI. Start the backend server."
    );
  }

  let payload;

  try {
    payload = await response.json();
  } catch {
    throw new Error("Server returned an invalid response.");
  }

  if (!response.ok) {
    let detail = payload.detail || "Request failed.";

    if (Array.isArray(detail)) {
      detail = detail
        .map((item) => item.msg || JSON.stringify(item))
        .join("; ");
    }

    throw new Error(String(detail));
  }

  return payload;
}

async function withLoading(button, callback) {
  const previousText = button.textContent;

  button.disabled = true;
  button.textContent = "Working...";

  try {
    await callback();
  } catch (error) {
    console.error(error);
    toast(error.message || String(error), true);
  } finally {
    button.disabled = false;
    button.textContent = previousText;
  }
}

// ---------- Navigation ----------

function navigate(view) {
  if (!$("view-" + view)) return;

  document.querySelectorAll(".view").forEach((element) => {
    element.classList.toggle(
      "active",
      element.id === "view-" + view
    );
  });

  document.querySelectorAll(".nav-item").forEach((element) => {
    element.classList.toggle(
      "active",
      element.dataset.view === view
    );
  });

  const link = document.querySelector(
    '.nav-item[data-view="' + view + '"]'
  );

  if (link && $("breadcrumb-current")) {
    $("breadcrumb-current").textContent =
      link.textContent.replace("⌘1", "").trim();
  }

  const sidebar = $("sidebar");

  if (sidebar) sidebar.classList.remove("open");

  const menu = $("menu-btn");

  if (menu) menu.setAttribute("aria-expanded", "false");

  try {
    history.replaceState(null, "", "#" + view);
  } catch {
    // Navigation works without History API.
  }

  if (view === "overview") {
    requestAnimationFrame(drawChart);
  }

  window.scrollTo({
    top: 0,
    behavior: "smooth"
  });
}

document.querySelectorAll("[data-view]").forEach((element) => {
  element.addEventListener("click", () => {
    navigate(element.dataset.view);
  });
});

document.querySelectorAll("[data-go]").forEach((element) => {
  element.addEventListener("click", () => {
    navigate(element.dataset.go);
  });
});

document.querySelectorAll("[data-view-link]").forEach((element) => {
  element.addEventListener("click", (event) => {
    event.preventDefault();
    navigate(element.dataset.viewLink);
  });
});

$("overview-action").addEventListener("click", () => {
  navigate("forecast");
});

$("side-upload").addEventListener("click", () => {
  navigate("forecast");
});

$("menu-btn").addEventListener("click", () => {
  const isOpen = $("sidebar").classList.toggle("open");

  $("menu-btn").setAttribute(
    "aria-expanded",
    String(isOpen)
  );
});

$("date-chip").textContent = new Intl.DateTimeFormat("en-IN", {
  day: "2-digit",
  month: "short",
  year: "numeric"
}).format(new Date());

// ---------- Backend Health ----------

async function updateHealth() {
  try {
    const result = await api("health");

    $("sidebar-status").textContent = "API connected";
    $("header-status").textContent = "System online";

    $("sidebar-status-dot").classList.add("online");
    $("header-status-dot").classList.add("online");

    if (!result.src_found) {
      toast("Python src folder was not found.", true);
    }
  } catch {
    $("sidebar-status").textContent = "API offline";
    $("header-status").textContent = "Disconnected";

    $("sidebar-status-dot").classList.remove("online");
    $("header-status-dot").classList.remove("online");

    toast("FastAPI backend is not running.", true);
  }
}

// ============================================
// CONSUMPTION CHART
// ============================================

// Demo data until user uploads real readings.
let chartData = [
  0.45, 0.42, 0.38, 0.35, 0.33, 0.42,
  0.71, 1.10, 0.90, 0.79, 0.74, 0.82,
  0.88, 0.94, 1.13, 1.26, 1.16, 1.38,
  1.48, 1.52, 1.72, 1.61, 1.13, 0.68
];

let chartLabels = chartData.map((_, index) =>
  String(index).padStart(2, "0")
);

function drawChart() {
  const canvas = $("consumption-chart");

  if (!canvas || !canvas.offsetWidth) return;

  const bounds = canvas.getBoundingClientRect();
  const scale = window.devicePixelRatio || 1;

  const width = bounds.width;
  const height = bounds.height;

  canvas.width = Math.round(width * scale);
  canvas.height = Math.round(height * scale);

  const ctx = canvas.getContext("2d");
  ctx.scale(scale, scale);

  const padding = {
    left: 39,
    right: 16,
    top: 18,
    bottom: 27
  };

  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  const maximum = Math.max(
    2,
    ...chartData.filter(Number.isFinite)
  ) * 1.12;

  // Dark theme chart grid and axis labels.
  ctx.font = "11px Inter, system-ui, sans-serif";
  ctx.textAlign = "right";

  for (let i = 0; i <= 4; i++) {
    const y = padding.top + chartHeight * i / 4;

    ctx.strokeStyle = "#293b43";
    ctx.lineWidth = 1;

    ctx.beginPath();
    ctx.moveTo(padding.left, y);
    ctx.lineTo(width - padding.right, y);
    ctx.stroke();

    ctx.fillStyle = "#a6b6c2";

    ctx.fillText(
      (maximum * (4 - i) / 4).toFixed(1),
      padding.left - 9,
      y + 4
    );
  }

  ctx.textAlign = "center";
  ctx.fillStyle = "#a6b6c2";

  const step = Math.max(
    1,
    Math.ceil(chartData.length / 6)
  );

  for (let i = 0; i < chartData.length; i += step) {
    const x =
      padding.left +
      chartWidth * i / Math.max(1, chartData.length - 1);

    const label = chartLabels[i] || String(i);

    ctx.fillText(
      label + (label.length === 2 ? ":00" : ""),
      x,
      height - 6
    );
  }

  const points = chartData.map((value, index) => ({
    x:
      padding.left +
      chartWidth * index / Math.max(1, chartData.length - 1),

    y:
      padding.top +
      chartHeight -
      value / maximum * chartHeight
  }));

  if (!points.length) return;

  // Area beneath the graph.
  ctx.beginPath();
  ctx.moveTo(points[0].x, points[0].y);

  points.slice(1).forEach((point) => {
    ctx.lineTo(point.x, point.y);
  });

  ctx.lineTo(
    points[points.length - 1].x,
    padding.top + chartHeight
  );

  ctx.lineTo(
    points[0].x,
    padding.top + chartHeight
  );

  ctx.closePath();

  const gradient = ctx.createLinearGradient(
    0,
    padding.top,
    0,
    height
  );

  gradient.addColorStop(0, "rgba(73,217,172,0.21)");
  gradient.addColorStop(1, "rgba(73,217,172,0)");

  ctx.fillStyle = gradient;
  ctx.fill();

  // Energy consumption line.
  ctx.beginPath();

  points.forEach((point, index) => {
    if (index === 0) {
      ctx.moveTo(point.x, point.y);
    } else {
      ctx.lineTo(point.x, point.y);
    }
  });

  ctx.strokeStyle = "#49d9ac";
  ctx.lineWidth = 2.7;
  ctx.lineJoin = "round";
  ctx.lineCap = "round";
  ctx.stroke();

  // Last observation marker.
  const last = points[points.length - 1];

  ctx.fillStyle = "#49d9ac";
  ctx.beginPath();
  ctx.arc(last.x, last.y, 4, 0, Math.PI * 2);
  ctx.fill();
}

window.addEventListener("resize", () => {
  requestAnimationFrame(drawChart);
});

// ============================================
// APPLIANCE STUDIO
// ============================================

const initialAppliances = [
  {
    name: "Air Conditioner",
    watts: 1500,
    hours: 6,
    quantity: 1
  },
  {
    name: "Refrigerator",
    watts: 200,
    hours: 8,
    quantity: 1
  },
  {
    name: "LED Bulb",
    watts: 9,
    hours: 6,
    quantity: 4
  }
];

function addApplianceRow(
  row = {
    name: "",
    watts: 100,
    hours: 4,
    quantity: 1
  }
) {
  const tr = document.createElement("tr");

  tr.innerHTML = `
    <td>
      <input
        class="app-name"
        placeholder="Appliance"
        value="${safe(row.name)}"
        required
      >
    </td>

    <td>
      <input
        class="app-watts"
        type="number"
        min="0"
        step="any"
        value="${Number(row.watts)}"
        required
      >
    </td>

    <td>
      <input
        class="app-hours"
        type="number"
        min="0"
        max="24"
        step="any"
        value="${Number(row.hours)}"
        required
      >
    </td>

    <td>
      <input
        class="app-qty"
        type="number"
        min="1"
        max="100"
        step="1"
        value="${Number(row.quantity)}"
        required
      >
    </td>

    <td>
      <button
        class="delete-row"
        type="button"
        title="Remove appliance"
      >
        ×
      </button>
    </td>
  `;

  tr.querySelector(".delete-row").addEventListener(
    "click",
    () => {
      if ($("appliance-rows").children.length <= 1) {
        toast("Keep at least one appliance.", true);
        return;
      }

      tr.remove();
    }
  );

  $("appliance-rows").appendChild(tr);
}

initialAppliances.forEach(addApplianceRow);

$("add-appliance").addEventListener("click", () => {
  addApplianceRow();
});

function toAdviceList(raw) {
  if (raw === null || raw === undefined) return [];

  if (Array.isArray(raw)) {
    return raw.flatMap(toAdviceList).slice(0, 12);
  }

  if (typeof raw === "string" || typeof raw === "number") {
    return [String(raw)];
  }

  if (typeof raw === "object") {
    if ("message" in raw) {
      return [String(raw.message)];
    }

    if ("recommendation" in raw) {
      return [String(raw.recommendation)];
    }

    // Weather agent alert objects.
    if ("Title" in raw && "Action" in raw) {
      return [
        `${raw.Title}: ${raw.Reason || ""} ${raw.Action}`
      ];
    }

    return Object.entries(raw)
      .map(([key, value]) => {
        const text = typeof value === "object"
          ? JSON.stringify(value)
          : value;

        return `${key}: ${text}`;
      })
      .slice(0, 12);
  }

  return [];
}

function renderAdvice(target, values, emptyText) {
  const items = toAdviceList(values);

  target.innerHTML = (
    items.length ? items : [emptyText]
  ).map((item) => `
    <div class="insight">
      ${safe(item)}
    </div>
  `).join("");
}

$("appliance-form").addEventListener(
  "submit",
  (event) => {
    event.preventDefault();

    withLoading($("manual-submit"), async () => {
      const appliances = [
        ...$("appliance-rows").querySelectorAll("tr")
      ].map((tr) => ({
        name: tr.querySelector(".app-name").value.trim(),
        watts: Number(tr.querySelector(".app-watts").value),
        hours: Number(tr.querySelector(".app-hours").value),
        quantity: Number(tr.querySelector(".app-qty").value)
      }));

      const tariff = Number($("manual-tariff").value);

      const output = await api("manual", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          appliances,
          tariff,
          target_savings: Number($("manual-target").value)
        })
      });

      const result = output.result || {};

      const daily = numeric(
        first(result, [
          "total_daily_energy_kwh",
          "daily_energy_kwh"
        ])
      );

      const cost = numeric(
        first(result, [
          "total_monthly_cost",
          "monthly_cost"
        ])
      );

      const savings = numeric(
        first(result, [
          "projected_savings",
          "potential_monthly_savings"
        ])
      );

      $("manual-placeholder").classList.add("hidden");
      $("manual-result").classList.remove("hidden");

      $("appliance-daily").textContent =
        daily === null ? "—" : number(daily) + " kWh";

      $("appliance-bill").textContent =
        cost === null ? "—" : money(cost);

      $("appliance-savings").textContent =
        savings === null ? "—" : money(savings);

      const summary = appliances.map((item) => ({
        name: item.name,
        energy:
          item.watts * item.hours * item.quantity / 1000
      }));

      const maximum = Math.max(
        0.001,
        ...summary.map((item) => item.energy)
      );

      $("appliance-bars").innerHTML = summary
        .sort((a, b) => b.energy - a.energy)
        .map((item) => `
          <div class="breakdown-row">
            <div class="breakdown-row-head">
              <span>${safe(item.name)}</span>
              <strong>${number(item.energy)} kWh/day</strong>
            </div>
            <div class="bar-track">
              <div
                class="bar-fill"
                style="width:${(
                  item.energy / maximum * 100
                ).toFixed(1)}%"
              ></div>
            </div>
          </div>
        `)
        .join("");

      renderAdvice(
        $("appliance-recs"),
        first(result, [
          "recommendations",
          "action_plan",
          "analysis"
        ]),
        "Analysis completed. Check the appliance breakdown."
      );

      if (daily !== null) {
        $("metric-energy").textContent = number(daily);
        $("metric-cost").textContent = number(daily * tariff);

        $("metric-analysis").textContent = "Analyzed";

        $("metric-analysis-foot").textContent =
          appliances.length + " appliance types";

        $("overview-source").textContent =
          "Derived from entered appliance information";

        $("overview-badge").textContent = "YOUR INPUT";

        const energyFoot = $("metric-energy")
          .parentElement
          .parentElement
          .querySelector(".metric-foot");

        const costFoot = $("metric-cost")
          .parentElement
          .parentElement
          .querySelector(".metric-foot");

        if (energyFoot) {
          energyFoot.textContent =
            "Estimated from entered appliances";
        }

        if (costFoot) {
          costFoot.textContent =
            `At ₹${number(tariff)} per kWh`;
        }
      }

      toast("Appliance analysis completed.");
    });
  }
);

// ============================================
// CSV UPLOAD HELPERS
// ============================================

function setupUpload(inputId, labelId) {
  const input = $(inputId);

  input.addEventListener("change", () => {
    const file = input.files[0];

    $(labelId).textContent = file
      ? file.name
      : "No file selected";
  });
}

setupUpload("forecast-file", "forecast-filename");
setupUpload("anomaly-file", "anomaly-filename");

function collectNumbers(object, prefix = "", depth = 0) {
  if (
    depth > 3 ||
    !object ||
    typeof object !== "object"
  ) {
    return [];
  }

  return Object.entries(object).flatMap(([key, value]) => {
    const fullKey = (prefix + " " + key).trim();

    if (
      typeof value === "number" &&
      Number.isFinite(value)
    ) {
      return [{
        key: fullKey,
        value
      }];
    }

    if (
      value &&
      typeof value === "object" &&
      !Array.isArray(value)
    ) {
      return collectNumbers(value, fullKey, depth + 1);
    }

    return [];
  });
}

// ============================================
// ML ENERGY FORECAST
// ============================================

$("forecast-form").addEventListener("submit", (event) => {
  event.preventDefault();

  withLoading($("forecast-submit"), async () => {
    const file = $("forecast-file").files[0];

    if (!file) {
      throw new Error("Choose a CSV file first.");
    }

    const tariff = Number($("forecast-tariff").value);

    const form = new FormData();
    form.append("file", file);

    const output = await api(
      "forecast?tariff=" + encodeURIComponent(tariff),
      {
        method: "POST",
        body: form
      }
    );

    const result = output.result || {};

    $("forecast-placeholder").classList.add("hidden");
    $("forecast-result").classList.remove("hidden");

    const candidates = collectNumbers(result).filter(
      (item) =>
        /predicted|prediction|forecast/i.test(item.key) &&
        /energy|kwh|consumption/i.test(item.key)
    );

    const selected =
      candidates[0] ||
      collectNumbers(result).find(
        (item) => /predict|forecast/i.test(item.key)
      );

    $("forecast-primary").textContent = selected
      ? number(selected.value, 3) +
        (
          /kwh|energy|consumption/i.test(selected.key)
            ? " kWh"
            : ""
        )
      : "Prediction completed";

    $("forecast-primary-label").textContent = selected
      ? selected.key.replace(/_/g, " ")
      : "Review model response below";

    $("forecast-json").textContent =
      JSON.stringify(result, null, 2);

    $("metric-analysis").textContent = "Forecasted";

    $("metric-analysis-foot").textContent =
      "ML forecast response received";

    toast("ML forecast completed.");
  });
});

// ============================================
// STATISTICAL ANOMALY DETECTION
// ============================================

$("anomaly-form").addEventListener("submit", (event) => {
  event.preventDefault();

  withLoading($("anomaly-submit"), async () => {
    const file = $("anomaly-file").files[0];

    if (!file) {
      throw new Error("Choose an hourly energy CSV.");
    }

    const form = new FormData();
    form.append("file", file);

    const output = await api("anomalies", {
      method: "POST",
      body: form
    });

    const result = output.result || {};

    $("anomaly-placeholder").classList.add("hidden");
    $("anomaly-result").classList.remove("hidden");

    $("anomaly-rows").textContent =
      number(result.rows_analyzed, 0);

    $("anomaly-count").textContent =
      number(result.anomaly_count, 0);

    $("anomaly-rate").textContent =
      number(result.anomaly_rate_pct) + "%";

    $("metric-anomalies").textContent =
      number(result.anomaly_count, 0);

    $("metric-anomalies-foot").textContent =
      number(result.rows_analyzed, 0) + " readings analyzed";

    const anomalies = Array.isArray(result.anomalies)
      ? [...result.anomalies].reverse().slice(0, 15)
      : [];

    $("anomaly-table").innerHTML = anomalies.length
      ? anomalies.map((item) => {
          const isHigh = String(
            item.Anomaly_Type
          ).includes("High");

          const classification = isHigh
            ? "status-high"
            : "status-low";

          const expected = item.Expected_Energy_kWh == null
            ? "—"
            : number(item.Expected_Energy_kWh) + " kWh";

          return `
            <tr>
              <td>${number(item.Energy_kWh)} kWh</td>
              <td>${expected}</td>
              <td class="${classification}">
                ${safe(item.Anomaly_Type)}
              </td>
            </tr>
          `;
        }).join("")
      : `
          <tr>
            <td colspan="3">
              No anomalies were flagged in the uploaded readings.
            </td>
          </tr>
        `;

    $("anomaly-info").textContent =
      "Showing the latest 15 anomalies. " +
      "Statistical flags do not confirm equipment faults.";

    // Update overview chart using actual uploaded readings.
    const readings = (result.recent_readings || [])
      .filter((item) =>
        Number.isFinite(Number(item.Energy_kWh))
      )
      .slice(-24);

    if (readings.length > 1) {
      chartData = readings.map((item) =>
        Number(item.Energy_kWh)
      );

      chartLabels = readings.map((_, index) =>
        String(index + 1)
      );

      $("overview-chart-sub").textContent =
        "Latest readings from your uploaded CSV";

      $("overview-source").textContent =
        "Anomaly analysis completed using uploaded readings";

      $("overview-badge").textContent = "YOUR DATA";
    }

    toast(
      "Anomaly scan completed: " +
      result.anomaly_count +
      " flagged readings."
    );
  });
});

// ============================================
// WEATHER ADVISOR
// ============================================

function weatherInsights(result) {
  const values = [
    first(result, [
      "alerts",
      "recommendations",
      "advice",
      "energy_advice",
      "suggestions"
    ], null)
  ];

  const knownKeys = [
    "alerts",
    "recommendations",
    "advice",
    "suggestions"
  ];

  for (const [key, value] of Object.entries(result)) {
    if (
      /alert|recommend|suggest|advice|tip/i.test(key) &&
      !knownKeys.includes(key)
    ) {
      values.push(value);
    }
  }

  return values.flatMap(toAdviceList);
}

$("weather-form").addEventListener("submit", (event) => {
  event.preventDefault();

  withLoading($("weather-submit"), async () => {
    const appliances = [
      ...document.querySelectorAll(".check-cards input:checked")
    ].map((input) => input.value);

    const payload = {
      city: $("weather-city").value.trim(),
      appliances,
      tariff: Number($("weather-tariff").value)
    };

    if (!payload.city) {
      throw new Error("Please enter a city.");
    }

    const output = await api("weather", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    });

    const result = output.result || {};

    $("weather-placeholder").classList.add("hidden");
    $("weather-result").classList.remove("hidden");

    const city = first(
      result,
      ["city", "location", "name"],
      payload.city
    );

    const country = first(result, ["country"], "");

    $("weather-location").textContent = [
      city,
      country
    ].filter(Boolean).join(", ");

    const temperature = numeric(
      first(result, [
        "temperature_c",
        "temperature",
        "temp_c",
        "current_temperature",
        "temperature_2m"
      ])
    );

    $("weather-temp").textContent =
      temperature === null
        ? "Weather data"
        : number(temperature, 1) + "°C";

    const daytime = first(
      result,
      ["is_day", "is_daytime", "daytime"],
      null
    );

    $("weather-condition").textContent =
      daytime === null
        ? "Current conditions"
        : daytime
          ? "Daytime"
          : "Nighttime";

    const weatherIcon = document.querySelector(
      ".weather-big-icon"
    );

    if (weatherIcon) {
      weatherIcon.textContent =
        daytime === false || daytime === 0
          ? "☾"
          : "☀";
    }

    const extras = [
      [
        "Humidity",
        first(result, [
          "humidity_percent",
          "humidity",
          "relative_humidity",
          "relative_humidity_2m"
        ])
      ],
      ["Sunrise", result.sunrise],
      ["Sunset", result.sunset],
      ["Local time", result.local_time]
    ].filter(
      ([, value]) =>
        value !== null &&
        value !== undefined
    );

    $("weather-extra").innerHTML = extras.map(
      ([key, value]) => `
        <span>
          ${safe(key)}:
          ${safe(value)}${key === "Humidity" ? "%" : ""}
        </span>
      `
    ).join("");

    renderAdvice(
      $("weather-alerts"),
      weatherInsights(result),
      "No appliance-specific advice was generated."
    );

    $("weather-json").textContent =
      JSON.stringify(result, null, 2);

    toast("Weather analysis completed.");
  });
});

// ============================================
// WHAT-IF SIMULATOR
// ============================================

function updateSimulator() {
  const watts = Math.max(
    0,
    Number($("sim-watts").value) || 0
  );

  const hours = Math.max(
    0,
    Math.min(24, Number($("sim-hours").value) || 0)
  );

  const reduction = Math.max(
    0,
    Math.min(
      hours,
      Number($("sim-reduction").value) || 0
    )
  );

  const quantity = Math.max(
    1,
    Math.floor(Number($("sim-qty").value) || 1)
  );

  const tariff = Math.max(
    0,
    Number($("sim-tariff").value) || 0
  );

  $("sim-reduction-val").textContent =
    number(reduction, 1);

  const before =
    watts * hours * quantity / 1000 * 30 * tariff;

  const savingsKwh =
    watts * reduction * quantity / 1000 * 30;

  const after = Math.max(
    0,
    before - savingsKwh * tariff
  );

  $("sim-savings").textContent = money(before - after);

  $("sim-energy").textContent =
    number(savingsKwh) + " kWh saved per month";

  $("sim-before").textContent = money(before);
  $("sim-after").textContent = money(after);

  $("sim-track-fill").style.width =
    (
      before === 0
        ? 0
        : Math.max(0, after / before) * 100
    ) + "%";
}

[
  "sim-watts",
  "sim-hours",
  "sim-reduction",
  "sim-qty",
  "sim-tariff"
].forEach((id) => {
  $(id).addEventListener("input", updateSimulator);
});

updateSimulator();

// ============================================
// ENERGY COPILOT
// ============================================

// API calculations are triggered on every submit.
// After first successful analysis, changing inputs
// automatically requests a fresh result.

let copilotHasRun = false;
let copilotRevision = 0;
let copilotTimer = null;

const copilotFields = [
  "copilot-question",
  "agent-name",
  "agent-watts",
  "agent-hours",
  "agent-qty",
  "agent-tariff"
];

function getCopilotPayload() {
  return {
    question: $("copilot-question").value.trim(),

    tariff: Number($("agent-tariff").value),

    appliances: [
      {
        name: $("agent-name").value.trim(),
        watts: Number($("agent-watts").value),
        hours: Number($("agent-hours").value),
        quantity: Number($("agent-qty").value)
      }
    ]
  };
}

function validateCopilot(payload) {
  const appliance = payload.appliances[0];

  if (payload.question.length < 3) {
    throw new Error(
      "Question must contain at least 3 characters."
    );
  }

  if (!appliance.name) {
    throw new Error("Enter an appliance name.");
  }

  if (
    !Number.isFinite(appliance.watts) ||
    appliance.watts < 0
  ) {
    throw new Error("Power must be zero or greater.");
  }

  if (
    !Number.isFinite(appliance.hours) ||
    appliance.hours < 0 ||
    appliance.hours > 24
  ) {
    throw new Error("Hours/day must be between 0 and 24.");
  }

  if (
    !Number.isInteger(appliance.quantity) ||
    appliance.quantity < 1 ||
    appliance.quantity > 100
  ) {
    throw new Error("Quantity must be between 1 and 100.");
  }

  if (
    !Number.isFinite(payload.tariff) ||
    payload.tariff < 0
  ) {
    throw new Error("Tariff must be zero or greater.");
  }
}

async function updateCopilot(showToast = false) {
  const revision = ++copilotRevision;

  clearTimeout(copilotTimer);

  const payload = getCopilotPayload();

  validateCopilot(payload);

  const button = $("agent-submit");

  button.disabled = true;
  button.textContent = "Calculating...";

  try {
    const output = await api("copilot", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    });

    // Prevent an old request from replacing new results.
    if (revision !== copilotRevision) return;

    const result = output.result || {};

    $("agent-placeholder").classList.add("hidden");
    $("agent-result").classList.remove("hidden");

    // Assistant message.
    $("agent-answer").textContent =
      result.answer || "No response returned.";

    // Optional question bubble in updated Bento HTML.
    const questionPreview = document.querySelector(
      ".agent-question-preview"
    );

    if (questionPreview) {
      questionPreview.textContent = payload.question;
    }

    // Tools used by the decision engine.
    $("agent-tools").innerHTML = (
      result.tools_used || []
    ).map((tool) => `
      <span class="agent-pill">
        ${safe(String(tool).replaceAll("_", " "))}
      </span>
    `).join("") || `
      <span class="muted">
        No tools needed
      </span>
    `;

    // Recommended actions and potential savings.
    $("agent-actions").innerHTML = (
      result.actions || []
    ).map((action) => `
      <div class="agent-action">
        <strong>
          ${safe(action.appliance)}
        </strong>

        <span>
          Reduce
          ${number(action.reduction_hours_per_day, 1)}
          h/day -
          ${money(action.monthly_inr_saved)}/month
          (estimate)
        </span>
      </div>
    `).join("") || `
      <p class="muted small">
        Ask for saving suggestions to generate scenarios.
      </p>
    `;

    $("agent-assumptions").textContent =
      result.assumptions || "";

    copilotHasRun = true;

    // Make the assistant output visible on longer panels.
    const answer = $("agent-answer");

    answer.scrollIntoView({
      behavior: window.matchMedia(
        "(prefers-reduced-motion: reduce)"
      ).matches ? "auto" : "smooth",
      block: "nearest"
    });

    if (showToast) {
      toast("Energy Copilot analysis completed.");
    }

  } catch (error) {
    if (revision === copilotRevision) {
      throw error;
    }

  } finally {
    if (revision === copilotRevision) {
      button.disabled = false;
      button.textContent = "Run decision agent";
    }
  }
}

// Button submission.
$("copilot-form").addEventListener("submit", (event) => {
  event.preventDefault();

  updateCopilot(true).catch((error) => {
    console.error(error);
    toast(error.message || String(error), true);
  });
});

// Recalculate automatically after a previously successful run.
copilotFields.forEach((id) => {
  $(id).addEventListener("input", () => {
    ++copilotRevision;
    clearTimeout(copilotTimer);

    if (!copilotHasRun) return;

    // Hide outdated answer during recalculation.
    $("agent-result").classList.add("hidden");
    $("agent-placeholder").classList.remove("hidden");

    $("agent-submit").disabled = false;
    $("agent-submit").textContent = "Run decision agent";

    // Debounce avoids excessive API requests.
    copilotTimer = setTimeout(() => {
      updateCopilot().catch((error) => {
        console.error(error);
        toast(error.message || String(error), true);
      });
    }, 500);
  });
});

// ============================================
// ML PATTERN LAB
// ============================================

$("patterns-file").addEventListener("change", () => {
  const file = $("patterns-file").files[0];

  $("patterns-filename").textContent =
    file ? file.name : "No file selected";
});

$("patterns-form").addEventListener("submit", (event) => {
  event.preventDefault();

  withLoading($("patterns-submit"), async () => {
    const file = $("patterns-file").files[0];

    if (!file) {
      throw new Error("Select a CSV file first.");
    }

    const contamination =
      Number($("patterns-contamination").value) / 100;

    const form = new FormData();
    form.append("file", file);

    const output = await api(
      "ml-patterns?contamination=" +
        encodeURIComponent(contamination),
      {
        method: "POST",
        body: form
      }
    );

    const result = output.result || {};

    $("patterns-placeholder").classList.add("hidden");
    $("patterns-result").classList.remove("hidden");

    $("patterns-rows").textContent =
      number(result.total_scanned, 0);

    $("patterns-count").textContent =
      number(result.outliers, 0);

    $("patterns-median").textContent =
      number(result.typical_energy_kwh, 3);

    $("patterns-features").innerHTML = (
      result.features_used || []
    ).map((feature) => `
      <span class="agent-pill">
        ${safe(feature)}
      </span>
    `).join("");

    $("patterns-list").innerHTML = (
      result.highest_outlier_examples || []
    ).map((item, index) => `
      <div class="agent-action">
        <strong>
          Outlier ${index + 1}
        </strong>

        <span>
          ${number(item.Energy_kWh, 3)} kWh -
          Score ${number(item.anomaly_score, 4)}
        </span>
      </div>
    `).join("") || `
      <p class="muted small">
        No outlier examples to display.
      </p>
    `;

    $("patterns-notes").textContent =
      result.limitations || "";

    toast("ML Pattern Lab analysis completed.");
  });
});

// ============================================
// SUBTLE 3D CARD INTERACTION
// ============================================

function initializeCardAnimations() {
  const reducedMotion = window.matchMedia(
    "(prefers-reduced-motion: reduce)"
  );

  const finePointer = window.matchMedia(
    "(hover: hover) and (pointer: fine)"
  );

  if (reducedMotion.matches || !finePointer.matches) {
    return;
  }

  document.querySelectorAll(".metric-card").forEach((card) => {
    card.addEventListener("pointermove", (event) => {
      const bounds = card.getBoundingClientRect();

      const x =
        (event.clientX - bounds.left) / bounds.width - 0.5;

      const y =
        (event.clientY - bounds.top) / bounds.height - 0.5;

      card.style.transform = `
        perspective(850px)
        rotateX(${-y * 4}deg)
        rotateY(${x * 5}deg)
        translateY(-2px)
      `;
    });

    card.addEventListener("pointerleave", () => {
      card.style.transform = "";
    });
  });
}

initializeCardAnimations();

// ============================================
// INITIALIZE APPLICATION
// ============================================

const initialView = location.hash.substring(1);

navigate(
  $("view-" + initialView)
    ? initialView
    : "overview"
);

requestAnimationFrame(drawChart);
updateHealth();
