(function() {
  const dataURL = aileen_data_url;

  d3.json(dataURL).then(data => {
    ////////////////////////////////////////////////////////////
    //// Processing Data ///////////////////////////////////////
    ////////////////////////////////////////////////////////////
    data.forEach(d => {
      d.time = moment.unix(d.time).utc();
      d.hour = parseInt(d.time.format("H"));
      d.date = d.time.clone().startOf("day");
      d.dayOfWeek = parseInt(d.time.format("d"));
      d.devices = +d.devices;
    });

    const minDate = data[0].time.clone();
    const maxDate = data[data.length - 1].time.clone();

    const myHeatmapChart = heatmapChart({
      chartContainerId: "heatmapContainer",
      data: data,
      minDate: minDate,
      maxDate: maxDate
    });

    const myRadialBarChart = radialBarChart({
      chartContainerId: "radialBarContainer",
      data: data,
      minDate: minDate,
      maxDate: maxDate,
      initDateRangeStart: maxDate
        .clone()
        .subtract(30, "days")
        .format("YYYY-MM-DD"),
      initDateRangeEnd: maxDate.format("YYYY-MM-DD")
    });

    window.addEventListener("heatmap-date-change", event => {
      const heatmapDate = event.detail.heatmapDate;
      const maxDevices = event.detail.maxDevices;
      myRadialBarChart.updateDayBars(heatmapDate, maxDevices);
    });
  });
})();
