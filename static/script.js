let luxGauge, pwmGauge;

function updateUI(isConnected) {
  const statusBadge = document.getElementById("connection-status");
  const openBtn = document.getElementById("openBtn");
  const closeBtn = document.getElementById("closeBtn");
  const startBtn = document.getElementById("startBtn");

  if (isConnected) {
    statusBadge.innerText = "STAV: PRIPOJENÉ";
    statusBadge.classList.replace("bg-danger", "bg-success");
    openBtn.disabled = true;
    closeBtn.disabled = false;
    startBtn.disabled = false; // Odomkneme Štart
  } else {
    statusBadge.innerText = "STAV: ODPOJENÉ";
    statusBadge.classList.replace("bg-success", "bg-danger");
    openBtn.disabled = false;
    closeBtn.disabled = true;
    startBtn.disabled = true;
    document.getElementById("stopBtn").disabled = true;
  }
}

function openConnection() {
  fetch("/open_connection", { method: "POST" })
    .then((response) => response.json())
    .then((data) => {
      if (data.status === "connected" || data.status === "already_connected") {
        updateUI(true);
      } else {
        alert("Chyba: " + data.msg);
      }
    });
}

window.onload = function () {
  fetch("/get_status")
    .then((response) => response.json())
    .then((data) => {
      if (data.connected) {
        updateUI(true);
        // Ak náhodou bežal aj monitoring, upravíme tlačidlá Štart/Stop
        if (data.monitoring) {
          isRunning = true;
          document.getElementById("startBtn").disabled = true;
          document.getElementById("stopBtn").disabled = false;
        }
      } else {
        updateUI(false);
      }
    });
};

function closeConnection() {
  fetch("/close_connection", { method: "POST" })
    .then((response) => response.json())
    .then((data) => {
      location.reload(); // Najjednoduchší spôsob ako resetovať web do východiskového stavu
    });
}
// Funkcia na odoslanie nového Setpointu
function poslatUdaje() {
  const val = document.getElementById("intenzita").value;
  let formData = new FormData();
  formData.append("intenzita", val);
  fetch("/set_led", { method: "POST", body: formData });
}

let isRunning = false;

function startMonitoring() {
  fetch("/start_monitoring", { method: "POST" }).then(() => {
    isRunning = true;
    document.getElementById("startBtn").disabled = true;
    document.getElementById("stopBtn").disabled = false;
  });
}

function stopMonitoring() {
  fetch("/stop_monitoring", { method: "POST" }).then(() => {
    isRunning = false;
    document.getElementById("startBtn").disabled = false;
    document.getElementById("stopBtn").disabled = true;
  });
}

let graphData = {
  time: [],
  setpoint: [],
  input: [],
  output: [],
};

// Prepínanie pohľadov
function showView(view) {
  const dash = document.getElementById("view-dashboard");
  const graph = document.getElementById("view-graph");
  const gauges = document.getElementById("view-gauges");

  // Tlačidlá
  const btnDash = document.getElementById("btn-dash");
  const btnGraph = document.getElementById("btn-graph");
  const btnGauges = document.getElementById("btn-gauges");

  // Skryť všetko
  dash.classList.add("d-none");
  graph.classList.add("d-none");
  gauges.classList.add("d-none");
  btnDash.classList.remove("active");
  btnGraph.classList.remove("active");
  btnGauges.classList.remove("active");

  // Zobraziť vybrané
  if (view === "dashboard") {
    dash.classList.remove("d-none");
    btnDash.classList.add("active");
  } else if (view === "graph") {
    graph.classList.remove("d-none");
    btnGraph.classList.add("active");
    Plotly.Plots.resize("plot-lux");
    Plotly.Plots.resize("plot-pwm");
  } else if (view === "gauges") {
    gauges.classList.remove("d-none");
    btnGauges.classList.add("active");
  }
}

// Inicializácia Plotly grafu
function initPlots() {
  // 1. Graf pre LUX (Setpoint a Input)
  const tracesLux = [
    {
      x: [],
      y: [],
      name: "Žiadaná (Setpoint)",
      line: { color: "#ff7f0e", width: 3 },
    },
    {
      x: [],
      y: [],
      name: "Aktuálna (Input)",
      line: { color: "#1f77b4" },
    },
  ];
  const layoutLux = {
    title: "Regulácia intenzity (Lux)",
    xaxis: { title: "Čas" },
    yaxis: { title: "Luxy (lx)" },
    margin: { t: 50, b: 50, l: 60, r: 30 },
  };

  // 2. Graf pre PWM (Output)
  const tracesPwm = [
    {
      x: [],
      y: [],
      name: "Výkon (PWM)",
      fill: "tozeroy",
      line: { color: "#2ca02c" },
    },
  ];
  const layoutPwm = {
    title: "Akčný zásah (PWM)",
    xaxis: { title: "Čas" },
    yaxis: { title: "PWM (0-255)" },
    margin: { t: 50, b: 50, l: 60, r: 30 },
  };

  Plotly.newPlot("plot-lux", tracesLux, layoutLux);
  Plotly.newPlot("plot-pwm", tracesPwm, layoutPwm);
}

// Nezabudni zavolať novú funkciu pri načítaní
initPlots();

function initGauges() {
  luxGauge = new RadialGauge({
    renderTo: "gauge-lux",
    width: 300,
    height: 300,
    units: "Lux (lx)",
    minValue: 0,
    maxValue: 1650, // Nastavené na 1650
    majorTicks: ["0", "250", "500", "750", "1000", "1250", "1500", "1650"],
    minorTicks: 5,
    highlights: [{ from: 1400, to: 1650, color: "rgba(200, 50, 50, .75)" }],
    colorPlate: "#fff",
    borderShadowWidth: 0,
    borders: false,
    needleType: "arrow",
    needleWidth: 2,
    needleCircleSize: 7,
    needleCircleOuter: true,
    needleCircleInner: false,
    animationDuration: 500,
    animationRule: "linear",
    valueBox: true, // Zobrazí aj digitálnu hodnotu pod ručičkou
    fontValueSize: 30,
  }).draw();

  pwmGauge = new RadialGauge({
    renderTo: "gauge-pwm",
    width: 300,
    height: 300,
    units: "PWM (0-255)",
    minValue: 0,
    maxValue: 255,
    majorTicks: ["0", "50", "100", "150", "200", "255"],
    minorTicks: 5,
    highlights: [{ from: 200, to: 255, color: "rgba(200, 50, 50, .75)" }],
    colorPlate: "#fff",
    borders: false,
    needleType: "arrow",
    animationDuration: 500,
    valueBox: true,
    fontValueSize: 30,
  }).draw();
}

// Zavolaj ju na konci script.js
initGauges();

setInterval(() => {
  fetch("/get_data")
    .then((response) => response.json())
    .then((data) => {
      // Aktualizácia veľkých čísel v kartách
      document.getElementById("val-setpoint").innerText = data.setpoint;
      document.getElementById("val-input").innerText = data.input;
      document.getElementById("val-output").innerText = data.output;

      // PRIDÁVANIE DO ZOZNAMU (iba ak beží monitoring)
      if (isRunning && data.setpoint !== "---") {
        const tableBody = document.getElementById("log-table-body");
        const now = new Date().toLocaleTimeString(); // Aktuálny čas

        // Vytvoríme nový riadok
        const newRow = `<tr>
                        <td>${now}</td>
                        <td>${data.setpoint}</td>
                        <td>${data.input}</td>
                        <td>${data.output}</td>
                    </tr>`;

        // Pridáme riadok na ZAČIATOK tabuľky (nové hore)
        tableBody.insertAdjacentHTML("afterbegin", newRow);

        // Voliteľné: Ak je riadkov priveľa (napr. 50), najstarší vymažeme
        if (tableBody.rows.length > 50) {
          tableBody.deleteRow(tableBody.rows.length - 1);
        }
      }

      if (isRunning && data.setpoint !== "---") {
        const now = new Date().toLocaleTimeString();

        // Aktualizácia prvého grafu (Luxy - 2 čiary)
        Plotly.extendTraces(
          "plot-lux",
          {
            x: [[now], [now]],
            y: [[data.setpoint], [data.input]],
          },
          [0, 1],
        );

        // Aktualizácia druhého grafu (PWM - 1 čiara)
        Plotly.extendTraces(
          "plot-pwm",
          {
            x: [[now]],
            y: [[data.output]],
          },
          [0],
        );
      }

      if (isRunning && data.input !== "---") {
        luxGauge.value = data.input;
        pwmGauge.value = data.output;
      } else {
        luxGauge.value = 0;
        pwmGauge.value = 0;
      }
    });
}, 1000);
