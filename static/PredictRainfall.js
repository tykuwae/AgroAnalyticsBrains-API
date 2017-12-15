$(document).ready(function() {

	$('form').on('submit', function(event) {

		var formId = this.id;
		
		if (formId == 'executeARIMA'){
			$('#ARIMAprocessingAlert').show();
			$('#ARIMAprocessingMessage').text("Aguarde até o término da execução.");
			$('#ARIMAsuccessAlert').hide();
	
			event.preventDefault();
	
			var formData = new FormData();
			formData.append('modelo', 'ARIMA')
	
			$.ajax({
				type : 'POST',
				url : '/PredictRainfall',
				data : formData,
				processData : false,
				contentType : false
			})
			.done(function(data) {
				
				if (data.error) {
					//
					// 	TODO
					//
					$('#errorAlert').text(data.error).show();
					$('#successAlert').hide();
				}
				else {
					$('#ARIMAsuccessAlert').show();
					$('#ARIMAsuccessMessage').text(data.message);
					$('#ARIMAprocessingAlert').hide();
					$('#ARIMAupdateChart').show();
					
				}
	
			});
		} else if (formId == 'executeSARIMA') {
			$('#SARIMAprocessingAlert').show();
			$('#SARIMAprocessingMessage').text("Aguarde até o término da execução.");
			$('#SARIMAsuccessAlert').hide();
	
			event.preventDefault();
	
			var formData = new FormData();
			formData.append('modelo', 'SARIMA')
	
			$.ajax({
				type : 'POST',
				url : '/PredictRainfall',
				data : formData,
				processData : false,
				contentType : false
			})
			.done(function(data) {
				
				if (data.error) {
					//
					// 	TODO
					//
					$('#errorAlert').text(data.error).show();
					$('#successAlert').hide();
				}
				else {
					$('#SARIMAsuccessAlert').show();
					$('#SARIMAsuccessMessage').text(data.message);
					$('#SARIMAprocessingAlert').hide();
					$('#SARIMAupdateChart').show();
					
				}
	
			});
		}
	});
})


$('#ARIMAupdateChart').on('click', ARIMAupdateChart);
$('#SARIMAupdateChart').on('click', SARIMAupdateChart);


function ARIMAupdateChart() {

	var updateData = $.get('/chartRainfallARIMA');
	
	$('#ARIMADiagnosis').show();

	updateData.done(function(results) {
	
		var data = {
			labels: results.index,	
			datasets: [
				{
				  label               : 'Dados de Treino',
				  fillColor           : 'rgba(210, 214, 222, 1)',
				  strokeColor         : 'rgba(210, 214, 222, 1)',
				  pointColor          : 'rgba(210, 214, 222, 1)',
				  pointStrokeColor    : '#c1c7d1',
				  pointHighlightFill  : '#fff',
				  pointHighlightStroke: 'rgba(220,220,220,1)',
				  data                : results.data_train
				},
				{
				  label               : 'Dados de Teste',
				  fillColor           : 'rgba(255, 178, 102, 1)',
				  strokeColor         : 'rgba(255, 178, 102, 1)',
				  pointColor          : 'rgba(255, 178, 102, 1)',
				  pointStrokeColor    : 'rgba(255, 178, 102, 1)',
				  pointHighlightFill  : '#fff',
				  pointHighlightStroke: 'rgba(255,178,102,1)',
				  borderDash: [5, 5],
				  data                : results.data_test
				},
				{
				  label               : 'Previsões',
				  fillColor           : 'rgba(60,141,188,0.9)',
				  strokeColor         : 'rgba(60,141,188,0.8)',
				  pointColor          : '#3b8bba',
				  pointStrokeColor    : 'rgba(60,141,188,1)',
				  pointHighlightFill  : '#fff',
				  pointHighlightStroke: 'rgba(60,141,188,1)',
				  data                : results.pred
				}
			  ]

		}

		var ChartOptions = {
			//Boolean - If we should show the scale at all
			showScale               : true,
			//Boolean - Whether grid lines are shown across the chart
			scaleShowGridLines      : false,
			//String - Colour of the grid lines
			scaleGridLineColor      : 'rgba(0,0,0,.05)',
			//Number - Width of the grid lines
			scaleGridLineWidth      : 1,
			//Boolean - Whether to show horizontal lines (except X axis)
			scaleShowHorizontalLines: true,
			//Boolean - Whether to show vertical lines (except Y axis)
			scaleShowVerticalLines  : true,
			//Boolean - Whether the line is curved between points
			bezierCurve             : true,
			//Number - Tension of the bezier curve between points
			bezierCurveTension      : 0.3,
			//Boolean - Whether to show a dot for each point
			pointDot                : false,
			//Number - Radius of each point dot in pixels
			pointDotRadius          : 4,
			//Number - Pixel width of point dot stroke
			pointDotStrokeWidth     : 1,
			//Number - amount extra to add to the radius to cater for hit detection outside the drawn point
			pointHitDetectionRadius : 20,
			//Boolean - Whether to show a stroke for datasets
			datasetStroke           : true,
			//Number - Pixel width of dataset stroke
			datasetStrokeWidth      : 2,
			//Boolean - Whether to fill the dataset with a color
			datasetFill             : true,
			//String - A legend template
			legendTemplate          : '<ul class="<%=name.toLowerCase()%>-legend"><% for (var i=0; i<datasets.length; i++){%><li><span style="background-color:<%=datasets[i].lineColor%>"></span><%if(datasets[i].label){%><%=datasets[i].label%><%}%></li><%}%></ul>',
			//Boolean - whether to maintain the starting aspect ratio or not when responsive, if set to false, will take up entire container
			maintainAspectRatio     : true,
			//Boolean - whether to make the chart responsive to window resizing
			responsive              : true
		  }

		//-------------
		//- LINE CHART -
		//--------------
		var lineChartCanvas          = $('#ARIMAChart').get(0).getContext('2d');
		var lineChart                = new Chart(lineChartCanvas);
		var lineChartOptions         = ChartOptions;
		lineChartOptions.datasetFill = false;
		//lineChartOptions.scales.xAxes.ticks.autoSkip=true
		//lineChartOptions.scales.xAxes.ticks.maxTicksLimit = 24
		lineChart.Line(data, ChartOptions);	
		
		$('#ARIMApdq').text(results.pdq);
		$('#ARIMARMSEtrain').text(results.rmse_train);
		$('#ARIMARMSEtest').text(results.rmse_test);
		$('#ARIMAAIC').text(results.AIC);
		$('#ARIMABIC').text(results.BIC);
		$('#ARIMAcity').text(results.city);
		$('#ARIMAdate').text(results.date);
	
	})

}


function SARIMAupdateChart() {
	
		var updateData = $.get('/chartRainfallSARIMA');
		
		$('#SARIMADiagnosis').show();
	
		updateData.done(function(results) {
		
			var data = {
				labels: results.index,	
				datasets: [
					{
					  label               : 'Dados de Treino',
					  fillColor           : 'rgba(210, 214, 222, 1)',
					  strokeColor         : 'rgba(210, 214, 222, 1)',
					  pointColor          : 'rgba(210, 214, 222, 1)',
					  pointStrokeColor    : '#c1c7d1',
					  pointHighlightFill  : '#fff',
					  pointHighlightStroke: 'rgba(220,220,220,1)',
					  data                : results.data_train
					},
					{
					  label               : 'Dados de Teste',
					  fillColor           : 'rgba(255, 178, 102, 1)',
					  strokeColor         : 'rgba(255, 178, 102, 1)',
					  pointColor          : 'rgba(255, 178, 102, 1)',
					  pointStrokeColor    : 'rgba(255, 178, 102, 1)',
					  pointHighlightFill  : '#fff',
					  pointHighlightStroke: 'rgba(255,178,102,1)',
					  borderDash: [5, 5],
					  data                : results.data_test
					},
					{
					  label               : 'Previsões',
					  fillColor           : 'rgba(60,141,188,0.9)',
					  strokeColor         : 'rgba(60,141,188,0.8)',
					  pointColor          : '#3b8bba',
					  pointStrokeColor    : 'rgba(60,141,188,1)',
					  pointHighlightFill  : '#fff',
					  pointHighlightStroke: 'rgba(60,141,188,1)',
					  data                : results.pred
					}
				  ]
	
			}
	
			var ChartOptions = {
				//Boolean - If we should show the scale at all
				showScale               : true,
				//Boolean - Whether grid lines are shown across the chart
				scaleShowGridLines      : false,
				//String - Colour of the grid lines
				scaleGridLineColor      : 'rgba(0,0,0,.05)',
				//Number - Width of the grid lines
				scaleGridLineWidth      : 1,
				//Boolean - Whether to show horizontal lines (except X axis)
				scaleShowHorizontalLines: true,
				//Boolean - Whether to show vertical lines (except Y axis)
				scaleShowVerticalLines  : true,
				//Boolean - Whether the line is curved between points
				bezierCurve             : true,
				//Number - Tension of the bezier curve between points
				bezierCurveTension      : 0.3,
				//Boolean - Whether to show a dot for each point
				pointDot                : false,
				//Number - Radius of each point dot in pixels
				pointDotRadius          : 4,
				//Number - Pixel width of point dot stroke
				pointDotStrokeWidth     : 1,
				//Number - amount extra to add to the radius to cater for hit detection outside the drawn point
				pointHitDetectionRadius : 20,
				//Boolean - Whether to show a stroke for datasets
				datasetStroke           : true,
				//Number - Pixel width of dataset stroke
				datasetStrokeWidth      : 2,
				//Boolean - Whether to fill the dataset with a color
				datasetFill             : true,
				//String - A legend template
				legendTemplate          : '<ul class="<%=name.toLowerCase()%>-legend"><% for (var i=0; i<datasets.length; i++){%><li><span style="background-color:<%=datasets[i].lineColor%>"></span><%if(datasets[i].label){%><%=datasets[i].label%><%}%></li><%}%></ul>',
				//Boolean - whether to maintain the starting aspect ratio or not when responsive, if set to false, will take up entire container
				maintainAspectRatio     : true,
				//Boolean - whether to make the chart responsive to window resizing
				responsive              : true
			  }
	
			//-------------
			//- LINE CHART -
			//--------------
			var lineChartCanvas          = $('#SARIMAChart').get(0).getContext('2d');
			var lineChart                = new Chart(lineChartCanvas);
			var lineChartOptions         = ChartOptions;
			lineChartOptions.datasetFill = false;
			//lineChartOptions.scales.xAxes.ticks.autoSkip=true
			//lineChartOptions.scales.xAxes.ticks.maxTicksLimit = 24
			lineChart.Line(data, ChartOptions);	
			
			$('#SARIMApdq').text(results.pdq);
			$('#SARIMAPDQs').text(results.PDQs);
			$('#SARIMARMSEtrain').text(results.rmse_train);
			$('#SARIMARMSEtest').text(results.rmse_test);
			$('#SARIMAAIC').text(results.AIC);
			$('#SARIMABIC').text(results.BIC);
			$('#SARIMAcity').text(results.city);
			$('#SARIMAdate').text(results.date);
		
		})
	
	}






