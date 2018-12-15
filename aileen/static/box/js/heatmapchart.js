function heatmapChart(options) {
const chartContainerId = options.chartContainerId;
const data = options.data;
const minDate = options.minDate;
const maxDate = options.maxDate;
const initMonth = moment.utc(options.initMonth, "YYYY-MM").isValid()
  ? moment.utc(options.initMonth, "YYYY-MM")
  : data[0].time.clone().startOf("month");
const containerWidth =
  options.width ||
  document.getElementById(chartContainerId).clientWidth ||
  window.innerWidth;
const containerHeight =
  options.height ||
  document.getElementById(chartContainerId).clientHeight ||
  window.innerHeight;

////////////////////////////////////////////////////////////
//// Initial Setup /////////////////////////////////////////
////////////////////////////////////////////////////////////
const chart = {};

// State
let selectedMonth;
let freezedDay;

// Dimension
const controlHeight = 60;
const margin = { top: 5, right: 25, bottom: 5, left: 10 };
const width = containerWidth - margin.left - margin.right;
const height = containerHeight - controlHeight - margin.top - margin.bottom;
const xAxisHeight = 28; // Top
const yAxisWidth = 40; // Left
const legendWidth = 40; // Right
const legendAdditionHeight = 16; // Bottom
const cellSize = Math.min(
  (width - yAxisWidth - legendWidth) / 31,
  (height - xAxisHeight - legendAdditionHeight) / 24
);
const heatmapWidth = cellSize * 31;
const heatmapHeight = cellSize * 24;
const visibleWidth = yAxisWidth + heatmapWidth + legendWidth;
const visibleHeight = xAxisHeight + heatmapHeight + legendAdditionHeight;

// Style
const colors = ["#D8D860", "#D8D860", "#A6CCCD", "#207E82", "#1D5464"];
const colorStops = [0.0, 0.05, 0.45, 0.75, 1.0];
const colorInterpolator = d3.interpolateHcl;
const max_times_seen = Math.max.apply(Math, data.map(function(o) { return o.devices}));
const colorScaleMaxDevices = Math.max(max_times_seen*0.8, 100);
const cellStrokeColor = "#fff";
const maxCellStrokeColor = "#FF0000";
const maxCellStrokeWidth = 2;
const focusRectStrokeColor = "#000";
const focusFreezedRectStrokeColor = "#000";
const legendStripSize = 10;

const locale = d3.formatLocale({
  decimal: ".",
  thousands: " ",
  grouping: [3],
  currency: ["€", ""]
});

// Container
const chartContainer = d3
  .select(`#${chartContainerId}`)
  .classed("heatmap-chart", true);
const tooltip = d3.select(".chart-tooltip");
const controlContainer = chartContainer.append("div").attr("class", "row");
const heatmapContainer = chartContainer
  .append("div")
  .attr("class", "heatmap row");
const svg = heatmapContainer
  .append("svg")
  .attr("width", containerWidth)
  .attr("height", containerHeight - controlHeight);
const g = svg
  .append("g")
  .attr(
    "transform",
    `translate(${margin.left +
      width / 2 -
      visibleWidth / 2 +
      yAxisWidth},${margin.top +
      height / 2 -
      visibleHeight / 2 +
      xAxisHeight})`
  );

////////////////////////////////////////////////////////////
//// Control ///////////////////////////////////////////////
////////////////////////////////////////////////////////////
controlContainer.html(`
  <div class="w-100 d-flex justify-content-between align-items-end">
    <div class="form-group monthly-activity-label">
      Monthly Activity
    </div>

    <div class="form-group month-select">
      <!-- <label>Select Month</label> -->
      <div class="input-group">
        <div class="input-group-prepend">
          <span class="input-group-text"><i class="fa fa-calendar"></i></span>
        </div>
        <input type="text" class="form-control form-control-sm" id="heatmapDatePicker">
      </div>
    </div>

  </div>
`);

////////////////////////////////////////////////////////////
//// Month picker

const heatmapDatePicker = $("#heatmapDatePicker")
  .datepicker({
    language: "en",
    position: "bottom right",
    view: "months",
    minView: "months",
    autoClose: true,
    toggleSelected: false,
    minDate: moment(minDate.format("YYYY-MM"), "YYYY-MM").toDate(),
    maxDate: moment(maxDate.format("YYYY-MM"), "YYYY-MM").toDate(),
    onSelect: (formattedDate, date, el) => {
      const datepickerMonth = moment.utc(formattedDate, "YYYY-MM-DD");
      if (datepickerMonth.isSame(selectedMonth)) return;
      selectedMonth = datepickerMonth;
      el.el.value = selectedMonth.format("YYYY-MMM");
      updateHeatmap();
    }
  })
  .data("datepicker");

  updateControlAlignment();

  function updateControlAlignment() {
    controlContainer
      .select(".monthly-activity-label")
      .style(
        "padding-left",
        margin.left + width / 2 - visibleWidth / 2 + yAxisWidth + "px"
      )
    controlContainer
      .select(".month-select")
      .style(
        "padding-right",
        containerWidth -
          (margin.left +
            width / 2 +
            visibleWidth / 2 -
            legendWidth +
            20 +
            legendStripSize) +
          "px"
      );
  }

////////////////////////////////////////////////////////////
//// Heatmap ///////////////////////////////////////////////
////////////////////////////////////////////////////////////
// Scale
const xScale = d3
  .scalePoint()
  .domain(d3.range(1, 32))
  .range([0, heatmapWidth])
  .padding(0.5);
const yScale = d3
  .scalePoint()
  .domain(d3.range(0, 24))
  .range([0, heatmapHeight])
  .padding(0.5);
const colorScale = d3
  .scaleLinear()
  .domain(colorStops.map(d => d * colorScaleMaxDevices))
  .range(colors)
  .interpolate(colorInterpolator);

// Axis
const xAxis = d3.axisTop().scale(xScale);
const yAxis = d3
  .axisLeft()
  .scale(yScale)
  .tickFormat(d => `${d}:00`);

// Minor ticks
const yAxisMinorTicks = d3
  .axisLeft()
  .scale(yScale)
  .tickFormat(``)
  .tickSize(3);
const xAxisMinorTicks = d3
  .axisTop()
  .scale(xScale)
  .tickFormat(``)
  .tickSize(3);

const gAxis = g.append("g").attr("class", "axis");
const gXAxis = gAxis.append("g").attr("class", "x-axis");
const gXAxisMinor = gAxis.append("g").attr("class", "x-axis");
const gYAxis = gAxis.append("g").attr("class", "y-axis");
const gYAxisMinor = gAxis.append("g").attr("class", "y-axis");

function updateAxes() {
  gXAxis.call(xAxis);
  gXAxis.select(".domain").remove();
  gXAxis
    .selectAll(".tick")
    .filter((d, i) => i % 2 === 1)
    .remove();
  // create minor X-axis ticks
  gXAxisMinor.call(xAxisMinorTicks);
  gXAxisMinor.select(".domain").remove();
  gXAxisMinor
    .selectAll(".tick")
    .filter((d, i) => i % 2 === 0)
    .remove();

  gYAxis.call(yAxis);
  gYAxis.select(".domain").remove();
  gYAxis
    .selectAll(".tick")
    .filter((d, i) => i % 2 === 1)
    .remove();
  // create minor Y-axis ticks
  gYAxisMinor.call(yAxisMinorTicks);
  gYAxisMinor.select(".domain").remove();
  gYAxisMinor
    .selectAll(".tick")
    .filter((d, i) => i % 2 === 0)
    .remove();
}

updateAxes();

gAxis
  .append("text")
  .attr("x", 0)
  .attr("y", -20)
  .attr("text-anchor", "start")
  .text("Day");

gAxis
  .append("text")
  .attr("x", -35)
  .attr("y", 0)
  .attr("transform", `rotate(-90,-35,0)`)
  .attr("text-anchor", "end")
  .text("Time in Europe/Amsterdam");

const gCells = g.append("g").attr("class", "heatmap-cells");

// Focus
const gFocus = g
  .append("g")
  .attr("class", "heatmap-day-focus")
  .style("pointer-events", "none");

const gFocusFreezedRect = gFocus
  .append("rect")
  .attr("y", 0)
  .attr("width", cellSize)
  .attr("height", heatmapHeight)
  .attr("fill", "none")
  .attr("stroke", focusFreezedRectStrokeColor)
  .style("display", "none");

const gFocusRect = gFocus
  .append("rect")
  .attr("y", 0)
  .attr("width", cellSize)
  .attr("height", heatmapHeight)
  .attr("fill", "none")
  .attr("stroke", focusRectStrokeColor)
  .style("display", "none");

function updateHeatmap() {
  const monthStart = selectedMonth;
  const monthEnd = selectedMonth.clone().endOf("month");
  const startIndex = data.findIndex(d => d.time.isSameOrAfter(monthStart));
  const endIndex = data.findIndex(d => d.time.isAfter(monthEnd));
  const monthData =
    endIndex === -1
      ? data.slice(startIndex)
      : data.slice(startIndex, endIndex);

  const maxDevices = d3.max(monthData, d => d.devices);

  // Update x axis ticks
  const numDaysInMonth = parseInt(monthEnd.format("D"));
  gXAxis
    .selectAll(".tick")
    .style("display", d => (d > numDaysInMonth ? "none" : "block"));

  // Heatmap cell
  const exitTransition = d3.transition().duration(500);
  const enterTransition = exitTransition.transition().duration(500);

  const cellExit = gCells
    .selectAll(".heatmap-cell")
    .attr("class", "heatmap-cell-exit")
    .transition(exitTransition)
    .remove();

  cellExit
    .select("rect")
    .attr("y", d => yScale(d.hour))
    .attr("height", 0);

  cellExit
    .selectAll("line")
    .attr("y1", d => yScale(d.hour))
    .attr("y2", d => yScale(d.hour));

  const cell = gCells
    .selectAll(".heatmap-cell")
    .data(monthData, d => d.time.unix())
    .enter()
    .append("g")
    .attr("class", "heatmap-cell");

  cell
    .append("rect")
    .attr("class", "heatmap-cell-rect")
    .attr("x", d => xScale(d.day) - cellSize / 2)
    .attr("y", d => yScale(d.hour))
    .attr("width", cellSize)
    .attr("height", 0)
    .attr("stroke", cellStrokeColor)
    .attr("fill", d => colorScale(d.devices))
    .on("mouseover", d => {
      gFocusRect
        .attr("x", xScale(d.day) - cellSize / 2)
        .style("display", "block");

      gXAxis
        .selectAll(".tick text")
        .filter(e => e === d.day)
        .attr("font-weight", "bold");
      gYAxis
        .selectAll(".tick text")
        .filter(e => e === d.hour)
        .attr("font-weight", "bold");

      showTooltip(d);
      if (!freezedDay) {
        window.dispatchEvent(
          new CustomEvent("heatmap-date-change", {
            detail: { heatmapDate: d.time.clone().startOf("day") }
          })
        );
      }
    })
    .on("mousemove", moveTooltip)
    .on("mouseout", d => {
      gFocusRect.style("display", "none");

      gXAxis
        .selectAll(".tick text")
        .filter(e => e === d.day)
        .attr("font-weight", undefined);
      gYAxis
        .selectAll(".tick text")
        .filter(e => e === d.hour)
        .attr("font-weight", undefined);

      hideTooltip();

      if (!freezedDay) {
        window.dispatchEvent(
          new CustomEvent("heatmap-date-change", {
            detail: { heatmapDate: undefined }
          })
        );
      }
    })
    .on("click", d => {
      const clickedDay = d.time.clone().startOf("day");
      if (freezedDay && freezedDay.isSame(clickedDay)) {
        freezedDay = undefined;
        gFocusFreezedRect.style("display", "none");
      } else {
        freezedDay = clickedDay;
        window.dispatchEvent(
          new CustomEvent("heatmap-date-change", {
            detail: { heatmapDate: d.time.clone().startOf("day") }
          })
        );
        gFocusFreezedRect
          .attr("x", xScale(d.day) - cellSize / 2)
          .style("display", "block");
      }
      gFocusRect.style("display", "none");
      hideTooltip();
    })
    .transition(enterTransition)
    .attr("y", d => yScale(d.hour) - cellSize / 2)
    .attr("height", cellSize);

  const maxCell = cell.filter(d => d.devices === maxDevices).raise();
  maxCell
    .select("rect")
    .attr("stroke", maxCellStrokeColor)
    .attr("stroke-width", maxCellStrokeWidth);

  const zeroCell = cell.filter(d => d.devices === 0);
  zeroCell
    .append("line")
    .style("pointer-events", "none")
    .attr("class", "zero-cell-line-1")
    .attr("stroke", cellStrokeColor)
    .attr("stroke-opacity", 0)
    .attr("x1", d => xScale(d.day) - cellSize / 2)
    .attr("x2", d => xScale(d.day) + cellSize / 2)
    .attr("y1", d => yScale(d.hour))
    .attr("y2", d => yScale(d.hour))
    .transition(enterTransition)
    .attr("y1", d => yScale(d.hour) - cellSize / 2)
    .attr("y2", d => yScale(d.hour) + cellSize / 2)
    .attr("stroke-opacity", 1);
  zeroCell
    .append("line")
    .style("pointer-events", "none")
    .attr("class", "zero-cell-line-2")
    .attr("stroke", cellStrokeColor)
    .attr("stroke-opacity", 0)
    .attr("x1", d => xScale(d.day) - cellSize / 2)
    .attr("x2", d => xScale(d.day) + cellSize / 2)
    .attr("y1", d => yScale(d.hour))
    .attr("y2", d => yScale(d.hour))
    .transition(enterTransition)
    .attr("y1", d => yScale(d.hour) + cellSize / 2)
    .attr("y2", d => yScale(d.hour) - cellSize / 2)
    .attr("stroke-opacity", 1);

  // Update focus freezed rect
  gFocusFreezedRect.style("display", "none");
  if (
    freezedDay &&
    freezedDay.isSameOrAfter(monthStart) &&
    freezedDay.isSameOrBefore(monthEnd)
  ) {
    gFocusFreezedRect
      .attr("x", xScale(parseInt(freezedDay.format("D"))) - cellSize / 2)
      .transition()
      .duration(0)
      .delay(1000)
      .style("display", "block");
  }
}

////////////////////////////////////////////////////////////
//// Legend ////////////////////////////////////////////////
////////////////////////////////////////////////////////////

const linearGradient = svg
  .append("defs")
  .append("linearGradient")
  .attr("id", "heatmapLegendLinearGradient")
  .attr("x1", "0%")
  .attr("y1", "0%")
  .attr("x2", "0%")
  .attr("y2", "100%");

linearGradient
  .selectAll("stop")
  .data(
    colorScale.ticks().map((t, i, n) => ({
      offset: `${(100 * i) / n.length}%`,
      color: colorScale(t)
    }))
  )
  .enter()
  .append("stop")
  .attr("offset", d => d.offset)
  .attr("stop-color", d => d.color);

const gLegend = svg
  .append("g")
  .attr("class", "legend")
  .attr(
    "transform",
    `translate(${margin.left +
      width / 2 +
      visibleWidth / 2 -
      legendWidth +
      20 +
      legendStripSize},${margin.top +
      height / 2 -
      visibleHeight / 2 +
      xAxisHeight})`
  );

gLegend
  .append("rect")
  .attr("x", -legendStripSize)
  .attr("width", legendStripSize)
  .attr("height", heatmapHeight)
  .style("fill", "url(#heatmapLegendLinearGradient)");

const legendScale = d3
  .scaleLinear()
  .domain([0, colorScaleMaxDevices])
  .range([0, heatmapHeight]);

const legendAxis = d3
  .axisRight(legendScale)
  .ticks(heatmapWidth / 60)
  .tickSize(0)
  .tickFormat(d =>
    d === colorScaleMaxDevices
      ? "≥" + locale.format(",")(d)
      : locale.format(",")(d)
  );

const legendTicks = gLegend.append("g");
legendTicks
  .call(legendAxis)
  .select(".domain")
  .remove();

gLegend
  .append("text")
  .attr("text-anchor", "end")
  .attr("x", 0)
  .attr("y", -legendStripSize - 3)
  .attr("transform", `rotate(-90)`)
  .text("Total Number of Devices");

const gLegendAddition = svg
  .append("g")
  .attr("class", "legend-addition")
  .attr(
    "transform",
    `translate(${margin.left +
      width / 2 -
      visibleWidth / 2 +
      yAxisWidth}, ${margin.top +
      height / 2 +
      visibleHeight / 2 -
      legendAdditionHeight +
      6})`
  );

let endPosition = 0;
gLegendAddition
  .append("rect")
  .attr("width", legendStripSize)
  .attr("height", legendStripSize)
  .attr("fill", colorScale(colorScaleMaxDevices))
  .attr("stroke", maxCellStrokeColor)
  .attr("stroke-width", maxCellStrokeWidth)
  .each(function() {
    endPosition += legendStripSize;
  });
gLegendAddition
  .append("text")
  .attr("x", endPosition + 4)
  .attr("y", legendStripSize / 2)
  .attr("dy", "0.35em")
  .text("Max Number of Devices")
  .each(function() {
    endPosition += this.getBBox().width + 4;
  });

const zeroCellLegend = gLegendAddition
  .append("g")
  .attr("transform", `translate(${endPosition + 8}, 0)`);
zeroCellLegend
  .append("rect")
  .attr("width", legendStripSize)
  .attr("height", legendStripSize)
  .attr("fill", colorScale(0))
  .each(function() {
    endPosition += legendStripSize + 8;
  });
zeroCellLegend
  .append("line")
  .attr("x1", 0)
  .attr("x2", legendStripSize)
  .attr("y1", 0)
  .attr("y2", legendStripSize)
  .attr("stroke", cellStrokeColor);
zeroCellLegend
  .append("line")
  .attr("x1", 0)
  .attr("x2", legendStripSize)
  .attr("y1", legendStripSize)
  .attr("y2", 0)
  .attr("stroke", cellStrokeColor);
gLegendAddition
  .append("text")
  .attr("x", endPosition + 4)
  .attr("y", legendStripSize / 2)
  .attr("dy", "0.35em")
  .text("No Observations");

////////////////////////////////////////////////////////////
//// Tooltip ///////////////////////////////////////////////
////////////////////////////////////////////////////////////
function showTooltip(d) {
  const dayOfTheWeek = d.time.format("ddd");
  const date = d.time.format("YYYY-MM-DD");
  const hourStart = d.time.format("H:mm");
  const hourEnd = d.time
    .clone()
    .endOf("hour")
    .format("H:mm");

  const html = `
    <div>${dayOfTheWeek} ${date}</div>
    <div>${hourStart} - ${hourEnd}</div>
    <div>Total Devices</div>
    <div>${d.devices}</div>
  `;
  tooltip.html(html);
  tooltip.box = tooltip.node().getBoundingClientRect();
  tooltip.transition().style("opacity", 1);
}

function moveTooltip() {
  const top = d3.event.clientY - tooltip.box.height - 5;
  let left = d3.event.clientX - tooltip.box.width / 2;
  if (left < 0) {
    left = 0;
  } else if (left + tooltip.box.width > window.innerWidth) {
    left = window.innerWidth - tooltip.box.width;
  }
  tooltip.style("left", left + "px").style("top", top + "px");
}

function hideTooltip() {
  tooltip.transition().style("opacity", 0);
}

// Init
heatmapDatePicker.selectDate(
  moment(initMonth.format("YYYY-MM"), "YYYY-MM").toDate()
);

////////////////////////////////////////////////////////////
//// Resize ////////////////////////////////////////////////
////////////////////////////////////////////////////////////
function resize() {
  const containerWidth =
    document.getElementById(chartContainerId).clientWidth ||
    window.innerWidth;
  const containerHeight =
    document.getElementById(chartContainerId).clientHeight ||
    window.innerHeight;

  const width = containerWidth - margin.left - margin.right;
  const height = containerHeight - controlHeight - margin.top - margin.bottom;

  const cellSize = Math.min(
    (width - yAxisWidth - legendWidth) / 31,
    (height - xAxisHeight - legendAdditionHeight) / 24
  );
  const heatmapWidth = cellSize * 31;
  const heatmapHeight = cellSize * 24;
  const visibleWidth = yAxisWidth + heatmapWidth + legendWidth;
  const visibleHeight = xAxisHeight + heatmapHeight + legendAdditionHeight;

  svg
    .attr("width", containerWidth)
    .attr("height", containerHeight - controlHeight);
  g.attr(
    "transform",
    `translate(${margin.left +
      width / 2 -
      visibleWidth / 2 +
      yAxisWidth},${margin.top +
      height / 2 -
      visibleHeight / 2 +
      xAxisHeight})`
  );

  xScale.range([0, heatmapWidth]);
  yScale.range([0, heatmapHeight]);
  updateAxes();

  // Chart
  gFocusFreezedRect.attr("width", cellSize).attr("height", heatmapHeight);

  gFocusRect.attr("width", cellSize).attr("height", heatmapHeight);

  const cell = gCells.selectAll(".heatmap-cell");

  cell
    .select(".heatmap-cell-rect")
    .attr("x", d => xScale(d.day) - cellSize / 2)
    .attr("y", d => yScale(d.hour) - cellSize / 2)
    .attr("width", cellSize)
    .attr("height", cellSize);

  const zeroCell = cell.filter(d => d.devices === 0);
  zeroCell
    .select(".zero-cell-line-1")
    .attr("x1", d => xScale(d.day) - cellSize / 2)
    .attr("x2", d => xScale(d.day) + cellSize / 2)
    .attr("y1", d => yScale(d.hour) - cellSize / 2)
    .attr("y2", d => yScale(d.hour) + cellSize / 2);
  zeroCell
    .select(".zero-cell-line-2")
    .attr("stroke", cellStrokeColor)
    .attr("x1", d => xScale(d.day) - cellSize / 2)
    .attr("x2", d => xScale(d.day) + cellSize / 2)
    .attr("y1", d => yScale(d.hour) + cellSize / 2)
    .attr("y2", d => yScale(d.hour) - cellSize / 2);

  // Legend
  gLegend.attr(
    "transform",
    `translate(${margin.left +
      width / 2 +
      visibleWidth / 2 -
      legendWidth +
      20 +
      legendStripSize},${margin.top +
      height / 2 -
      visibleHeight / 2 +
      xAxisHeight})`
  );

  gLegend.select("rect").attr("height", heatmapHeight);

  legendScale.range([0, heatmapHeight]);

  legendAxis.ticks(heatmapHeight / 60);

  legendTicks
    .call(legendAxis)
    .select(".domain")
    .remove();

  gLegendAddition.attr(
    "transform",
    `translate(${margin.left +
      width / 2 -
      visibleWidth / 2 +
      yAxisWidth}, ${margin.top +
      height / 2 +
      visibleHeight / 2 -
      legendAdditionHeight +
      6})`
  );
}

const throttledResize = throttle(resize, 250);
window.addEventListener("resize", throttledResize);

return chart;
}
