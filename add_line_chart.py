import re

def update_frontend_chart():
    with open('d:/Goldbees/frontend/src/app/page.js', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Add lineSeriesData and lineOptions
    # Find candlestickSeries
    candlestick_series_index = content.find('const candlestickSeries = [{')
    if candlestick_series_index != -1 and 'const lineSeriesData' not in content:
        line_chart_logic = """
  const lineSeriesData = [{
    name: 'Close Price',
    data: (ohlc || []).map(item => ({ x: item.x, y: item.y[3] }))
  }];

  const lineOptions = {
    chart: { type: 'area', background: 'transparent', toolbar: { show: false }, animations: { enabled: false } },
    theme: { mode: 'dark' },
    colors: ['#818cf8'], // Indigo color
    fill: {
      type: 'gradient',
      gradient: { shadeIntensity: 1, opacityFrom: 0.4, opacityTo: 0.05, stops: [0, 100] }
    },
    stroke: { curve: 'smooth', width: 2 },
    xaxis: { type: 'datetime', labels: { style: { colors: '#9ca3af' } }, axisBorder: { show: false }, axisTicks: { show: false } },
    yaxis: {
      labels: { formatter: (value) => '₹' + value.toFixed(2), style: { colors: '#9ca3af' } }
    },
    grid: { borderColor: '#1f2937', strokeDashArray: 4 },
    dataLabels: { enabled: false },
    tooltip: { theme: 'dark', x: { format: 'dd MMM yyyy' } }
  };
"""
        content = content[:candlestick_series_index] + line_chart_logic + "\n" + content[candlestick_series_index:]

    # 2. Inject the UI below the Candlestick chart
    # Find the end of the Candlestick chart div
    candlestick_ui_find = '<TrendingUp className="mr-2 text-emerald-500 w-6 h-6" /> Professional Candlestick Chart'
    if candlestick_ui_find in content and "Simple Price Trend" not in content:
        # We need to find the closing </div> of that section.
        # Let's just use regex to insert after the candlestick's ReactApexChart block
        # The block is:
        #           <div className="bg-gray-900 border border-gray-800 rounded-2xl shadow-lg p-6 lg:col-span-2">
        #             ... chart ...
        #           </div>
        # Let's insert it after that `</div>`
        pattern = r'(<ReactApexChart\s+options=\{candlestickOptions\}\s+series=\{candlestickSeries\}\s+type="candlestick"\s+height="100%"\s+/>\s*\)\s*:\s*\(\s*<div.*?</div>\s*\)\}\s*</div>\s*</div>)'
        
        replacement = r"""\1

          {/* Simple Price Trend Chart */}
          <div className="bg-gray-900 border border-gray-800 rounded-2xl shadow-lg p-6 lg:col-span-2">
            <h2 className="text-xl font-semibold mb-4 flex items-center text-gray-200">
              <TrendingUp className="mr-2 text-indigo-400 w-6 h-6" /> Simple Price Trend
            </h2>
            <div className="h-64 w-full relative">
              {ohlc && ohlc.length > 0 ? (
                <ReactApexChart 
                  options={lineOptions} 
                  series={lineSeriesData} 
                  type="area" 
                  height="100%" 
                />
              ) : (
                <div className="absolute inset-0 flex items-center justify-center text-gray-500">Loading chart data...</div>
              )}
            </div>
          </div>"""
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    with open('d:/Goldbees/frontend/src/app/page.js', 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    update_frontend_chart()
