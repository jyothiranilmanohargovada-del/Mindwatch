/**
 * MindWatch 2.0 — Interactive Timeline Visualization with Chart.js
 */
document.addEventListener("DOMContentLoaded", function () {
  const lineCtx = document.getElementById("timelineChart");
  if (lineCtx && window.Chart && window.TIMELINE_DATA) {
    const data = window.TIMELINE_DATA;
    const labels = data.map(d => d.period || d.week || d.date || d.month);
    const scores = data.map(d => d.mean_risk);

    const moderateThreshold = window.THRESH_MODERATE || 0.40;
    const highThreshold = window.THRESH_HIGH || 0.65;

    new Chart(lineCtx, {
      type: "line",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Emotional Distress Indicator",
            data: scores,
            borderColor: "#4f46e5",
            backgroundColor: "rgba(79, 70, 229, 0.08)",
            borderWidth: 2.5,
            fill: true,
            tension: 0.3,
            pointBackgroundColor: "#4f46e5",
            pointRadius: 4,
            pointHoverRadius: 6
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: function (ctx) {
                return ` Distress Marker Score: ${ctx.parsed.y} / 1.0`;
              }
            }
          }
        },
        scales: {
          y: {
            min: 0,
            max: 1.0,
            grid: { color: "rgba(100, 116, 139, 0.12)" },
            ticks: {
              callback: function (val) {
                return (val * 100) + "%";
              }
            }
          },
          x: {
            grid: { display: false }
          }
        }
      }
    });
  }

  // Recurring Themes Chart
  const themesCtx = document.getElementById("themesChart");
  if (themesCtx && window.Chart && window.THEMES_DATA) {
    const themes = window.THEMES_DATA;
    const keys = Object.keys(themes);
    const values = Object.values(themes);

    if (keys.length > 0) {
      new Chart(themesCtx, {
        type: "bar",
        data: {
          labels: keys,
          datasets: [
            {
              label: "Frequency",
              data: values,
              backgroundColor: "#6366f1",
              borderRadius: 6
            }
          ]
        },
        options: {
          indexAxis: "y",
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            x: { beginAtZero: true, grid: { color: "rgba(100, 116, 139, 0.12)" }, ticks: { stepSize: 1 } },
            y: { grid: { display: false } }
          }
        }
      });
    }
  }

  // Signal Frequency Doughnut Chart
  const signalsCtx = document.getElementById("signalsChart");
  if (signalsCtx && window.Chart && window.SIGNALS_DATA) {
    const signals = window.SIGNALS_DATA;
    new Chart(signalsCtx, {
      type: "doughnut",
      data: {
        labels: ["Low Risk", "Moderate Risk", "High Risk", "Crisis Language"],
        datasets: [
          {
            data: [
              signals.LOW || 0,
              signals.MODERATE || 0,
              signals.HIGH || 0,
              signals.CRISIS || 0
            ],
            backgroundColor: ["#10b981", "#f59e0b", "#ef4444", "#7f1d1d"],
            borderWidth: 0
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: "bottom", labels: { boxWidth: 12, padding: 12 } }
        },
        cutout: "65%"
      }
    });
  }
});
