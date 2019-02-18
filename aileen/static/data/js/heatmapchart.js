function heatmapChart(options) {
  const chartContainerId = options.chartContainerId;
  const data = options.data;
  const minDate = options.minDate;
  const maxDate = options.maxDate;
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
  let freezedDay;
  let xAxisMinDate;
  let xAxisMaxDate;
  let maxDevices;

  const allDates = enumerateDaysBetweenDates(
    data[0].date.clone(),
    data[data.length - 1].date.clone()
  );

  const heatmapWidthDays = 31;
  const leftAlign = allDates.length <= heatmapWidthDays;

  // Dimension
  const margin = {
    top: 5,
    right: 5,
    bottom: 5,
    left: 5
  };
  const width = containerWidth - margin.left - margin.right;
  const height = containerHeight - margin.top - margin.bottom;
  const padding = {
    top: 25,
    right: 40,
    bottom: 50,
    left: 40
  };
  let cellSize = Math.min(
    (width - padding.left - padding.right) / heatmapWidthDays,
    (height - padding.top - padding.bottom) / 24
  );
  const heatmapWidth = cellSize * heatmapWidthDays;
  const heatmapHeight = cellSize * 24;
  const visibleWidth = padding.left + heatmapWidth + padding.right;
  const visibleHeight = padding.top + heatmapHeight + padding.bottom;

  // Style
  const colors = ["#D8D860", "#D8D860", "#A6CCCD", "#207E82", "#1D5464"];
  const colorStops = [0.0, 0.05, 0.45, 0.75, 1.0];
  const colorInterpolator = d3.interpolateHcl;
  const max_times_seen = Math.max.apply(
    Math,
    data.map(function (o) {
      return o.devices;
    })
  );
  const colorScaleMaxDevices = Math.max(max_times_seen * 0.8, 100);
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

  const zoom = d3
    .zoom()
    .extent([
      [0, 0],
      [heatmapWidth, heatmapHeight]
    ])
    .scaleExtent([1, 1])
    .translateExtent([
      [heatmapWidth - cellSize * allDates.length, 0],
      [heatmapWidth, heatmapHeight]
    ])
    .on("zoom", zoomed);

  // Container
  const chartContainer = d3
    .select(`#${chartContainerId}`)
    .classed("heatmap-chart", true);
  const tooltip = d3.select(".chart-tooltip");
  // const controlContainer = chartContainer.append("div").attr("class", "row");
  const heatmapContainer = chartContainer
    .append("div")
    .attr("class", "heatmap row");
  const svg = heatmapContainer
    .append("svg")
    .attr("width", containerWidth)
    .attr("height", containerHeight);
  const g = svg
    .append("g")
    .attr(
      "transform",
      `translate(${margin.left +
        width / 2 -
        visibleWidth / 2 +
        padding.left},${margin.top +
        height / 2 -
        visibleHeight / 2 +
        padding.top})`
    );
  if (!leftAlign) {
    g.call(zoom);
  }

  const defs = g.append("defs");
  const cellsClip = defs
    .append("clipPath")
    .attr("id", "heat-map-chart-cells-clip")
    .append("rect")
    .attr("width", heatmapWidth)
    .attr("height", heatmapHeight);
  const xAxisClip = defs
    .append("clipPath")
    .attr("id", "heat-map-chart-x-axis-clip")
    .append("rect")
    .attr("y", -padding.top)
    .attr("width", heatmapWidth)
    .attr("height", padding.top);

  ////////////////////////////////////////////////////////////
  //// Heatmap ///////////////////////////////////////////////
  ////////////////////////////////////////////////////////////
  // Scale
  const xScale = d3
    .scalePoint()
    .domain(allDates)
    .padding(0.5);
  if (leftAlign) {
    xScale.range([0, cellSize * allDates.length]);
  } else {
    xScale.range([heatmapWidth - cellSize * allDates.length, heatmapWidth]);
  }
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
  const xAxis = d3
    .axisTop()
    .scale(xScale)
    .tickFormat(d => d.format("D"));
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
  const gXAxisContainer = gAxis
    .append("g")
    .attr("clip-path", "url(#heat-map-chart-x-axis-clip)");
  const gXAxisZoomContainer = gXAxisContainer.append("g");
  const gXAxis = gXAxisZoomContainer.append("g").attr("class", "x-axis");
  const gXAxisMinor = gXAxisZoomContainer.append("g").attr("class", "x-axis");
  const gYAxisContainer = gAxis.append("g");
  const gYAxis = gYAxisContainer.append("g").attr("class", "y-axis");
  const gYAxisMinor = gYAxisContainer.append("g").attr("class", "y-axis");
  const gXAxisExtent = g.append("g").attr("class", "x-axis-extent");

  const xAxisMinLabelG = gXAxisExtent
    .append("g")
    .attr("transform", `translate(${cellSize / 2},${heatmapHeight})`)
    .attr("text-anchor", "middle");
  xAxisMinLabelG
    .append("line")
    .attr("stroke", "#000")
    .attr("y2", 6);
  xAxisMinLabel = xAxisMinLabelG.append("text").attr("y", 9);
  const xAxisMinDayOfWeekLabel = xAxisMinLabel
    .append("tspan")
    .attr("x", 0)
    .attr("dy", "0.71em");
  const xAxisMinDateLabel = xAxisMinLabel
    .append("tspan")
    .attr("x", 0)
    .attr("dy", "1.21em");

  const xAxisMaxLabelG = gXAxisExtent
    .append("g")
    .attr(
      "transform",
      `translate(${heatmapWidth - cellSize / 2},${heatmapHeight})`
    )
    .attr("text-anchor", "middle");
  xAxisMaxLabelG
    .append("line")
    .attr("stroke", "#000")
    .attr("y2", 6);
  const xAxisMaxLabel = xAxisMaxLabelG.append("text").attr("y", 9);
  const xAxisMaxDayOfWeekLabel = xAxisMaxLabel
    .append("tspan")
    .attr("x", 0)
    .attr("dy", "0.71em");
  const xAxisMaxDateLabel = xAxisMaxLabel
    .append("tspan")
    .attr("x", 0)
    .attr("dy", "1.21em");

  function updateXAxisExtentLabels(maxDate) {
    if (leftAlign) {
      xAxisMinDate = maxDate.clone().subtract(allDates.length - 1, "days");
      xAxisMaxDate = xAxisMinDate.clone().add(heatmapWidthDays - 1, "days");
    } else {
      xAxisMaxDate = maxDate;
      xAxisMinDate = xAxisMaxDate
        .clone()
        .subtract(heatmapWidthDays - 1, "days");
    }
    xAxisMaxDayOfWeekLabel.text(xAxisMaxDate.format("ddd"));
    xAxisMaxDateLabel.text(xAxisMaxDate.format("YYYY-MM-DD"));
    xAxisMinDayOfWeekLabel.text(xAxisMinDate.format("ddd"));
    xAxisMinDateLabel.text(xAxisMinDate.format("YYYY-MM-DD"));
  }

  gAxis
    .append("text")
    .attr("x", 0)
    .attr("y", -21)
    .attr("text-anchor", "start")
    .text("Day");

  gAxis
    .append("text")
    .attr("x", -35)
    .attr("y", 0)
    .attr("transform", `rotate(-90,-35,0)`)
    .attr("text-anchor", "end")
    .text("Time in Europe/Amsterdam");

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

  const gCells = g
    .append("g")
    .attr("class", "heatmap-cells")
    .attr("clip-path", "url(#heat-map-chart-cells-clip)");

  const gCellsZoom = gCells.append("g");

  // Focus
  const gFocus = gCellsZoom
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
    // Heatmap cell
    const exitTransition = d3.transition().duration(500);
    const enterTransition = exitTransition.transition().duration(500);

    const cellExit = gCellsZoom
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

    const cell = gCellsZoom
      .insert("g", ".heatmap-day-focus")
      .selectAll(".heatmap-cell")
      .data(data, d => d.time.unix())
      .enter()
      .append("g")
      .attr("class", "heatmap-cell");

    cell
      .append("rect")
      .attr("class", "heatmap-cell-rect")
      .attr("x", d => xScale(d.date) - cellSize / 2)
      .attr("y", d => yScale(d.hour))
      .attr("width", cellSize)
      .attr("height", 0)
      .attr("stroke", cellStrokeColor)
      .attr("fill", d => colorScale(d.devices))
      .on("mouseover", d => {
        if (d3.event.buttons === 1) return; // Zoom/pan
        gFocusRect
          .attr("x", xScale(d.date) - cellSize / 2)
          .style("display", "block");

        gXAxis
          .selectAll(".tick text")
          .filter(e => e === d.date)
          .attr("font-weight", "bold");
        gYAxis
          .selectAll(".tick text")
          .filter(e => e === d.hour)
          .attr("font-weight", "bold");

        showTooltip(d);
        if (!freezedDay) {
          window.dispatchEvent(
            new CustomEvent("heatmap-date-change", {
              detail: {
                heatmapDate: d.date.clone(),
                maxDevices: maxDevices
              }
            })
          );
        }
      })
      .on("mousemove", moveTooltip)
      .on("mouseout", d => {
        gFocusRect.style("display", "none");

        gXAxis
          .selectAll(".tick text")
          .filter(e => e === d.date)
          .attr("font-weight", undefined);
        gYAxis
          .selectAll(".tick text")
          .filter(e => e === d.hour)
          .attr("font-weight", undefined);

        hideTooltip();

        if (!freezedDay) {
          window.dispatchEvent(
            new CustomEvent("heatmap-date-change", {
              detail: {
                heatmapDate: undefined
              }
            })
          );
        }
      })
      .on("click", d => {
        const clickedDay = d.date.clone();
        if (freezedDay && freezedDay.isSame(clickedDay)) {
          freezedDay = undefined;
          gFocusFreezedRect.style("display", "none");
        } else {
          freezedDay = clickedDay;
          window.dispatchEvent(
            new CustomEvent("heatmap-date-change", {
              detail: {
                heatmapDate: d.date.clone(),
                maxDevices: maxDevices
              }
            })
          );
          gFocusFreezedRect
            .attr("x", xScale(d.date) - cellSize / 2)
            .style("display", "block");
        }
        gFocusRect.style("display", "none");
        hideTooltip();
      })
      .transition(enterTransition)
      .attr("y", d => yScale(d.hour) - cellSize / 2)
      .attr("height", cellSize);

    const zeroCell = cell.filter(d => d.devices === 0);
    zeroCell
      .append("line")
      .style("pointer-events", "none")
      .attr("class", "zero-cell-line-1")
      .attr("stroke", cellStrokeColor)
      .attr("stroke-opacity", 0)
      .attr("x1", d => xScale(d.date) - cellSize / 2)
      .attr("x2", d => xScale(d.date) + cellSize / 2)
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
      .attr("x1", d => xScale(d.date) - cellSize / 2)
      .attr("x2", d => xScale(d.date) + cellSize / 2)
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

  function updateMaxCell() {
    const minVisibleDate = xAxisMinDate.clone().subtract(1, "days");
    const maxVisibleDate = xAxisMaxDate.clone().add(1, "days");
    const visibleCells = gCellsZoom
      .selectAll(".heatmap-cell")
      .filter(
        d =>
        d.date.isSameOrAfter(minVisibleDate) &&
        d.date.isSameOrBefore(maxVisibleDate)
      );

    visibleCells
      .filter(d => d.devices === maxDevices)
      .select("rect")
      .attr("stroke", cellStrokeColor)
      .attr("stroke-width", 1);

    const innerVisibleCells = visibleCells.filter(
      d =>
      d.date.isSameOrAfter(xAxisMinDate) &&
      d.date.isSameOrBefore(xAxisMaxDate)
    );

    maxDevices = d3.max(innerVisibleCells.data(), d => d.devices);

    const maxCell = innerVisibleCells
      .filter(d => d.devices === maxDevices)
      .raise();
    maxCell
      .select("rect")
      .attr("stroke", maxCellStrokeColor)
      .attr("stroke-width", maxCellStrokeWidth);
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
        padding.right +
        20 +
        legendStripSize},${margin.top +
        height / 2 -
        visibleHeight / 2 +
        padding.top})`
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
      d === colorScaleMaxDevices ?
      "≥" + locale.format(",")(d) :
      locale.format(",")(d)
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

  const gLegendAddition = g.append("g").attr("class", "legend-addition");
  let endPosition = 0;
  gLegendAddition
    .append("rect")
    .attr("width", legendStripSize)
    .attr("height", legendStripSize)
    .attr("fill", colorScale(colorScaleMaxDevices))
    .attr("stroke", maxCellStrokeColor)
    .attr("stroke-width", maxCellStrokeWidth)
    .each(function () {
      endPosition += legendStripSize;
    });
  gLegendAddition
    .append("text")
    .attr("x", endPosition + 4)
    .attr("y", legendStripSize / 2)
    .attr("dy", "0.35em")
    .text("Max Number of Devices")
    .each(function () {
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
    .each(function () {
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
    .text("No Observations")
    .each(function () {
      endPosition += this.getBBox().width + 4;
    });

  gLegendAddition.attr("transform", `translate(0,${heatmapHeight + 35})`);

  ////////////////////////////////////////////////////////////
  //// Panning ///////////////////////////////////////////////
  ////////////////////////////////////////////////////////////
  let transformXN = 0;

  function zoomed() {
    tooltip.style("opacity", 0);

    // Snap to the nearest day
    const transform = d3.event.transform;
    const transformX = transform.x;
    const n = Math.round(transformX / cellSize);

    if (transformXN === n) return;
    transformXN = n;
    transform.x = transformXN * cellSize;

    gXAxisZoomContainer.attr("transform", transform);
    gCellsZoom.attr("transform", transform);

    updateXAxisExtentLabels(
      allDates[allDates.length - 1 - transformXN].clone()
    );

    updateMaxCell();
  }

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
    <div><b>${d.devices}</b></div>
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
  updateHeatmap();
  updateAxes();
  updateXAxisExtentLabels(data[data.length - 1].date.clone());
  updateMaxCell();

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
    const height = containerHeight - margin.top - margin.bottom;

    cellSize = Math.min(
      (width - padding.left - padding.right) / heatmapWidthDays,
      (height - padding.top - padding.bottom) / 24
    );
    const heatmapWidth = cellSize * heatmapWidthDays;
    const heatmapHeight = cellSize * 24;
    const visibleWidth = padding.left + heatmapWidth + padding.right;
    const visibleHeight = padding.top + heatmapHeight + padding.bottom;

    zoom
      .extent([
        [0, 0],
        [heatmapWidth, heatmapHeight]
      ])
      .translateExtent([
        [heatmapWidth - cellSize * allDates.length, 0],
        [heatmapWidth, heatmapHeight]
      ]);

    svg.attr("width", containerWidth).attr("height", containerHeight);
    g.attr(
      "transform",
      `translate(${margin.left +
        width / 2 -
        visibleWidth / 2 +
        padding.left},${margin.top +
        height / 2 -
        visibleHeight / 2 +
        padding.top})`
    );

    cellsClip.attr("width", heatmapWidth).attr("height", heatmapHeight);
    xAxisClip.attr("width", heatmapWidth);

    if (leftAlign) {
      xScale.range([0, cellSize * allDates.length]);
    } else {
      xScale.range([heatmapWidth - cellSize * allDates.length, heatmapWidth]);
    }
    yScale.range([0, heatmapHeight]);
    xAxisMinLabelG.attr(
      "transform",
      `translate(${cellSize / 2},${heatmapHeight})`
    );
    xAxisMaxLabelG.attr(
      "transform",
      `translate(${heatmapWidth - cellSize / 2},${heatmapHeight})`
    );
    updateAxes();

    // Chart
    gFocusFreezedRect.attr("width", cellSize).attr("height", heatmapHeight);

    gFocusRect.attr("width", cellSize).attr("height", heatmapHeight);

    const cell = gCellsZoom.selectAll(".heatmap-cell");

    cell
      .select(".heatmap-cell-rect")
      .attr("x", d => xScale(d.date) - cellSize / 2)
      .attr("y", d => yScale(d.hour) - cellSize / 2)
      .attr("width", cellSize)
      .attr("height", cellSize);

    const zeroCell = cell.filter(d => d.devices === 0);
    zeroCell
      .select(".zero-cell-line-1")
      .attr("x1", d => xScale(d.date) - cellSize / 2)
      .attr("x2", d => xScale(d.date) + cellSize / 2)
      .attr("y1", d => yScale(d.hour) - cellSize / 2)
      .attr("y2", d => yScale(d.hour) + cellSize / 2);
    zeroCell
      .select(".zero-cell-line-2")
      .attr("stroke", cellStrokeColor)
      .attr("x1", d => xScale(d.date) - cellSize / 2)
      .attr("x2", d => xScale(d.date) + cellSize / 2)
      .attr("y1", d => yScale(d.hour) + cellSize / 2)
      .attr("y2", d => yScale(d.hour) - cellSize / 2);

    // Legend
    gLegend.attr(
      "transform",
      `translate(${margin.left +
        width / 2 +
        visibleWidth / 2 -
        padding.right +
        20 +
        legendStripSize},${margin.top +
        height / 2 -
        visibleHeight / 2 +
        padding.top})`
    );

    gLegend.select("rect").attr("height", heatmapHeight);

    legendScale.range([0, heatmapHeight]);

    legendAxis.ticks(heatmapHeight / 60);

    legendTicks
      .call(legendAxis)
      .select(".domain")
      .remove();

    gLegendAddition.attr("transform", `translate(0,${heatmapHeight + 35})`);

    if (!leftAlign) {
      const transformX = transformXN * cellSize;
      transformXN = 0;
      g.call(zoom.transform, d3.zoomIdentity.translate(transformX, 0));
    }
  }

  const throttledResize = throttle(resize, 500);
  window.addEventListener("resize", throttledResize);

  ////////////////////////////////////////////////////////////
  //// Utilities /////////////////////////////////////////////
  ////////////////////////////////////////////////////////////
  function enumerateDaysBetweenDates(startDate, endDate) {
    const dates = [];

    const currDate = startDate.clone().startOf("day");
    const lastDate = endDate.clone().endOf("day");

    do {
      dates.push(currDate.clone());
    } while (currDate.add(1, "days").diff(lastDate) < 0);
    return dates;
  }

  return chart;
}