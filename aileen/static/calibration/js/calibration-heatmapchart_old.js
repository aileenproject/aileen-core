function heatmapChart(options) {
  const chartContainerId = options.chartContainerId;
  const data = options.data;
  const minDate = options.minDate;
  const maxDate = options.maxDate;
  const initMonth = moment.utc(options.initMonth, "YYYY-MM").isValid()
    ? moment.utc(options.initMonth, "YYYY-MM")
    : data[0].time.clone().startOf("month");
  const chartContainerStyle = window.getComputedStyle(
    document.getElementById(chartContainerId)
  );
  const containerWidth =
    options.width ||
    document.getElementById(chartContainerId).clientWidth -
      parseInt(chartContainerStyle.paddingLeft) -
      parseInt(chartContainerStyle.paddingRight) ||
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
  let selectedMonth = initMonth;
  let freezedDay;

  // Dimension
  const margin = { top: 65, right: 5, bottom: 5, left: 5 };
  const width = containerWidth - margin.left - margin.right;
  const height = containerHeight - margin.top - margin.bottom;

  // Style
  const color = d3.interpolateGnBu;
  const max_times_seen = Math.max.apply(Math, data.map(function(o) { return o.seen_count}));
  const colorScaleMaxDevices = Math.max(max_times_seen, 100);
  console.log(colorScaleMaxDevices)
  const axisSize = 40;
  const legendPadding = 10;
  const legendWidth = 40;
  const cellSize = Math.min(
    (width - axisSize - legendPadding - legendWidth) / 31,
    (height - axisSize) / 24
  );
  const cellStrokeColor = "#fff";
  const heatmapWidth = cellSize * 31;
  const heatmapHeight = cellSize * 24;
  const focusRectStrokeColor = "#000";
  const focusFreezedRectStrokeColor = "#000";

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
  // const tooltip = chartContainer
  //   .append("div")
  //   .attr("class", "chart-tooltip")
  //   .style("opacity", 0);
  const tooltip = d3.select(".chart-tooltip");
  const controlContainer = chartContainer
    .append("div")
    .attr("class", "chart-control")
    .style("right", 0)
    .style("display", "flex")
    .style("justify-content", "flex-start");
  const heatmapContainer = chartContainer
    .append("div")
    .attr("class", "heatmap");
  const svg = heatmapContainer
    .append("svg")
    .attr("width", containerWidth)
    .attr("height", containerHeight);
  const g = svg
    .append("g")
    .attr(
      "transform",
      `translate(${margin.left + width / 2 - heatmapWidth / 2},${margin.top +
        height / 2 -
        heatmapHeight / 2})`
    );

  ////////////////////////////////////////////////////////////
  //// Control ///////////////////////////////////////////////
  ////////////////////////////////////////////////////////////
  controlContainer.html(`
      <form>
        <div class="form-group">
          <label>Select Month</label>
          <div class="input-group">
            <div class="input-group-prepend">
              <span class="input-group-text"><i class="fa fa-calendar"></i></span>
            </div>
            <input type="text" class="form-control form-control-sm" id="heatmapDatePicker">
          </div>
        </div>
      </form>
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
      minDate: moment(minDate.format("YYYY-MM"), "YYYY-MM").toDate(),
      maxDate: moment(maxDate.format("YYYY-MM"), "YYYY-MM").toDate(),
      onSelect: (formattedDate, date, el) => {
        selectedMonth = moment.utc(formattedDate, "YYYY-MM-DD");
        el.el.value = selectedMonth.format("YYYY-MM");
        updateHeatmap();
      }
    })
    .data("datepicker");

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
    .scaleSequential(color)
    .domain([0, colorScaleMaxDevices]);

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
  const xAxisMinorTicks = d3.axisTop()
    .scale(xScale)
    .tickFormat(``)
    .tickSize(3);

  const gAxis = g.append("g").attr("class", "axis");
  const gXAxis = gAxis.append("g").attr("class", "x-axis");
  const gXAxisMinor = gAxis.append('g').attr("class", "x-axis");
  const gYAxis = gAxis.append("g").attr("class", "y-axis");
  const gYAxisMinor = gAxis.append('g').attr("class", "y-axis");

  gXAxis.call(xAxis);
  gXAxis.select(".domain").remove();
  gXAxis
    .selectAll(".tick")
    .filter((d, i) => i % 2 === 1)
    .remove();
  // create minor X-axis ticks
  gXAxisMinor.call(xAxisMinorTicks);
  gXAxisMinor.select('.domain').remove();
  gXAxisMinor
    .selectAll(".tick")
    .filter((d, i) => i % 2 === 0 )
    .remove();

  gYAxis.call(yAxis);
  gYAxis.select(".domain").remove();
  gYAxis
    .selectAll(".tick")
    .filter((d, i) => i % 2 === 1)
    .remove();
  // create minor Y-axis ticks
  gYAxisMinor.call(yAxisMinorTicks);
  gYAxisMinor.select('.domain').remove();
  gYAxisMinor
    .selectAll(".tick")
    .filter((d, i) => i % 2 === 0)
    .remove();

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
    .text("Hour Europe/Amsterdam");

  gAxis
    .append("text")
    .attr("x", - heatmapHeight + 55)
    .attr("y", heatmapWidth + 40)
    .attr("transform", `rotate(-90,-35,0)`)
    .attr("text-anchor", "end")
    .text("Number of time seen");






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
    const monthData = endIndex === -1 ? data.slice(startIndex) : data.slice(startIndex, endIndex);


    monthData.forEach(d => {
      if (!d.day) {
        d.day = parseInt(d.time.format("D"));
      }
      if (!d.hour) {
        d.hour = parseInt(d.time.format("H"));
      }
    });

    // Update x axis ticks
    const numDaysInMonth = parseInt(monthEnd.format("D"));
    gXAxis
      .selectAll(".tick")
      .style("display", d => (d > numDaysInMonth ? "none" : "block"));

    // Heatmap cell
    gCells
      .selectAll(".heatmap-cell")
      .attr("class", "heatmap-cell-exit")
      .transition()
      .duration(500)
      .attr("y", d => yScale(d.hour))
      .attr("height", 0)
      .remove();

    gCells
      .selectAll(".heatmap-cell")
      .data(monthData)
      .enter()
      .append("rect")
      .attr("class", "heatmap-cell")
      .attr("x", d => xScale(d.day) - cellSize / 2)
      .attr("y", d => yScale(d.hour))
      .attr("width", cellSize)
      .attr("height", 0)
      .attr("stroke", cellStrokeColor)
      .attr("fill", d => colorScale(d.seen_count))
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
      // .on("mousemove", moveTooltip)
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
      .transition()
      .duration(500)
      .delay(500)
      .attr("y", d => yScale(d.hour) - cellSize / 2)
      .attr("height", cellSize);

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
  //// Legend ///////////////////////////////////////////////
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

  const gLegend = g
    .append("g")
    .attr("class", "legend")
    .attr("transform", `translate(${heatmapWidth + legendPadding},0)`);

  gLegend
    .append("rect")
    .attr("width", 12)
    .attr("height", heatmapHeight)
    .style("fill", "url(#heatmapLegendLinearGradient)");

  const legendScale = d3
    .scaleLinear()
    .domain(colorScale.domain())
    .range([0, heatmapHeight]);

  const legendAxis = d3
    .axisRight(legendScale)
    .ticks(heatmapHeight / 80)
    .tickSize(0)
    .tickFormat(d =>
      d === colorScaleMaxDevices
        ? "≥" + locale.format(",")(d)
        : locale.format(",")(d)
    );

  gLegend
    .append("g")
    .attr("transform", "translate(12,0)")
    .call(legendAxis)
    .select(".domain")
    .remove();

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
      <div>Times Seen</div>
      <div>${d.seen_count}</div>
    `;
    tooltip.html(html);
    tooltip.box = tooltip.node().getBoundingClientRect();
    tooltip.transition().style("opacity", 1);
  }

  // function moveTooltip() {
  //   const top = d3.event.clientY - tooltip.box.height - 5;
  //   let left = d3.event.clientX - tooltip.box.width / 2;
  //   if (left < 0) {
  //     left = 0;
  //   } else if (left + tooltip.box.width > window.innerWidth) {
  //     left = window.innerWidth - tooltip.box.width;
  //   }
  //   tooltip.style("left", left + "px").style("top", top + "px");
  // }

  function hideTooltip() {
    tooltip.transition().style("opacity", 0);
  }

  // Init
  heatmapDatePicker.selectDate(
    moment(selectedMonth.format("YYYY-MM"), "YYYY-MM").toDate()
  );
  return chart;
}
