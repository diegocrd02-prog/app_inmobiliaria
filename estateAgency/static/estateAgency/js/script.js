function predict() {
  const type = document.getElementById("type").value;
  const city = document.getElementById("city").value;
  const result = document.getElementById("result");
  redirectUrl = `/properties/?type=${type}&city=${city}`;
  window.location.href = redirectUrl;
}

function renderChart(labels, data, label) {
  new Chart(document.getElementById("grafico"), {
    type: "bar",
    data: {
      labels: labels,
      datasets: [{
        label: label,
        data: data
      }]
    }
  });
}

function renderPropertyCharts(chartData, selectedType) {
  const priceCanvas = document.getElementById("grafico");
  const priceM2Canvas = document.getElementById("graficoM2");
  const priceTitle = document.getElementById("priceChartTitle");

  if (!priceCanvas || !priceM2Canvas || typeof Chart === "undefined") {
    return;
  }

  let chartType = "bar";
  let chartTitle = "Precio de compra por vivienda";

  if (selectedType === "rent_long") {
    chartType = "line";
    chartTitle = "Alquiler mensual por vivienda";
  }

  if (selectedType === "rent_short") {
    chartType = "doughnut";
    chartTitle = "Alquiler de temporada por vivienda";
  }

  if (priceTitle) {
    priceTitle.textContent = chartTitle;
  }

  new Chart(priceCanvas, {
    type: chartType,
    data: {
      labels: chartData.labels,
      datasets: [{
        label: chartTitle,
        data: chartData.prices,
        backgroundColor: [
          "#1f6feb",
          "#0f9f8f",
          "#d85b42",
          "#d6a73b",
          "#7557b8",
          "#344054",
        ],
        borderColor: "#1f6feb",
        borderWidth: 2,
        tension: 0.3,
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          display: true,
        }
      }
    }
  });

  new Chart(priceM2Canvas, {
    type: "bar",
    data: {
      labels: chartData.labels,
      datasets: [{
        label: "Precio por metro cuadrado",
        data: chartData.prices_m2,
        backgroundColor: "#0f9f8f",
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          display: true,
        }
      }
    }
  });
}

function renderPropertyDetailChart(chartData, selectedType) {
  const detailCanvas = document.getElementById("propertyDetailChart");
  const detailTitle = document.getElementById("detailChartTitle");

  if (!detailCanvas || typeof Chart === "undefined") {
    return;
  }

  const labels = chartData.labels && chartData.labels.length ? chartData.labels : ["Actual"];
  const prices = chartData.prices && chartData.prices.length ? chartData.prices : [0];
  const pricesM2 = chartData.prices_m2 && chartData.prices_m2.length ? chartData.prices_m2 : [0];

  let chartType = "line";
  let title = "Evolucion del precio de venta";
  let color = "#c45a2d";

  if (selectedType === "rent_long") {
    chartType = "bar";
    title = "Variacion del alquiler mensual";
    color = "#9b6b32";
  }

  if (selectedType === "rent_short") {
    chartType = "line";
    title = "Evolucion del alquiler de temporada";
    color = "#b23b2f";
  }

  if (detailTitle) {
    detailTitle.textContent = title;
  }

  new Chart(detailCanvas, {
    type: chartType,
    data: {
      labels: labels,
      datasets: [
        {
          label: "Precio",
          data: prices,
          borderColor: color,
          backgroundColor: "rgba(196, 90, 45, 0.18)",
          borderWidth: 3,
          tension: 0.35,
          fill: selectedType !== "rent_long",
        },
        {
          label: "Precio por m2",
          data: pricesM2,
          borderColor: "#2f6f5e",
          backgroundColor: "rgba(47, 111, 94, 0.14)",
          borderWidth: 2,
          tension: 0.35,
          yAxisID: "y1",
        }
      ]
    },
    options: {
      responsive: true,
      interaction: {
        mode: "index",
        intersect: false,
      },
      scales: {
        y: {
          beginAtZero: false,
          title: {
            display: true,
            text: "Precio"
          }
        },
        y1: {
          beginAtZero: false,
          position: "right",
          grid: {
            drawOnChartArea: false,
          },
          title: {
            display: true,
            text: "EUR/m2"
          }
        }
      }
    }
  });
}

function renderPageCharts() {
  if (window.chartData && window.selectedType) {
    renderPropertyCharts(window.chartData, window.selectedType);
  }

  if (window.detailChartData && window.detailSelectedType) {
    renderPropertyDetailChart(window.detailChartData, window.detailSelectedType);
  }
}
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", renderPageCharts);
} else {
  renderPageCharts();
}

let scrapingPopupManuallyClosed = false;
let scrapingStatusInterval = null;

const popup = document.getElementById("scraping-popup");
const closeBtn = document.getElementById("scraping-popup-close");
let isDatabaseEmpty = document.getElementById("isPropertyDatabaseEmpty").value === "true";
const emptyDatabasePopup = document.getElementById("empty-scraping-popup");

function showScrapingPopup() {
  if (!scrapingPopupManuallyClosed) {
    popup.classList.remove("hidden");
  }
}

function hideScrapingPopup() {
  popup.classList.add("hidden");
}

closeBtn.addEventListener("click", (e) => {
  e.preventDefault();
  e.stopPropagation();

  scrapingPopupManuallyClosed = true;
  hideScrapingPopup();
});

async function checkScrapingStatus() {
  try {
    const response = await fetch("/scraping/status/");
    const data = await response.json();

    if (data.running) {
      if (isDatabaseEmpty) {
        emptyDatabasePopup.style.display = "flex";
      } else { 
        showScrapingPopup();
      }
    } else {
      emptyDatabasePopup.style.display = "none";
      if (scrapingStatusInterval) {
        clearInterval(scrapingStatusInterval);
        scrapingStatusInterval = null;
      }
      scrapingPopupManuallyClosed = false;
      hideScrapingPopup();
    }
  } catch (e) {
    console.error("Error checking scraping status", e);
  }
}

interact("#scraping-popup").draggable({
  allowFrom: ".scraping-popup-header",
  ignoreFrom: "#scraping-popup-close",
  listeners: {
    move(event) {
      const target = event.target;

      const left = parseFloat(target.style.left || target.offsetLeft);
      const top = parseFloat(target.style.top || target.offsetTop);

      target.style.left = `${left + event.dx}px`;
      target.style.top = `${top + event.dy}px`;
      target.style.right = "auto";
      target.style.bottom = "auto";
    }
  }
});

checkScrapingStatus();
scrapingStatusInterval = setInterval(checkScrapingStatus, 10000);