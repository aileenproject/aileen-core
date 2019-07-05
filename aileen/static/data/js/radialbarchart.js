function radialBarChart(options) {
  const chartContainerId = options.chartContainerId;
  const data = options.data;
  const minDate = options.minDate;
  const maxDate = options.maxDate;
  let potentialInitDateRangeStart = moment
    .utc(options.initDateRangeStart, "YYYY-MM-DD")
    .isValid() ?
    moment.utc(options.initDateRangeStart, "YYYY-MM-DD") :
    data[0].time.clone();
  let potentialInitDateRangeEnd = moment
    .utc(options.initDateRangeEnd, "YYYY-MM-DD")
    .isValid() ?
    moment.utc(options.initDateRangeEnd, "YYYY-MM-DD") :
    date[data.length - 1].time.clone();
  let initDateRangeStart, initDateRangeEnd;
  // Make sure the start date isn't before the first date in data
  if (potentialInitDateRangeStart.isBefore(data[0].time)) {
    potentialInitDateRangeStart = data[0].time.clone();
  }
  // Make sure the end date isn't after the last date in data
  if (potentialInitDateRangeEnd.isAfter(data[data.length - 1].time)) {
    potentialInitDateRangeEnd = data[data.length - 1].time.clone();
  }
  // Make sure the start date is before the end date
  if (potentialInitDateRangeStart.isBefore(potentialInitDateRangeEnd)) {
    initDateRangeStart = potentialInitDateRangeStart;
    initDateRangeEnd = potentialInitDateRangeEnd;
  } else {
    initDateRangeStart = data[0].time.clone();
    initDateRangeEnd = data[data.length - 1].time.clone();
  }
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
  let selectedAverageStartDate = initDateRangeStart;
  let selectedAverageEndDate = initDateRangeEnd;
  let selectedDayDate;
  let selectedDayFilter = "All days";
  let dateRangeFilteredData;
  let dayMaxseen;

  // Dimension
  const controlHeight = 60;
  const legendHeight = 24;
  const margin = {
    top: 15,
    right: 5,
    bottom: legendHeight + 5,
    left: 5
  };
  const width = containerWidth - margin.left - margin.right;
  const height = containerHeight - controlHeight - margin.top - margin.bottom;

  // Style
  const outerRadius = Math.min(width, height) / 2;
  const innerRadius = outerRadius * 0.4;
  const angleScalePadding = 0.36;
  const series = ["day", "average"];
  const color = ["#1D5464", "#D8D860"];
  const radiusAxisCircleStroke = "#ddd";
  const wedgeFillOpacity = 0.6;
  const wedgeFillOpacityHovered = 1.0;
  const maxWedgeStrokeColor = "#FF0000";

  const locale = d3.formatLocale({
    decimal: ".",
    thousands: " ",
    grouping: [3],
    currency: ["€", ""]
  });

  // Container
  const chartContainer = d3
    .select(`#${chartContainerId}`)
    .classed("radial-bar-chart", true);
  const tooltip = d3.select(".chart-tooltip");
  const controlContainer = chartContainer.append("div").attr("class", "row");
  const radialBarChartContainer = chartContainer
    .append("div")
    .attr("class", "radial-bar-chart row");
  const svg = radialBarChartContainer
    .append("svg")
    .attr("width", containerWidth)
    .attr("height", containerHeight - controlHeight);
  const g = svg
    .append("g")
    .attr(
      "transform",
      `translate(${margin.left + width / 2},${margin.top + height / 2})`
    );

  ////////////////////////////////////////////////////////////
  //// Control ///////////////////////////////////////////////
  ////////////////////////////////////////////////////////////

  controlContainer.html(`
    <div class="w-100 m-0 d-flex justify-content-center">
      <div class="form-group pr-3">
        <label>Selected Date Range</label>
        <div class="input-group">
          <div class="input-group-prepend">
            <span class="input-group-text"><i class="fa fa-calendar"></i></span>
          </div>
          <input type="text" class="form-control form-control-sm" id="radialBarDatePicker">
        </div>
      </div>

      <div class="form-group day-select">
        <label>Filter</label>
        <select class="form-control form-control-sm" id="radialBarDayFilterDropdown">
          <option>All days</option>
          <option>Monday</option>
          <option>Tuesday</option>
          <option>Wednesday</option>
          <option>Thursday</option>
          <option>Friday</option>
          <option>Saturday</option>
          <option>Sunday</option>
          <option>Weekday</option>
          <option>Weekend</option>
        </select>
      </div>

    </div>
  `);

  ////////////////////////////////////////////////////////////
  //// Date range Picker for average
  const radialBarDatePicker = $("#radialBarDatePicker")
    .datepicker({
      language: "en",
      position: "bottom right",
      range: true,
      multipleDatesSeparator: " — ",
      toggleSelected: false,
      autoClose: true,
      minDate: moment(minDate.format("YYYY-MM-DD"), "YYYY-MM-DD").toDate(),
      maxDate: moment(maxDate.format("YYYY-MM-DD"), "YYYY-MM-DD").toDate(),
      onSelect: (formattedDate, date, el) => {
        if (date.length !== 2) return;
        [formattedStartDate, formattedEndDate] = formattedDate.split(" — ");
        selectedAverageStartDate = moment.utc(formattedStartDate, "YYYY-MM-DD");
        selectedAverageEndDate = moment
          .utc(formattedEndDate, "YYYY-MM-DD")
          .endOf("day");
        dateRangeFilteredData = data.filter(
          d =>
          d.time.isSameOrAfter(selectedAverageStartDate) &&
          d.time.isSameOrBefore(selectedAverageEndDate)
        );
        updateRadialBar("average");
      }
    })
    .data("datepicker");

  ////////////////////////////////////////////////////////////
  //// Filter dropdown for average
  const dayFilterDefinition = {
    Monday: [1],
    Tuesday: [2],
    Wednesday: [3],
    Thursday: [4],
    Friday: [5],
    Saturday: [6],
    Sunday: [0],
    Weekday: [1, 2, 3, 4, 5],
    Weekend: [6, 0]
  };

  $("#radialBarDayFilterDropdown").on("change", function (event) {
    selectedDayFilter = event.target.value;
    updateRadialBar("average");
    updateLegendAverageText();
  });

  ////////////////////////////////////////////////////////////
  //// Radial Bar ////////////////////////////////////////////
  ////////////////////////////////////////////////////////////
  const arcs = d3.local();
  const outerRadiuses = d3.local();

  // Scale
  const angleScale = d3
    .scaleBand()
    .domain(d3.range(24).map(d => d.toString()))
    .range([0, Math.PI * 2])
    .paddingInner(angleScalePadding)
    .paddingOuter(angleScalePadding / 2);

  const radiusScale = d3.scaleRadial().range([innerRadius, outerRadius]);

  const colorScale = d3
    .scaleOrdinal()
    .domain(series)
    .range(color);

  // Axis
  const gAxis = g.append("g").attr("class", "axis");
  g.append("g").attr("class", "average-wedges");
  g.append("g").attr("class", "day-wedges");
  const gInvisibleWedges = g.append("g").attr("class", "invisible-wedges"); // Invisible wedges are used to capture mouse event
  const gAxisLabels = g.append("g").attr("class", "axis-labels");

  // Hours axis label
  const axisLabelRadius = innerRadius - 9;
  gAxisLabels
    .selectAll(".angle-axis-label")
    .data(angleScale.domain())
    .enter()
    .append("text")
    .attr("class", "angle-axis-label")
    .attr("dy", "0.35em")
    .attr(
      "x",
      d =>
      axisLabelRadius *
      Math.cos(
        angleScale(d) -
        Math.PI / 2 -
        (angleScale.step() * angleScalePadding) / 2
      )
    )
    .attr(
      "y",
      d =>
      axisLabelRadius *
      Math.sin(
        angleScale(d) -
        Math.PI / 2 -
        (angleScale.step() * angleScalePadding) / 2
      )
    )
    .attr("text-anchor", "middle")
    .text(d => (+d === 0 ? "0:00h" : +d % 2 === 0 ? d : ""));

  // Hour axis tick
  gAxis
    .selectAll(".angle-axis-line")
    .data(angleScale.domain())
    .enter()
    .append("line")
    .attr("class", "angle-axis-line")
    .attr("stroke", "#000")
    .attr("y1", innerRadius)
    .attr("y2", innerRadius - 3)
    .attr("transform", d => {
      const angle =
        angleScale(d) -
        Math.PI / 2 -
        (angleScale.step() * angleScalePadding) / 2;
      return `rotate(${(angle * 180) / Math.PI + 90})`;
    });

  // Total seen axis title
  gAxisLabels
    .append("text")
    .attr("class", "radius-axis-title")
    .attr("y", -outerRadius - 3)
    .attr("text-anchor", "middle")
    .text("Total observations");

  // Invisible wedges
  gInvisibleWedges
    .selectAll(".invisible-wedge")
    .data(angleScale.domain())
    .enter()
    .append("path")
    .attr("class", "invisible-wedge")
    .attr("d", function (d) {
      return d3
        .arc()
        .innerRadius(innerRadius)
        .outerRadius(outerRadius)
        .startAngle(angleScale(d))
        .endAngle(angleScale(d) + angleScale.bandwidth())();
    })
    .attr("fill", "none")
    .style("pointer-events", "all")
    .on("mouseover", d => {
      series.forEach(series => {
        g.select(`.${series}-wedges`)
          .selectAll(".wedge")
          .filter(e => e.hour.toString() === d)
          .attr("fill-opacity", wedgeFillOpacityHovered);
      });
      g.select(".axis-labels")
        .selectAll(".angle-axis-label")
        .filter(e => e === d)
        .attr("font-weight", "bold");
      showTooltip(d);
    })
    .on("mousemove", moveTooltip)
    .on("mouseout", d => {
      series.forEach(series => {
        g.select(`.${series}-wedges`)
          .selectAll(".wedge")
          .filter(e => e.hour.toString() === d)
          .attr("fill-opacity", wedgeFillOpacity);
      });
      g.select(".axis-labels")
        .selectAll(".angle-axis-label")
        .filter(e => e === d)
        .attr("font-weight", undefined);
      hideTooltip();
    });

  function updateRadialBar(seriesToUpdate) {
    // Update series data
    let seriesData;
    switch (seriesToUpdate) {
      case "day":
        if (selectedDayDate) {
          const dayStart = selectedDayDate;
          const dayEnd = selectedDayDate.clone().endOf("day");
          const startIndex = data.findIndex(d =>
            d.time.isSameOrAfter(dayStart)
          );
          let endIndex = data.findIndex(d => d.time.isAfter(dayEnd));
          endIndex = endIndex === -1 ? data.length : endIndex;

          seriesData = data.slice(startIndex, endIndex).map(d => {
            return {
              hour: d.hour,
              seen: d.seen
            };
          });
        } else {
          seriesData = [];
        }
        break;
      case "average":
        let dayFilteredData;
        if (selectedDayFilter === "All days") {
          dayFilteredData = dateRangeFilteredData;
        } else {
          const currentDayFilter = dayFilterDefinition[selectedDayFilter];
          dayFilteredData = dateRangeFilteredData.filter(d => {
            return currentDayFilter.includes(d.dayOfWeek);
          });
        }
        seriesData = d3
          .nest()
          .key(d => d.hour)
          .rollup(leaves => {
            const sum = d3.sum(leaves, leaf => leaf.seen);
            const count = leaves.filter(leaf => leaf.seen !== 0).length;
            return sum / count;
          })
          .entries(dayFilteredData)
          .map(d => ({
            hour: parseInt(d.key),
            seen: d.value
          }));
        break;
    }
    if (seriesData.length > 0) {
      radiusScale.domain([
        0,
        Math.max(d3.max(seriesData, d => d.seen), radiusScale.domain()[1])
      ]);
    } else {
      radiusScale.domain([
        0,
        Math.max(
          d3.max(
            g
            .select(`.average-wedges`)
            .selectAll(".wedge")
            .data(),
            d => d.seen
          )
        )
      ]);
    }

    // Update axes
    const radiusAxisCircle = g
      .select(".axis")
      .selectAll(".radius-axis-circle")
      .data(radiusScale.ticks(5), d => d);

    radiusAxisCircle
      .exit()
      .transition()
      .duration(500)
      .attr("r", d => {
        let exitR = radiusScale(d);
        if (exitR > outerRadius) {
          exitR = outerRadius;
        } else if (exitR < innerRadius) {
          exitR = innerRadius;
        }
        return exitR;
      })
      .remove();

    radiusAxisCircle
      .enter()
      .append("circle")
      .attr("class", "radius-axis-circle")
      .attr("fill", "none")
      .attr("stroke", radiusAxisCircleStroke)
      .merge(radiusAxisCircle)
      .transition()
      .duration(500)
      .attr("r", d => radiusScale(d));

    const radiusAxisLabel = g
      .select(".axis-labels")
      .selectAll(".radius-axis-label")
      .data(radiusScale.ticks(5), d => d);

    radiusAxisLabel
      .exit()
      .transition()
      .duration(500)
      .attr("transform", d => `translate(0, ${-radiusScale(d)})`)
      .remove();

    const radiusAxisLabelEnter = radiusAxisLabel
      .enter()
      .append("g")
      .attr("class", "radius-axis-label")
      .attr("transform", d => `translate(0, ${-innerRadius})`)
      .attr("text-anchor", "middle");

    radiusAxisLabelEnter
      .append("text")
      .attr("dy", "0.35em")
      .attr("stroke", "#fff")
      .attr("stroke-width", 3)
      .text(d => (d === 0 ? "" : locale.format(",")(d)));

    radiusAxisLabelEnter
      .append("text")
      .attr("dy", "0.35em")
      .text(d => (d === 0 ? "" : locale.format(",")(d)));

    radiusAxisLabelEnter
      .merge(radiusAxisLabel)
      .transition()
      .duration(500)
      .attr("transform", d => `translate(0, ${-radiusScale(d)})`);

    // Update wedges
    series.forEach(currentSeries => {
      if (currentSeries === seriesToUpdate) {
        const wedge = g
          .select(`.${seriesToUpdate}-wedges`)
          .selectAll(".wedge")
          .data(seriesData, d => d.hour);

        wedge
          .enter()
          .append("path")
          .attr("class", "wedge")
          .attr("fill", colorScale(seriesToUpdate))
          .attr("fill-opacity", wedgeFillOpacity)
          .attr("d", function (d) {
            const angleOffset = angleScale.bandwidth() / series.length;
            const startAngle =
              angleScale(d.hour.toString()) +
              series.indexOf(seriesToUpdate) * angleOffset;
            const endAngle = startAngle + angleOffset;
            const outerRadius = outerRadiuses.set(this, innerRadius);
            const arc = arcs.set(
              this,
              d3
              .arc()
              .innerRadius(innerRadius)
              .outerRadius(outerRadius)
              .startAngle(startAngle)
              .endAngle(endAngle)
            );
            return arc();
          })
          .merge(wedge)
          .attr("stroke", d =>
            d.seen === dayMaxseen && currentSeries === "day" ?
            maxWedgeStrokeColor :
            "none"
          )
          .transition()
          .duration(500)
          .attrTween("d", function (d) {
            const newOuterRadius = radiusScale(d.seen);
            return arcTween.call(this, newOuterRadius);
          })
          .on("end", function (d) {
            outerRadiuses.set(this, radiusScale(d.seen));
          });

        wedge
          .exit()
          .transition()
          .duration(500)
          .attrTween("d", function (d) {
            return arcTween.call(this, innerRadius);
          })
          .remove();
      } else {
        g.select(`.${currentSeries}-wedges`)
          .selectAll(".wedge")
          .attr("stroke", d =>
            d.seen === dayMaxseen && currentSeries === "day" ?
            maxWedgeStrokeColor :
            "none"
          )
          .transition()
          .duration(500)
          .attrTween("d", function (d) {
            const newOuterRadius = radiusScale(d.seen);
            return arcTween.call(this, newOuterRadius);
          })
          .on("end", function (d) {
            outerRadiuses.set(this, radiusScale(d.seen));
          });
      }
    });
  }

  function arcTween(newOuterRadius) {
    const arc = arcs.get(this);
    const oldOuterRadius = outerRadiuses.get(this);
    const i = d3.interpolateNumber(oldOuterRadius, newOuterRadius);
    return function (t) {
      const r = i(t);
      return arc.outerRadius(r)();
    };
  }

  ////////////////////////////////////////////////////////////
  //// Legend ///////////////////////////////////////////////
  ////////////////////////////////////////////////////////////
  const legendRowHeight = legendHeight / 2;
  const legendItemWidth = 155;
  const legendCircleRadius = legendRowHeight * 0.5;

  const gLegend = svg
    .append("g")
    .attr("class", "legend")
    .attr("transform", `translate(0, ${margin.top + height})`);

  const legendRow = gLegend
    .selectAll(".legend-row")
    .data(colorScale.domain().reverse())
    .enter()
    .append("g")
    .attr("class", d => `legend-row`)
    .attr(
      "transform",
      (d, i) =>
      `translate(${margin.left +
          width / 2 -
          i * legendItemWidth}, ${legendRowHeight})`
    );

  legendRow
    .append("circle")
    .attr("cx", legendCircleRadius)
    .attr("cy", 0)
    .attr("r", legendCircleRadius)
    .attr("fill", d => colorScale(d))
    .attr("opacity", 0.8);

  const legendText = legendRow.append("text");

  const dayText = legendText.filter(d => d === "day");
  updateLegendDayText();

  const averageText = legendText.filter(d => d === "average");
  averageText
    .append("tspan")
    .attr("x", legendCircleRadius * 2 + 3)
    .text("Average observations");
  const averageTextVariableRow = averageText
    .append("tspan")
    .attr("x", legendCircleRadius * 2 + 3)
    .attr("dy", "1em")
    .text("on " + selectedDayFilter);

  function updateLegendDayText() {
    if (!selectedDayDate) {
      dayText.selectAll("*").remove();
      dayText
        .text("Please Select a Day")
        .attr("x", legendCircleRadius * 2 + 3)
        .attr("dy", "0.35em");
    } else {
      dayText
        .text("")
        .attr("x", null)
        .attr("dy", null);
      dayText
        .append("tspan")
        .attr("x", legendCircleRadius * 2 + 3)
        .text("Total observations");
      dayText
        .append("tspan")
        .attr("x", legendCircleRadius * 2 + 3)
        .attr("dy", "1em")
        .text("on " + selectedDayDate.format("dddd YYYY-MM-DD"));
    }
  }

  function updateLegendAverageText() {
    averageTextVariableRow.text("on " + selectedDayFilter);
  }

  ////////////////////////////////////////////////////////////
  //// Tooltip ///////////////////////////////////////////////
  ////////////////////////////////////////////////////////////
  function showTooltip(d) {
    d = parseInt(d);
    let html = `
      <div>${d}:00 - ${d}:59</div>
      <div>Total seen </div>
    `;
    series.forEach(series => {
      const seriesData = g
        .select(`.${series}-wedges`)
        .selectAll(".wedge")
        .data();
      if (seriesData.length === 0) return;
      const hourData = seriesData.find(e => e.hour === d);
      if (!hourData) return;
      const circle = `<div style="display: inline-block; width: 0.8em; height: 0.8em; border-radius: 0.4em; background-color: ${colorScale(
        series
      )}"></div>`;
      const count =
        series === "average" ?
        hourData.seen === 0 ?
        0 :
        d3.format(".1f")(hourData.seen) :
        hourData.seen;
      html += `<div>${circle} ${count}</div>`;
    });
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

  radialBarDatePicker.selectDate([
    moment(
      selectedAverageStartDate.format("YYYY-MM-DD"),
      "YYYY-MM-DD"
    ).toDate(),
    moment(selectedAverageEndDate.format("YYYY-MM-DD"), "YYYY-MM-DD").toDate()
  ]);

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

    const outerRadius = Math.min(width, height) / 2;
    const innerRadius = outerRadius * 0.4;

    svg
      .attr("width", containerWidth)
      .attr("height", containerHeight - controlHeight);
    g.attr(
      "transform",
      `translate(${margin.left + width / 2},${margin.top + height / 2})`
    );

    radiusScale.range([innerRadius, outerRadius]);

    // Axes
    const axisLabelRadius = innerRadius - 9;
    gAxisLabels
      .selectAll(".angle-axis-label")
      .attr(
        "x",
        d =>
        axisLabelRadius *
        Math.cos(
          angleScale(d) -
          Math.PI / 2 -
          (angleScale.step() * angleScalePadding) / 2
        )
      )
      .attr(
        "y",
        d =>
        axisLabelRadius *
        Math.sin(
          angleScale(d) -
          Math.PI / 2 -
          (angleScale.step() * angleScalePadding) / 2
        )
      );

    gAxis
      .selectAll(".angle-axis-line")
      .attr("y1", innerRadius)
      .attr("y2", innerRadius - 3)
      .attr("transform", d => {
        const angle =
          angleScale(d) -
          Math.PI / 2 -
          (angleScale.step() * angleScalePadding) / 2;
        return `rotate(${(angle * 180) / Math.PI + 90})`;
      });

    gAxisLabels.select(".radius-axis-title").attr("y", -outerRadius - 3);

    g.select(".axis")
      .selectAll(".radius-axis-circle")
      .attr("r", d => radiusScale(d));

    g.select(".axis-labels")
      .selectAll(".radius-axis-label")
      .attr("transform", d => `translate(0, ${-radiusScale(d)})`);

    // Chart
    gInvisibleWedges.selectAll(".invisible-wedge").attr("d", function (d) {
      return d3
        .arc()
        .innerRadius(innerRadius)
        .outerRadius(outerRadius)
        .startAngle(angleScale(d))
        .endAngle(angleScale(d) + angleScale.bandwidth())();
    });

    series.forEach(seriesToUpdate => {
      g.select(`.${seriesToUpdate}-wedges`)
        .selectAll(".wedge")
        .attr("d", function (d) {
          const angleOffset = angleScale.bandwidth() / series.length;
          const startAngle =
            angleScale(d.hour.toString()) +
            series.indexOf(seriesToUpdate) * angleOffset;
          const endAngle = startAngle + angleOffset;
          const outerRadius = radiusScale(d.seen);
          const arc = arcs.set(
            this,
            d3
            .arc()
            .innerRadius(innerRadius)
            .outerRadius(outerRadius)
            .startAngle(startAngle)
            .endAngle(endAngle)
          );
          outerRadiuses.set(this, radiusScale(d.seen));
          return arc();
        });
    });

    // Legend
    legendRow.attr(
      "transform",
      (d, i) =>
      `translate(${margin.left +
          width / 2 -
          i * legendItemWidth}, ${legendRowHeight})`
    );
  }

  const throttledResize = throttle(resize, 250);
  window.addEventListener("resize", throttledResize);

  ////////////////////////////////////////////////////////////
  //// Exported Chart Methods ////////////////////////////////
  ////////////////////////////////////////////////////////////
  chart.updateDayBars = function (date, maxseen) {
    selectedDayDate = date ? date : undefined;
    dayMaxseen = maxseen;
    updateRadialBar("day");
    updateLegendDayText();
  };

  return chart;
}
