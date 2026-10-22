
"use strict";

/* =====================================================
   WATTMINDS 2.0 - RESPONSIVE WEB APPLICATION
   Vanilla JavaScript + FastAPI Integration
   ===================================================== */

// -------------------------
// 1. Utility Functions
// -------------------------

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
  if (!object || typeof object !== "object") {
    return fallback;
  }

  for (const key of keys) {
    if (object[key] !== undefined && object[key] !== null) {
      return object[key];
    }
  }

  return fallback;
}

function numeric(value) {
  if (value === null || value === undefined || value === "") {
    return null;
  }

  const result = Number(value);
  return Number.isFinite(result) ? result : null;
}

let toastTimer;

function toast(message, isError = false) {
  const element = $("toast");

  if (!element) return;

  element.textContent = String(message);
  element.className = "toast show" + (isError ? " error" : "");

  clearTimeout(toastTimer);

  toastTimer = setTimeout(() => {
    element.className = "toast";
  }, 4700);
}

// -------------------------
// 2. Backend API
// -------------------------

async function api(path, options = {}) {
  let response;

  try {
    response = await fetch("/api/" + path, options);
  } catch {
    throw new Error(
      "Cannot reach FastAPI. Start the WattMinds server."
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

async function withLoading(button, task) {
  const oldText = button.textContent;

  button.disabled = true;
  button.textContent = "Working...";

  try {
    await task();
  } catch (error) {
    console.error(error);
    toast(error.message || String(error), true);
  } finally {
    button.disabled = false;
    button.textContent = oldText;
  }
}

// -------------------------
// 3. Navigation
// -------------------------

const backdrop = document.querySelector(
  ".mobile-nav-backdrop"
);

function closeMenu() {
  $("sidebar").classList.remove("open");

  if (backdrop) {
    backdrop.classList.remove("show");
  }

  $("menu-btn").setAttribute("aria-expanded", "false");
  $("menu-btn").setAttribute(
    "aria-label",
    "Open navigation"
  );

  document.body.style.overflow = "";
}

function toggleMenu() {
  const isOpen = $("sidebar").classList.toggle("open");

  if (backdrop) {
    backdrop.classList.toggle("show", isOpen);
  }

  $("menu-btn").setAttribute(
    "aria-expanded",
    String(isOpen)
  );

  $("menu-btn").setAttribute(
    "aria-label",
    isOpen ? "Close navigation" : "Open navigation"
  );

  document.body.style.overflow = isOpen ? "hidden" : "";
}

function navigate(view) {
  if (!$("view-" + view)) return;

  document.querySelectorAll(".view").forEach((element) => {
    element.classList.toggle(
      "active",
      element.id === "view-" + view
    );
  });

  document.querySelectorAll(".nav-item").forEach((element) => {
    const active = element.dataset.view === view;

    element.classList.toggle("active", active);

    if (active) {
      element.setAttribute("aria-current", "page");
    } else {
      element.removeAttribute("aria-current");
    }
  });

  const link = document.querySelector(
    `.nav-item[data-view="${view}"]`
  );

  if (link && $("breadcrumb-current")) {
    $("breadcrumb-current").textContent =
      link.textContent.replace("⌘1", "").trim();
  }

  closeMenu();

  try {
    history.replaceState(null, "", "#" + view);
  } catch {
    // Hash navigation still works.
  }

  if (view === "overview") {
    requestAnimationFrame(drawChart);
  }

  window.scrollTo({
    top: 0,
    behavior: window.matchMedia(
      "(prefers-reduced-motion: reduce)"
    ).matches ? "auto" : "smooth"
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

$("menu-btn").addEventListener("click", toggleMenu);

if (backdrop) {
  backdrop.addEventListener("click", closeMenu);
}

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    closeMenu();
  }
});

window.addEventListener("resize", () => {
  if (window.innerWidth > 850) {
    closeMenu();
  }

  requestAnimationFrame(drawChart);
});

$("overview-action").addEventListener("click", () => {
  navigate("forecast");
});

$("side-upload").addEventListener("click", () => {
  navigate("forecast");
});

$("date-chip").textContent = new Intl.DateTimeFormat("en-IN", {
  day: "2-digit",
  month: "short",
  year: "numeric"
}).format(new Date());

// -------------------------
// 4. API Health
// -------------------------

async function updateHealth() {
  try {
    const info = await api("health");

    $("sidebar-status").textContent = "API connected";
    $("header-status").textContent = "System online";

    $("sidebar-status-dot").classList.add("online");
    $("header-status-dot").classList.add("online");

    if (!info.src_found) {
      toast("The Python src folder is missing.", true);
    }
  } catch {
    $("sidebar-status").textContent = "API offline";
    $("header-status").textContent = "Disconnected";

    $("sidebar-status-dot").classList.remove("online");
    $("header-status-dot").classList.remove("online");

    toast("Connect to your FastAPI backend.", true);
  }
}

// -------------------------
// 5. Energy Chart
// -------------------------

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

  if (!canvas || !canvas.offsetWidth) {
    return;
  }

  const bounds = canvas.getBoundingClientRect();
  const scale = window.devicePixelRatio || 1;

  const width = bounds.width;
  const height = bounds.height;

  canvas.width = Math.round(width * scale);
  canvas.height = Math.round(height * scale);

  const context = canvas.getContext("2d");

  if (!context) return;

  context.scale(scale, scale);

  const padding = {
    left: 37,
    right: 14,
    top: 18,
    bottom: 29
  };

  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  const maxY = Math.max(
    2,
    ...chartData.filter(Number.isFinite)
  ) * 1.12;

  context.font = "10px Inter, system-ui, sans-serif";
  context.textAlign = "right";

  // Gridlines and Y-axis values.
  for (let i = 0; i <= 4; i++) {
    const y = padding.top + chartHeight * i / 4;

    context.strokeStyle = "#293b43";
    context.lineWidth = 1;

    context.beginPath();
    context.moveTo(padding.left, y);
    context.lineTo(width - padding.right, y);
    context.stroke();

    context.fillStyle = "#a6b6c2";

    context.fillText(
      (maxY * (4 - i) / 4).toFixed(1),
      padding.left - 8,
      y + 3
    );
  }

  // X-axis labels adapt to mobile width.
  context.textAlign = "center";
  context.fillStyle = "#a6b6c2";

  const labelCount = width < 400 ? 4 : 6;
  const step = Math.max(
    1,
    Math.ceil(chartData.length / labelCount)
  );

  for (let i = 0; i < chartData.length; i += step) {
    const x = padding.left +
      chartWidth * i / Math.max(1, chartData.length - 1);

    const label = chartLabels[i] || String(i);

    context.fillText(
      label + (label.length === 2 ? ":00" : ""),
      x,
      height - 6
    );
  }

  const points = chartData.map((value, index) => ({
    x: padding.left +
      chartWidth * index / Math.max(1, chartData.length - 1),
    y: padding.top +
      chartHeight -
      value / maxY * chartHeight
  }));

  if (!points.length) return;

  // Filled chart area.
  context.beginPath();
  context.moveTo(points[0].x, points[0].y);

  points.slice(1).forEach((point) => {
    context.lineTo(point.x, point.y);
  });

  context.lineTo(
    points[points.length - 1].x,
    padding.top + chartHeight
  );

  context.lineTo(points[0].x, padding.top + chartHeight);
  context.closePath();

  const gradient = context.createLinearGradient(
    0,
    padding.top,
    0,
    height
  );

  gradient.addColorStop(0, "rgba(73,217,172,0.21)");
  gradient.addColorStop(1, "rgba(73,217,172,0)");

  context.fillStyle = gradient;
  context.fill();

  // Electric green chart line.
  context.beginPath();

  points.forEach((point, index) => {
    if (index === 0) {
      context.moveTo(point.x, point.y);
    } else {
      context.lineTo(point.x, point.y);
    }
  });

  context.strokeStyle = "#49d9ac";
  context.lineWidth = 2.7;
  context.lineJoin = "round";
  context.stroke();

  const lastPoint = points[points.length - 1];

  context.fillStyle = "#49d9ac";
  context.beginPath();
  context.arc(
    lastPoint.x,
    lastPoint.y,
    4,
    0,
    Math.PI * 2
  );
  context.fill();
}

// -------------------------
// 6. Appliance Studio
// -------------------------

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
  const tableRow = document.createElement("tr");

  tableRow.innerHTML = `
    <td>
      <input class="app-name" placeholder="Appliance"
             value="${safe(row.name)}" required>
    </td>
    <td>
      <input class="app-watts" type="number"
             min="0" step="any"
             value="${Number(row.watts)}" required>
    </td>
    <td>
      <input class="app-hours" type="number"
             min="0" max="24" step="any"
             value="${Number(row.hours)}" required>
    </td>
    <td>
      <input class="app-qty" type="number"
             min="1" max="100" step="1"
             value="${Number(row.quantity)}" required>
    </td>
    <td>
      <button class="delete-row" type="button"
              aria-label="Remove appliance">×</button>
    </td>
  `;

  tableRow.querySelector(".delete-row")
    .addEventListener("click", () => {
      if ($("appliance-rows").children.length <= 1) {
        toast("Keep at least one appliance.", true);
        return;
      }

      tableRow.remove();
    });

  $("appliance-rows").appendChild(tableRow);
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
    if ("message" in raw) return [String(raw.message)];

    if ("recommendation" in raw) {
      return [String(raw.recommendation)];
    }

    if ("Title" in raw && "Action" in raw) {
      return [
        `${raw.Title}: ${raw.Reason || ""} ${raw.Action}`
      ];
    }

    return Object.entries(raw).map(([key, value]) => {
      const content = typeof value === "object"
        ? JSON.stringify(value)
        : value;

      return `${key}: ${content}`;
    }).slice(0, 12);
  }

  return [];
}

function renderAdvice(target, values, emptyText) {
  const list = toAdviceList(values);

  target.innerHTML = (
    list.length ? list : [emptyText]
  ).map((value) => `
    <div class="insight">${safe(value)}</div>
  `).join("");
}

$("appliance-form").addEventListener("submit", (event) => {
  event.preventDefault();

  withLoading($("manual-submit"), async () => {
    const appliances = [
      ...$("appliance-rows").querySelectorAll("tr")
    ].map((row) => ({
      name: row.querySelector(".app-name").value.trim(),
      watts: Number(row.querySelector(".app-watts").value),
      hours: Number(row.querySelector(".app-hours").value),
      quantity: Number(row.querySelector(".app-qty").value)
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

    const daily = numeric(first(result, [
      "total_daily_energy_kwh",
      "daily_energy_kwh"
    ]));

    const cost = numeric(first(result, [
      "total_monthly_cost",
      "monthly_cost"
    ]));

    const savings = numeric(first(result, [
      "projected_savings",
      "potential_monthly_savings"
    ]));

    $("manual-placeholder").classList.add("hidden");
    $("manual-result").classList.remove("hidden");

    $("appliance-daily").textContent =
      daily === null ? "—" : number(daily) + " kWh";

    $("appliance-bill").textContent =
      cost === null ? "—" : money(cost);

    $("appliance-savings").textContent =
      savings === null ? "—" : money(savings);

    const breakdown = appliances.map((item) => ({
      name: item.name,
      energy: item.watts * item.hours * item.quantity / 1000
    }));

    const maximum = Math.max(
      0.001,
      ...breakdown.map((item) => item.energy)
    );

    $("appliance-bars").innerHTML = breakdown
      .sort((a, b) => b.energy - a.energy)
      .map((item) => `
        <div class="breakdown-row">
          <div class="breakdown-row-head">
            <span>${safe(item.name)}</span>
            <strong>${number(item.energy)} kWh/day</strong>
          </div>
          <div class="bar-track">
            <div class="bar-fill"
                 style="width:${(item.energy / maximum * 100).toFixed(1)}%">
            </div>
          </div>
        </div>
      `).join("");

    renderAdvice(
      $("appliance-recs"),
      first(result, [
        "recommendations",
        "action_plan",
        "analysis"
      ]),
      "Appliance analysis completed."
    );

    if (daily !== null) {
      $("metric-energy").textContent = number(daily);
      $("metric-cost").textContent = number(daily * tariff);

      $("metric-analysis").textContent = "Analyzed";
      $("metric-analysis-foot").textContent =
        appliances.length + " appliance types";

      $("overview-source").textContent =
        "Calculated from your appliance inputs";

      $("overview-badge").textContent = "YOUR INPUT";

      const energyCard = $("metric-energy")
        .closest(".metric-card");

      const costCard = $("metric-cost")
        .closest(".metric-card");

      if (energyCard) {
        energyCard.querySelector(".metric-foot").textContent =
          "Estimated from entered appliances";
      }

      if (costCard) {
        costCard.querySelector(".metric-foot").textContent =
          `At ₹${number(tariff)} per kWh`;
      }
    }

    toast("Appliance analysis completed.");
  });
});

// -------------------------
// 7. CSV Helpers
// -------------------------

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
setupUpload("patterns-file", "patterns-filename");

function collectNumbers(object, prefix = "", depth = 0) {
  if (!object || typeof object !== "object" || depth > 3) {
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

// -------------------------
// 8. ML Forecast
// -------------------------

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

    const selected = candidates[0] ||
      collectNumbers(result).find((item) =>
        /predict|forecast/i.test(item.key)
      );

    $("forecast-primary").textContent = selected
      ? number(selected.value, 3) +
        (/kwh|energy|consumption/i.test(selected.key)
          ? " kWh" : "")
      : "Prediction completed";

    $("forecast-primary-label").textContent = selected
      ? selected.key.replace(/_/g, " ")
      : "Review model response";

    $("forecast-json").textContent =
      JSON.stringify(result, null, 2);

    $("metric-analysis").textContent = "Forecasted";
    $("metric-analysis-foot").textContent =
      "ML prediction completed";

    toast("ML forecast completed.");
  });
});

// -------------------------
// 9. Anomaly Center
// -------------------------

$("anomaly-form").addEventListener("submit", (event) => {
  event.preventDefault();

  withLoading($("anomaly-submit"), async () => {
    const file = $("anomaly-file").files[0];

    if (!file) {
      throw new Error("Choose an energy CSV.");
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
          const classification = String(
            item.Anomaly_Type || ""
          );

          const isHigh = classification.includes("High");

          const expected = item.Expected_Energy_kWh == null
            ? "—"
            : number(item.Expected_Energy_kWh) + " kWh";

          return `
            <tr>
              <td>${number(item.Energy_kWh)} kWh</td>
              <td>${expected}</td>
              <td class="${isHigh ? "status-high" : "status-low"}">
                ${safe(classification)}
              </td>
            </tr>
          `;
        }).join("")
      : `
        <tr>
          <td colspan="3">No anomalies were flagged.</td>
        </tr>
      `;

    $("anomaly-info").textContent =
      "Statistical flags are not confirmed faults.";

    const readings = (result.recent_readings || [])
      .filter((item) =>
        Number.isFinite(Number(item.Energy_kWh))
      )
      .slice(-24);

    if (readings.length > 1) {
      chartData = readings.map(
        (item) => Number(item.Energy_kWh)
      );

      chartLabels = readings.map(
        (_, index) => String(index + 1)
      );

      $("overview-chart-sub").textContent =
        "Latest readings from uploaded CSV";

      $("overview-source").textContent =
        "Anomaly scan completed using uploaded readings";

      $("overview-badge").textContent = "YOUR DATA";
    }

    toast(
      `Anomaly scan complete: ${result.anomaly_count} flags.`
    );
  });
});

// -------------------------
// 10. Weather Advisor
// -------------------------

function weatherInsights(result) {
  const values = [
    first(result, [
      "alerts",
      "recommendations",
      "advice",
      "energy_advice",
      "suggestions"
    ], [])
  ];

  return values.flatMap(toAdviceList);
}

$("weather-form").addEventListener("submit", (event) => {
  event.preventDefault();

  withLoading($("weather-submit"), async () => {
    const appliances = [
      ...document.querySelectorAll(
        ".check-cards input:checked"
      )
    ].map((item) => item.value);

    const payload = {
      city: $("weather-city").value.trim(),
      appliances,
      tariff: Number($("weather-tariff").value)
    };

    if (!payload.city) {
      throw new Error("Please enter a city name.");
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

    $("weather-location").textContent = [
      first(result, ["city", "location", "name"], payload.city),
      first(result, ["country"], "")
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

    const daytime = first(result, [
      "is_day",
      "is_daytime",
      "daytime"
    ], null);

    $("weather-condition").textContent =
      daytime === null
        ? "Current conditions"
        : daytime ? "Daytime" : "Nighttime";

    const icon = document.querySelector(
      ".weather-big-icon"
    );

    if (icon) {
      icon.textContent =
        daytime === false || daytime === 0
          ? "☾" : "☀";
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
    ].filter(([, value]) =>
      value !== null && value !== undefined
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
      "No appliance-specific advice available."
    );

    $("weather-json").textContent =
      JSON.stringify(result, null, 2);

    toast("Weather analysis completed.");
  });
});

// -------------------------
// 11. What-If Simulator
// -------------------------

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

  const savedEnergy =
    watts * reduction * quantity / 1000 * 30;

  const after = Math.max(
    0,
    before - savedEnergy * tariff
  );

  $("sim-savings").textContent =
    money(before - after);

  $("sim-energy").textContent =
    number(savedEnergy) + " kWh saved per month";

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

// -------------------------
// 12. Energy Copilot
// -------------------------

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

    appliances: [{
      name: $("agent-name").value.trim(),
      watts: Number($("agent-watts").value),
      hours: Number($("agent-hours").value),
      quantity: Number($("agent-qty").value)
    }]
  };
}

function validateCopilot(payload) {
  const appliance = payload.appliances[0];

  if (payload.question.length < 3) {
    throw new Error(
      "Enter a question with at least 3 characters."
    );
  }

  if (!appliance.name) {
    throw new Error("Enter an appliance name.");
  }

  if (
    !Number.isFinite(appliance.watts) ||
    appliance.watts < 0
  ) {
    throw new Error("Power cannot be negative.");
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
    throw new Error("Tariff must be 0 or greater.");
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

    if (revision !== copilotRevision) {
      return;
    }

    const result = output.result || {};

    $("agent-placeholder").classList.add("hidden");
    $("agent-result").classList.remove("hidden");

    $("agent-answer").textContent =
      result.answer || "No response generated.";

    const preview = document.querySelector(
      ".agent-question-preview"
    );

    if (preview) {
      preview.textContent = payload.question;
    }

    $("agent-tools").innerHTML = (
      result.tools_used || []
    ).map((tool) => `
      <span class="agent-pill">
        ${safe(String(tool).replaceAll("_", " "))}
      </span>
    `).join("") || `
      <span class="muted">No tools needed</span>
    `;

    $("agent-actions").innerHTML = (
      result.actions || []
    ).map((action) => `
      <div class="agent-action">
        <strong>${safe(action.appliance)}</strong>
        <span>
          Reduce ${number(action.reduction_hours_per_day, 1)}
          h/day →
          ${money(action.monthly_inr_saved)}/month
          (estimate)
        </span>
      </div>
    `).join("") || `
      <p class="muted small">
        Ask for savings suggestions to create scenarios.
      </p>
    `;

    $("agent-assumptions").textContent =
      result.assumptions || "";

    copilotHasRun = true;

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
      button.textContent = "Run Decision Agent ↗";
    }
  }
}

$("copilot-form").addEventListener("submit", (event) => {
  event.preventDefault();

  updateCopilot(true).catch((error) => {
    console.error(error);
    toast(error.message || String(error), true);
  });
});

// After first successful run, update when values change.
copilotFields.forEach((id) => {
  $(id).addEventListener("input", () => {
    ++copilotRevision;
    clearTimeout(copilotTimer);

    if (!copilotHasRun) {
      return;
    }

    $("agent-result").classList.add("hidden");
    $("agent-placeholder").classList.remove("hidden");

    $("agent-submit").disabled = false;
    $("agent-submit").textContent = "Run Decision Agent ↗";

    copilotTimer = setTimeout(() => {
      updateCopilot().catch((error) => {
        console.error(error);
        toast(error.message || String(error), true);
      });
    }, 500);
  });
});

// -------------------------
// 13. ML Pattern Lab
// -------------------------

$("patterns-form").addEventListener("submit", (event) => {
  event.preventDefault();

  withLoading($("patterns-submit"), async () => {
    const file = $("patterns-file").files[0];

    if (!file) {
      throw new Error("Select an energy CSV file.");
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
      <span class="agent-pill">${safe(feature)}</span>
    `).join("");

    $("patterns-list").innerHTML = (
      result.highest_outlier_examples || []
    ).map((item, index) => `
      <div class="agent-action">
        <strong>Outlier ${index + 1}</strong>
        <span>
          ${number(item.Energy_kWh, 3)} kWh ·
          Score ${number(item.anomaly_score, 4)}
        </span>
      </div>
    `).join("") || `
      <p class="muted small">No outlier examples.</p>
    `;

    $("patterns-notes").textContent =
      result.limitations || "";

    toast("ML Pattern Lab analysis completed.");
  });
});

// -------------------------
// 14. Gentle 3D Card Effect
// -------------------------

function initializeCardAnimations() {
  const reduceMotion = window.matchMedia(
    "(prefers-reduced-motion: reduce)"
  );

  const desktopPointer = window.matchMedia(
    "(hover: hover) and (pointer: fine)"
  );

  if (reduceMotion.matches || !desktopPointer.matches) {
    return;
  }

  document.querySelectorAll(".metric-card").forEach((card) => {
    card.addEventListener("pointermove", (event) => {
      const bounds = card.getBoundingClientRect();

      const x = (
        (event.clientX - bounds.left) / bounds.width
      ) - 0.5;

      const y = (
        (event.clientY - bounds.top) / bounds.height
      ) - 0.5;

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

// -------------------------
// 15. Application Startup
// -------------------------

const initialView = location.hash.substring(1);

navigate(
  $("view-" + initialView)
    ? initialView
    : "overview"
);

requestAnimationFrame(drawChart);

updateHealth();
