function barChart(options) {
  const chartContainerId = options.chartContainerId;
  const dataURL = options.dataURL;
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
  let allData, data;

  const margin = { top: 10, right: 10, bottom: 70, left: 52 };
  const width = containerWidth - margin.left - margin.right;
  const height = containerHeight - margin.top - margin.bottom;

  const x = d3
    .scaleBand()
    .range([0, width])
    .padding(0.08);

  const y = d3.scaleLinear().range([height, 0]);

  const xAxis = d3.axisBottom().scale(x);

  let xTickInterval = Math.ceil(1200 / width);

  const locale = d3.formatLocale({
    decimal: ".",
    thousands: " ",
    grouping: [3],
    currency: ["€", ""]
  });

  const yAxis = d3
    .axisLeft()
    .scale(y)
    .tickFormat(d => locale.format(",")(d));

  const chartContainer = d3
    .select(`#${chartContainerId}`)
    .attr("class", "barChart");
  const tooltip = chartContainer
    .append("div")
    .attr("class", "tooltip")
    .style("opacity", 0);
  const dateRangePickerContainer = chartContainer
    .append("div")
    .attr("class", "barChartDateRangePicker");
  const barChartContainer = chartContainer
    .append("div")
    .attr("class", "barChartChart");

  const svg = barChartContainer
    .append("svg")
    .attr("width", containerWidth)
    .attr("height", containerHeight);

  const g = svg
    .append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);

  ////////////////////////////////////////////////////////////
  //// Processing Data ///////////////////////////////////////
  ////////////////////////////////////////////////////////////
  d3.json(dataURL).then(data => {
    init();
    render(data);
  });


  ////////////////////////////////////////////////////////////
  //// Rendering Chart ///////////////////////////////////////
  ////////////////////////////////////////////////////////////
  function init() {
    // Axes
    const gAxis = g.append("g").attr("class", "axis");

    gAxis
      .append("text")
      .attr("transform", `translate(${width / 2},${height + 68})`)
      .attr("text-anchor", "middle")
      .attr('class', 'bar-chart-label')
      .text("Aileen Boxes");

    gAxis
      .append("text")
      .attr("transform", `translate(-40,${height / 2})rotate(-90)`)
      .attr("text-anchor", "middle")
      .attr('class', 'bar-chart-label')
      .text("Average Daily Number of Devices Seen");

    gAxis
      .append("g")
      .attr("class", "x axis")
      .attr("transform", `translate(0,${height})`);

    gAxis.append("g").attr("class", "y axis");

    // Bars
    g.append("g").attr("class", "bars");
  }

  function render(data) {
    // Update scales
    x.domain(data.map(d => d.box_name));
    y.domain([0, d3.max(data, d => d.mean_devices_each_day)]).nice();

    // Calculate exit time
    const bars = g.selectAll(".bars");
    bars.selectAll(".bar").attr("class", "barExit");
    const ExitTransitionTime = 500 + bars.selectAll(".barExit").size() * 20;

    // Update axes
    g.select(".x.axis")
      .transition()
      .delay(ExitTransitionTime)
      .duration(500)
      .call(xAxis)
      .selectAll("text")
      .attr("transform", "rotate(-35)")
      .style("text-anchor", "end");

    g.select(".y.axis")
      .transition()
      .delay(ExitTransitionTime)
      .duration(500)
      .call(yAxis);

    // Update bars
    bars
      .selectAll(".barExit")
      .transition()
      .duration(500)
      .delay((d, i) => i * 20)
      .attr("y", height)
      .attr("height", 0)
      .on("end", function() {
        d3.select(this).remove();
      });

    bars
      .selectAll(".bar")
      .data(data)
      .enter()
      .append("rect")
      .attr("class", "bar")
      .attr("x", d => x(d.box_name))
      .attr("y", height)
      .attr("width", x.bandwidth())
      .attr("height", 0)
      .on("mouseover", showTooltip)
      .on("mousemove", moveTooltip)
      .on("mouseout", hideTooltip)
      .transition()
      .duration(500)
      .delay((d, i) => ExitTransitionTime + i * 20)
      .attr("y", d => y(d.mean_devices_each_day))
      .attr("height", d => height - y(d.mean_devices_each_day));
  }

  ////////////////////////////////////////////////////////////
  //// Tooltip ///////////////////////////////////////////////
  ////////////////////////////////////////////////////////////
  function showTooltip(d) {
    const html = `
      <div>${d.box_name}<div>
      <div>Average Daily Number of Devices Seen: ${d.mean_devices_each_day}<div>
    `;

    tooltip.html(html);
    tooltip.box = tooltip.node().getBoundingClientRect();
    tooltip.transition().style("opacity", 1);
  }

  function moveTooltip() {
    const top = d3.event.clientY - tooltip.box.height;
    let left = d3.event.clientX - tooltip.box.width / 2;
    if (left < 0) {
      left = 0;
    } else if (left + tooltip.box.width > containerWidth) {
      left = containerWidth - tooltip.box.width;
    }
    tooltip.style("left", left + "px").style("top", top + "px");
  }

  function hideTooltip() {
    tooltip.transition().style("opacity", 0);
  }
}
