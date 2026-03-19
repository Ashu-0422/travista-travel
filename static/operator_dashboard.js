(function () {
  const dashboardRoot = document.querySelector(".dashboard-overview");
  const modelScript = document.getElementById("dashboardModel");
  if (!dashboardRoot || !modelScript) {
    return;
  }

  let dashboardModel = {};
  try {
    dashboardModel = JSON.parse(modelScript.textContent || "{}");
  } catch (error) {
    return;
  }

  const tripsEl = document.getElementById("metricTrips");
  const bookingsEl = document.getElementById("metricBookings");
  const travelersEl = document.getElementById("metricTravelers");
  const revenueEl = document.getElementById("metricRevenue");
  const tripSlicerEl = document.getElementById("tripSlicer");
  const revenueViewEl = document.getElementById("revenueView");
  const topCustomerNameEl = document.getElementById("topCustomerName");
  const topCustomerMetaEl = document.getElementById("topCustomerMeta");
  const topCustomerRevenueEl = document.getElementById("topCustomerRevenue");
  const avgTravelersEl = document.getElementById("avgTravelers");
  const repeatCustomersEl = document.getElementById("repeatCustomers");
  const singleCustomersEl = document.getElementById("singleCustomers");
  const topCustomersTableEl = document.getElementById("topCustomersTable");
  const revenueChartTitleEl = document.getElementById("revenueChartTitle");
  const statusEl = document.getElementById("dashboardStatus");

  const overviewCtx = document.getElementById("overviewChart");
  const revenueCtx = document.getElementById("revenueChart");
  const tripRevenueCtx = document.getElementById("tripRevenueChart");
  const paymentModeCtx = document.getElementById("paymentModeChart");

  const formatNumber = (value) => new Intl.NumberFormat("en-IN").format(Number(value || 0));
  const formatCurrency = (value) =>
    "Rs. " +
    new Intl.NumberFormat("en-IN", {
      maximumFractionDigits: 2,
      minimumFractionDigits: 0,
    }).format(Number(value || 0));

  const escapeHtml = (value) =>
    String(value || "").replace(/[&<>"']/g, (char) => {
      const map = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
      return map[char];
    });

  const overviewChart = new Chart(overviewCtx, {
    type: "bar",
    data: {
      labels: ["Trips", "Bookings", "Travellers", "Revenue"],
      datasets: [
        {
          label: "Selected view",
          data: [0, 0, 0, 0],
          backgroundColor: ["#1f6a5b", "#d67c4a", "#93b7ab", "#3d5a50"],
          borderRadius: 12,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
        },
      },
      plugins: {
        legend: {
          display: false,
        },
        tooltip: {
          callbacks: {
            label(context) {
              if (context.dataIndex === 3) {
                return formatCurrency(context.raw);
              }
              return formatNumber(context.raw);
            },
          },
        },
      },
    },
  });

  const revenueChart = new Chart(revenueCtx, {
    type: "bar",
    data: {
      labels: [],
      datasets: [
        {
          label: "Revenue",
          data: [],
          backgroundColor: "rgba(214, 124, 74, 0.72)",
          borderRadius: 10,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            callback(value) {
              return formatCurrency(value);
            },
          },
        },
      },
      plugins: {
        legend: {
          display: false,
        },
      },
    },
  });

  const tripRevenueChart = new Chart(tripRevenueCtx, {
    type: "bar",
    data: {
      labels: [],
      datasets: [
        {
          label: "Revenue by trip",
          data: [],
          backgroundColor: ["#1f6a5b", "#d67c4a", "#93b7ab", "#3d5a50", "#ddc5a2", "#58756b"],
          borderRadius: 10,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            callback(value) {
              return formatCurrency(value);
            },
          },
        },
      },
      plugins: {
        legend: {
          display: false,
        },
      },
    },
  });

  const paymentModeChart = new Chart(paymentModeCtx, {
    type: "doughnut",
    data: {
      labels: [],
      datasets: [
        {
          data: [],
          backgroundColor: ["#1f6a5b", "#d67c4a", "#93b7ab", "#ddc5a2", "#58756b"],
          borderWidth: 0,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
    },
  });

  const renderTopCustomersTable = (customers) => {
    if (!Array.isArray(customers) || customers.length === 0) {
      topCustomersTableEl.innerHTML = '<tr><td colspan="4">No customer booking data yet.</td></tr>';
      return;
    }

    topCustomersTableEl.innerHTML = customers
      .map(
        (customer) => `
          <tr>
            <td>${escapeHtml(customer.name || customer.username || "Unknown")}<br><small>${escapeHtml(
              customer.email || ""
            )}</small></td>
            <td>${formatNumber(customer.bookings)}</td>
            <td>${formatNumber(customer.travelers)}</td>
            <td>${formatCurrency(customer.revenue)}</td>
          </tr>
        `
      )
      .join("");
  };

  const refreshTripOptions = () => {
    const tripOptions = Array.isArray(dashboardModel.trip_options) ? dashboardModel.trip_options : [];
    const currentValue = tripSlicerEl.value || "all";
    tripSlicerEl.innerHTML = '<option value="all">All Trips</option>';

    tripOptions.forEach((trip) => {
      const option = document.createElement("option");
      option.value = String(trip.id);
      option.textContent = trip.name || `Trip ${trip.id}`;
      tripSlicerEl.appendChild(option);
    });

    const canRestore = Array.from(tripSlicerEl.options).some((option) => option.value === currentValue);
    tripSlicerEl.value = canRestore ? currentValue : "all";
  };

  const updateDashboard = () => {
    const selectionKey = tripSlicerEl.value || "all";
    const revenueView = revenueViewEl.value || "weekly";
    const overviewBySelection = dashboardModel.overview_by_selection || {};
    const selectedTrip = overviewBySelection[selectionKey] || overviewBySelection.all || {};
    const customerBehavior = dashboardModel.customer_behavior || {};
    const revenueBreakdown = dashboardModel.revenue_breakdown || {};
    const selectedRevenueSeries = Array.isArray(revenueBreakdown[revenueView]) ? revenueBreakdown[revenueView] : [];
    const topCustomer = selectedTrip.top_customer || {};

    tripsEl.textContent = formatNumber(selectedTrip.trips || 0);
    bookingsEl.textContent = formatNumber(selectedTrip.bookings || 0);
    travelersEl.textContent = formatNumber(selectedTrip.travelers || 0);
    revenueEl.textContent = formatCurrency(selectedTrip.revenue || 0);

    topCustomerNameEl.textContent = topCustomer.name || "No bookings yet";
    topCustomerMetaEl.textContent =
      topCustomer.travelers && topCustomer.bookings
        ? `${formatNumber(topCustomer.travelers)} travellers across ${formatNumber(topCustomer.bookings)} bookings`
        : "Waiting for bookings";
    topCustomerRevenueEl.textContent = `Revenue contribution: ${formatCurrency(topCustomer.revenue || 0)}`;

    avgTravelersEl.textContent = String(customerBehavior.avg_travelers_per_booking || 0);
    repeatCustomersEl.textContent = formatNumber(customerBehavior.repeat_customers || 0);
    singleCustomersEl.textContent = `Single-booking customers: ${formatNumber(
      customerBehavior.single_booking_customers || 0
    )}`;

    overviewChart.data.datasets[0].data = [
      Number(selectedTrip.trips || 0),
      Number(selectedTrip.bookings || 0),
      Number(selectedTrip.travelers || 0),
      Number(selectedTrip.revenue || 0),
    ];
    overviewChart.update();

    revenueChartTitleEl.textContent = revenueView === "monthly" ? "Monthly Revenue" : "Weekly Revenue";
    revenueChart.data.labels = selectedRevenueSeries.map((item) => item.label || "");
    revenueChart.data.datasets[0].data = selectedRevenueSeries.map((item) => Number(item.value || 0));
    revenueChart.update();

    const tripRevenueChartModel = dashboardModel.trip_revenue_chart || {};
    tripRevenueChart.data.labels = tripRevenueChartModel.labels || [];
    tripRevenueChart.data.datasets[0].data = tripRevenueChartModel.values || [];
    tripRevenueChart.update();

    const paymentModeChartModel = dashboardModel.payment_mode_chart || {};
    paymentModeChart.data.labels = paymentModeChartModel.labels || [];
    paymentModeChart.data.datasets[0].data = paymentModeChartModel.values || [];
    paymentModeChart.update();

    renderTopCustomersTable(customerBehavior.top_customers || []);
    statusEl.textContent = "Dashboard loaded from Python analytics model.";
  };

  refreshTripOptions();
  tripSlicerEl.addEventListener("change", updateDashboard);
  revenueViewEl.addEventListener("change", updateDashboard);
  updateDashboard();
})();
