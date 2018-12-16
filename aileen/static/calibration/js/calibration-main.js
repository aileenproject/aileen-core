function create_heat_map(options) {

  myDataURL = options.dataURL

  d3.json(myDataURL).then(data => {
    ////////////////////////////////////////////////////////////
    //// Processing Data ///////////////////////////////////////
    ////////////////////////////////////////////////////////////
    data.forEach(d => {
      d.time = moment.unix(d.time).utc();
      d.hour = parseInt(d.time.format("H"));
      d.day = parseInt(d.time.format("D"));
      d.dayOfWeek = parseInt(d.time.format("d"));
      d.devices = +d.seen_count;
    });

    const minDate = data[0].time.clone();
    const maxDate = data[data.length - 1].time.clone();

    const myHeatmapChart = heatmapChart({
      chartContainerId: "heatmapContainer",
      data: data,
      minDate: minDate,
      maxDate: maxDate,
      initMonth: maxDate.startOf("month").format("YYYY-MM")
    });


    });
  };
