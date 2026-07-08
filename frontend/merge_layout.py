import re

with open('src/app/page.js', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Add framer-motion import
if "import { motion } from 'framer-motion'" not in code:
    code = "import { motion } from 'framer-motion';\n" + code

# 2. Reskin Chart setups to light theme
code = code.replace("theme: { mode: 'dark' }", "theme: { mode: 'light' }")
code = code.replace("grid: { borderColor: '#2B3139' }", "grid: { borderColor: '#E5E7EB' }")
code = code.replace("grid: { borderColor: '#2B3139', strokeDashArray: 4 }", "grid: { borderColor: '#E5E7EB', strokeDashArray: 4 }")
code = code.replace("colors: ['#10B981']", "colors: ['#5A67D8']") # Indigo primary line chart
code = code.replace("xaxis: { type: 'datetime', labels: { style: { colors: '#9CA3AF' } } }", "xaxis: { type: 'datetime', labels: { style: { colors: '#6B7280' } } }")
code = code.replace("labels: { style: { colors: '#9CA3AF' }", "labels: { style: { colors: '#6B7280' }")
code = code.replace("labels: { formatter: (value) => '₹' + value.toFixed(2), style: { colors: '#9CA3AF' } }", "labels: { formatter: (value) => '₹' + value.toFixed(2), style: { colors: '#6B7280' } }")

# 3. Reskin Loading and Error states
code = code.replace(
    'bg-[#181A20] text-gray-200', 
    'bg-[#E8EFE9] text-gray-900'
)
code = code.replace(
    'border-emerald-500', 
    'border-[#5A67D8]'
)
code = code.replace(
    'text-gray-200 bg-[#181A20] h-screen',
    'text-gray-900 bg-[#E8EFE9] h-screen'
)

# 4. Find where "return (" starts for the main render block
# We locate the exact line where the main return starts (usually around line 570)
# We can find the match for "return (" after "const renderSignalBadge"
start_idx = code.find("return (", code.find("const renderSignalBadge"))

# The JSX content to inject
new_jsx = '''return (
    <div className="min-h-screen bg-[#E8EFE9] text-gray-900 font-sans flex overflow-hidden">
      <Toaster position="top-right" toastOptions={{
        style: { background: '#FFFFFF', color: '#111827', border: '1px solid #E5E7EB', borderRadius: '12px', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)' }
      }} />

      {/* LEFT SIDEBAR */}
      <aside className="w-64 bg-white border-r border-gray-100 flex flex-col hidden md:flex z-30 shadow-sm relative">
        <div className="p-6">
          <h1 className="text-2xl font-bold flex items-center tracking-tight text-gray-900">
            <div className="w-8 h-8 bg-emerald-600 rounded-lg mr-3 flex items-center justify-center text-white font-black">G</div>
            GoldBeES
          </h1>
        </div>
        <div className="px-6 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Main Menu</div>
        <nav className="flex-1 px-4 space-y-1">
          <div 
            onClick={() => setActiveTab('overview')}
            className={`flex items-center px-4 py-3 rounded-xl font-medium cursor-pointer transition-all ${activeTab === 'overview' ? 'bg-[#EEF2FF] text-[#5A67D8]' : 'text-gray-500 hover:bg-gray-50 hover:text-gray-900'}`}
          >
            <BarChart2 className="w-5 h-5 mr-3" /> Dashboard
          </div>
          <div 
            onClick={() => setActiveTab('ailab')}
            className={`flex items-center px-4 py-3 rounded-xl font-medium cursor-pointer transition-all ${activeTab === 'ailab' ? 'bg-[#EEF2FF] text-[#5A67D8]' : 'text-gray-500 hover:bg-gray-50 hover:text-gray-900'}`}
          >
            <Cpu className="w-5 h-5 mr-3" /> AI Lab
          </div>
          <div 
            onClick={() => setActiveTab('simulation')}
            className={`flex items-center px-4 py-3 rounded-xl font-medium cursor-pointer transition-all ${activeTab === 'simulation' ? 'bg-[#EEF2FF] text-[#5A67D8]' : 'text-gray-500 hover:bg-gray-50 hover:text-gray-900'}`}
          >
            <ShieldCheck className="w-5 h-5 mr-3" /> Risk Console
          </div>
        </nav>
        
        {/* Help / Settings */}
        <div className="p-4 border-t border-gray-100 flex items-center justify-between">
           <span className="text-sm text-gray-500 flex items-center"><Info className="w-4 h-4 mr-2"/> Help</span>
           <span className="text-sm text-gray-500 flex items-center"><Lock className="w-4 h-4 mr-2"/> Setting</span>
        </div>
      </aside>

      {/* MAIN CONTENT AREA */}
      <main className="flex-1 flex flex-col h-screen overflow-y-auto">
        
        {/* TOP HEADER */}
        <header className="bg-white px-8 py-4 flex items-center justify-between border-b border-gray-100 sticky top-0 z-20 shadow-sm">
           <div className="flex items-center text-sm font-medium text-gray-500 bg-gray-50 px-4 py-2 rounded-lg border border-gray-100">
             <Calendar className="w-4 h-4 mr-2" /> GoldBeES Market Analyzer
           </div>
           
           <div className="flex items-center space-x-6">
             <a href={`${API_BASE_URL}/report`} target="_blank" rel="noreferrer" className="text-gray-400 hover:text-gray-600 transition-colors">
               <Download className="w-5 h-5" />
             </a>
             {userId ? (
               <button onClick={handleLogout} className="text-sm text-red-500 font-medium hover:text-red-600">Log Out</button>
             ) : (
               <button onClick={() => setShowAuthModal(true)} className="text-sm text-[#5A67D8] font-bold hover:text-indigo-700 bg-indigo-50 px-4 py-2 rounded-lg">Log In / Register</button>
             )}
             <div className="w-px h-6 bg-gray-200"></div>
             <div className="flex items-center space-x-3 cursor-pointer">
               <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center border-2 border-white shadow-sm overflow-hidden">
                  <span className="text-gray-500 font-bold text-xs">U</span>
               </div>
               <div className="hidden sm:block text-sm font-bold text-gray-700">{userId || "Guest"}</div>
             </div>
           </div>
        </header>

        {/* CONTAINER */}
        <div className="p-8 max-w-[1400px] w-full mx-auto">
          {activeTab === 'overview' && (
            <motion.div 
              initial="hidden" 
              animate="show" 
              variants={{
                hidden: { opacity: 0 },
                show: { opacity: 1, transition: { staggerChildren: 0.1, delayChildren: 0.1 } }
              }} 
              className="space-y-6"
            >
              
              {/* TOP SUMMARY CARDS */}
              <motion.div variants={{ hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0, transition: { duration: 0.4, ease: "easeOut" } } }} className="grid grid-cols-1 md:grid-cols-2 gap-6">
                 <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm relative overflow-hidden">
                    <div className="absolute top-0 right-0 p-4 opacity-5"><Briefcase className="w-24 h-24 text-gray-900"/></div>
                    <p className="text-sm font-semibold text-gray-500 mb-2">Total Invested (INR)</p>
                    <div className="flex items-end space-x-4">
                       <h2 className="text-4xl font-bold text-gray-900 font-mono tracking-tight">₹{investedAmount.toFixed(2)}</h2>
                       <span className="text-emerald-500 font-semibold text-sm bg-emerald-50 px-2 py-1 rounded-md mb-1 flex items-center">
                         <ArrowUpRight className="w-3 h-3 mr-1"/> +2.72%
                       </span>
                    </div>
                 </div>
                 <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm relative overflow-hidden">
                    <p className="text-sm font-semibold text-gray-500 mb-2">Total Portfolio (Units)</p>
                    <div className="flex items-end space-x-4">
                       <h2 className="text-4xl font-bold text-gray-900 font-mono tracking-tight">{units || 0} <span className="text-lg text-gray-400">UNITS</span></h2>
                       <span className={`font-semibold text-sm px-2 py-1 rounded-md mb-1 flex items-center ${profitLossPercent >= 0 ? 'text-emerald-500 bg-emerald-50' : 'text-rose-500 bg-rose-50'}`}>
                         {profitLossPercent >= 0 ? <TrendingUp className="w-3 h-3 mr-1"/> : <TrendingDown className="w-3 h-3 mr-1"/>}
                         {profitLossPercent.toFixed(2)}%
                       </span>
                    </div>
                 </div>
              </motion.div>

              {/* MAIN CHART & SIDEBAR GRID */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                
                {/* LEFT: CHART AREA */}
                <motion.div variants={{ hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0, transition: { duration: 0.4, ease: "easeOut" } } }} className="lg:col-span-2 space-y-6">
                   <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
                      <div className="flex justify-between items-start mb-6">
                        <div>
                           <div className="flex items-center mb-2">
                             <div className="w-6 h-6 bg-yellow-100 rounded-md flex items-center justify-center mr-2"><span className="text-yellow-600 font-bold text-xs">G</span></div>
                             <h3 className="font-bold text-gray-900 text-lg">GoldBeES (ETF)</h3>
                           </div>
                           <h2 className="text-3xl font-bold text-gray-900 font-mono">₹{current_price.toFixed(2)}</h2>
                        </div>
                        <div className="flex space-x-2">
                          {['1D', '5D', '1M', 'YTD', '6M', '1Y', '5Y', 'MAX'].map(tf => (
                            <span 
                              key={tf}
                              onClick={() => setChartTimeframe(tf)}
                              className={`px-3 py-1.5 text-xs font-semibold rounded-lg cursor-pointer transition-colors ${chartTimeframe === tf ? 'bg-[#5A67D8] text-white shadow-sm shadow-indigo-200' : 'text-gray-500 hover:bg-gray-100'}`}
                            >
                              {tf}
                            </span>
                          ))}
                        </div>
                      </div>

                      <div className="h-80 w-full relative -mx-2">
                        {ohlc && ohlc.length > 0 ? (
                          <ReactApexChart options={lineOptions} series={lineSeriesData} type="area" height="100%" />
                        ) : (
                          <div className="absolute inset-0 flex items-center justify-center text-gray-400 text-sm">Loading chart data...</div>
                        )}
                      </div>
                   </div>

                   {/* AI Smart Advice Row */}
                   <div className="bg-[#EEF2FF] border border-indigo-100 rounded-2xl p-6 flex flex-col md:flex-row items-center justify-between">
                     <div className="flex items-center mb-4 md:mb-0">
                       <div className="w-12 h-12 bg-white rounded-full flex items-center justify-center shadow-sm mr-4">
                         <Zap className="w-6 h-6 text-[#5A67D8]"/>
                       </div>
                       <div>
                         <h4 className="text-sm font-bold text-gray-900">AI Portfolio Advisor</h4>
                         <p className="text-sm text-indigo-700 font-medium">{smartAdvice}</p>
                       </div>
                     </div>
                   </div>
                </motion.div>

                {/* RIGHT: WIDGETS */}
                <motion.div variants={{ hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0, transition: { duration: 0.4, ease: "easeOut" } } }} className="space-y-6">
                   
                   {/* Confidence Widget */}
                   {intelligenceData?.confidence && (
                     <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
                       <div className="flex justify-between items-center mb-4">
                         <h3 className="font-bold text-gray-900 text-sm">AI Confidence</h3>
                         <span className="text-xs text-gray-400 font-medium">{intelligenceData.confidence.label}</span>
                       </div>
                       <div className="flex items-end justify-between mb-3">
                         <span className={`text-4xl font-bold font-mono tracking-tight ${intelligenceData.confidence.score >= 80 ? 'text-emerald-500' : intelligenceData.confidence.score >= 60 ? 'text-yellow-500' : 'text-red-500'}`}>
                           {intelligenceData.confidence.score}%
                         </span>
                       </div>
                       <div className="w-full bg-gray-100 rounded-full h-1.5">
                         <div className={`h-1.5 rounded-full ${intelligenceData.confidence.score >= 80 ? 'bg-emerald-500' : intelligenceData.confidence.score >= 60 ? 'bg-yellow-500' : 'bg-red-500'}`} style={{ width: `${intelligenceData.confidence.score}%` }} />
                       </div>
                     </div>
                   )}

                   {/* Regime Widget */}
                   {intelligenceData?.market_regime && (
                     <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
                       <div className="flex justify-between items-center mb-4">
                         <h3 className="font-bold text-gray-900 text-sm">Market Regime</h3>
                         <span className="text-xs text-gray-400 font-medium">{intelligenceData.market_regime.confidence}% conf</span>
                       </div>
                       <div className="mb-4">
                         <span className={`inline-block px-4 py-2 rounded-xl text-lg font-bold border ${
                           intelligenceData.market_regime.regime === 'Bull' ? 'bg-emerald-50 text-emerald-700 border-emerald-500/20' :
                           intelligenceData.market_regime.regime === 'Bear' ? 'bg-rose-50 text-rose-700 border-red-500/20' :
                           'bg-yellow-50 text-yellow-700 border-yellow-500/20'
                         }`}>
                           {intelligenceData.market_regime.regime === 'Bull' ? '🐂' : intelligenceData.market_regime.regime === 'Bear' ? '🐻' : '↔️'} {intelligenceData.market_regime.regime}
                         </span>
                       </div>
                       <div className="flex space-x-4 mt-2">
                         <span className="text-xs text-gray-500">RSI: {intelligenceData.market_regime.rsi}</span>
                         <span className="text-xs text-gray-500">Vol: {intelligenceData.market_regime.volatility}%</span>
                       </div>
                     </div>
                   )}

                   {/* Macro Data Widget */}
                   {macroData && (
                     <div className="grid grid-cols-2 gap-4">
                       <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-4 text-center">
                         <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">USD/INR</p>
                         <p className="text-lg font-bold text-gray-900 font-mono tracking-tight">₹{macroData.USD_INR.toFixed(2)}</p>
                       </div>
                       <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-4 text-center">
                         <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Global Gold</p>
                         <p className="text-lg font-bold text-gray-900 font-mono tracking-tight">${macroData.Gold_Futures_USD.toFixed(0)}</p>
                       </div>
                     </div>
                   )}

                   {/* News Sentiment Widget */}
                   {newsData?.summary && (
                     <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
                       <div className="flex justify-between items-center mb-4">
                         <h3 className="font-bold text-gray-900 text-sm">News Sentiment</h3>
                         <span className={`text-xs font-bold px-2 py-1 rounded-md ${newsData.sentiment === 'Bullish' ? 'bg-emerald-50 text-emerald-600' : newsData.sentiment === 'Bearish' ? 'bg-rose-50 text-rose-600' : 'bg-yellow-50 text-yellow-600'}`}>
                           {newsData.sentiment}
                         </span>
                       </div>
                       <p className="text-xs text-gray-500 leading-relaxed line-clamp-4">
                         {newsData.summary}
                       </p>
                     </div>
                   )}

                   {/* Anomaly Widget */}
                   {intelligenceData?.anomalies?.anomaly_detected && (
                     <div className="bg-red-50 rounded-2xl border border-red-100 shadow-sm p-6">
                       <div className="flex items-center mb-3 text-red-600">
                         <AlertTriangle className="w-5 h-5 mr-2" />
                         <h3 className="font-bold text-sm">Anomaly Detected</h3>
                       </div>
                       <div className="space-y-2">
                         {intelligenceData.anomalies.anomalies.map((a, i) => (
                           <p key={i} className="text-xs text-red-600/80 font-medium">{a.message}</p>
                         ))}
                       </div>
                     </div>
                   )}

                </motion.div>
              </div>

              {/* Personal Tracker Form Container (Bottom) */}
              <motion.div variants={{ hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0, transition: { duration: 0.4, ease: "easeOut" } } }} className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 mt-8">
                 <h2 className="text-xl font-bold mb-6 text-gray-900">Manage Portfolio</h2>
                 <form onSubmit={handleSavePortfolio} className="flex flex-col sm:flex-row items-end space-y-4 sm:space-y-0 sm:space-x-6">
                  <div className="flex-1 w-full">
                    <label className="block text-sm font-semibold text-gray-500 mb-2">Total Invested (₹)</label>
                    <input 
                      type="number" 
                      value={totalInvestedInput} 
                      onChange={(e) => setTotalInvestedInput(e.target.value)}
                      className="w-full bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 text-gray-900 focus:outline-none focus:ring-2 focus:ring-[#5A67D8]/50 focus:border-[#5A67D8] transition-all font-mono"
                      placeholder="e.g. 50000"
                    />
                  </div>
                  <div className="flex-1 w-full">
                    <label className="block text-sm font-semibold text-gray-500 mb-2">Total Units</label>
                    <input 
                      type="number" 
                      value={units} 
                      onChange={(e) => setUnits(e.target.value)}
                      className="w-full bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 text-gray-900 focus:outline-none focus:ring-2 focus:ring-[#5A67D8]/50 focus:border-[#5A67D8] transition-all font-mono"
                      placeholder="e.g. 400"
                    />
                  </div>
                  <button 
                    type="submit" 
                    className="w-full sm:w-auto bg-[#5A67D8] hover:bg-indigo-700 text-white font-bold py-3 px-8 rounded-xl transition-colors shadow-sm"
                  >
                    Save Portfolio
                  </button>
                 </form>
              </motion.div>

            </motion.div>
          )}

          {activeTab === 'ailab' && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
              
              {/* Multi Agent System */}
              {agentsData && (
                <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
                  <h2 className="text-xl font-bold flex items-center text-gray-900 mb-6">
                    <Users className="mr-2 text-indigo-500 w-6 h-6" /> Multi-Agent AI Decision System
                  </h2>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                    {agentsData.sub_agents.map((agent, i) => (
                      <div key={i} className="bg-gray-50 p-4 rounded-xl border border-gray-200 flex flex-col items-center text-center">
                        <p className="text-sm font-bold text-gray-700 mb-2">{agent.agent}</p>
                        <div className={`px-4 py-1.5 rounded-full text-xs font-bold mb-3 border ${
                          agent.signal === 'BUY' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 
                          agent.signal === 'SELL' ? 'bg-rose-50 text-rose-700 border-rose-200' : 
                          'bg-gray-100 text-gray-500 border-gray-200'
                        }`}>
                          {agent.signal} ({agent.confidence}%)
                        </div>
                        <p className="text-xs text-gray-500 leading-relaxed">{agent.reason}</p>
                      </div>
                    ))}
                  </div>

                  <div className="bg-[#EEF2FF] border border-indigo-100 p-6 rounded-xl flex flex-col md:flex-row items-center justify-between">
                    <div>
                      <p className="text-sm font-bold text-indigo-900 mb-1">Chief Investment AI Final Consensus</p>
                      <p className="text-xs text-indigo-700 font-medium">Aggregated vote consensus from specialized agents.</p>
                    </div>
                    <div className="mt-4 md:mt-0 flex items-center space-x-6">
                      <div className="text-right">
                        <p className="text-xs text-gray-400 uppercase tracking-wider mb-1">Confidence</p>
                        <p className="text-xl font-bold text-gray-900">{agentsData.confidence}%</p>
                      </div>
                      <div className={`px-6 py-3 rounded-xl text-2xl font-bold border ${
                        agentsData.final_signal === 'BUY' ? 'bg-emerald-500 text-white border-emerald-600' : 
                        agentsData.final_signal === 'SELL' ? 'bg-red-500 text-white border-red-600' : 
                        'bg-gray-500 text-white border-gray-600'
                      }`}>
                        {agentsData.final_signal}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* PPO Agent & Explainability */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                
                <div className="lg:col-span-2 space-y-6">
                  {rlData && (
                    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
                      <h2 className="text-xl font-bold flex items-center text-gray-900 mb-6">
                        <Cpu className="mr-2 text-indigo-500 w-6 h-6" /> Local RL Agent (PPO)
                      </h2>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="bg-gray-50 p-4 rounded-xl border border-gray-200">
                          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Cumulative Reward</p>
                          <p className="text-2xl font-bold text-emerald-600 font-mono">+₹{rlData.cumulative_reward.toLocaleString()}</p>
                        </div>
                        <div className="bg-gray-50 p-4 rounded-xl border border-gray-200">
                          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Episodes Trained</p>
                          <p className="text-2xl font-bold text-gray-900 font-mono">{rlData.episodes_trained.toLocaleString()}</p>
                        </div>
                        <div className="bg-gray-50 p-4 rounded-xl border border-gray-200 col-span-2">
                          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Policy Action</p>
                          <div className="flex justify-between items-center">
                            <span className={`text-xl font-bold ${rlData.current_action === 'BUY' ? 'text-emerald-500' : rlData.current_action === 'SELL' ? 'text-red-500' : 'text-gray-500'}`}>
                              {rlData.current_action} ({rlData.action_confidence}%)
                            </span>
                            <span className="text-xs text-gray-400 font-mono">Loss (P/V): {rlData.metrics.policy_loss}/{rlData.metrics.value_loss}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* SHAP explainability */}
                  {intelligenceData?.shap?.top_features?.length > 0 && (
                    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
                      <h2 className="text-xl font-bold flex items-center text-gray-900 mb-2">
                        <Info className="mr-2 text-indigo-500 w-6 h-6" /> Why this Prediction?
                      </h2>
                      <p className="text-xs text-gray-400 mb-6">Top technical features driving today's AI forecast models.</p>
                      <div className="space-y-4">
                        {intelligenceData.shap.top_features.map((f, i) => (
                          <div key={i}>
                            <div className="flex justify-between text-xs mb-1">
                              <span className="text-gray-700 font-semibold uppercase">{f.feature.replace(/_/g, ' ')}</span>
                              <span className={f.direction === 'positive' ? 'text-emerald-500 font-bold' : 'text-red-500 font-bold'}>
                                {f.direction === 'positive' ? '+' : '-'}{f.percentage}%
                              </span>
                            </div>
                            <div className="w-full bg-gray-100 rounded-full h-2">
                              <div className={`h-2 rounded-full ${f.direction === 'positive' ? 'bg-emerald-500' : 'bg-red-500'}`} style={{ width: `${f.percentage}%` }} />
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Right: Signals List */}
                <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 h-fit">
                   <h2 className="text-lg font-bold text-gray-900 mb-6">Signals Console</h2>
                   {latestSignal ? (
                     <div className="bg-gray-50 border border-gray-200 rounded-xl p-4 text-center mb-6">
                        <p className="text-xs text-gray-400 font-semibold uppercase tracking-wider mb-2">Consensus Signal</p>
                        <div className="mb-4">{renderSignalBadge(latestSignal.Action)}</div>
                        <div className="text-left bg-white border border-gray-100 rounded-lg p-3 text-xs text-gray-500">
                          <p className="font-bold text-gray-700 mb-1 flex items-center"><Info className="w-3 h-3 mr-1"/> Recommendation Detail:</p>
                          <p className="italic leading-relaxed">{aiReasoning || "Fetching reasoning..."}</p>
                        </div>
                     </div>
                   ) : <p className="text-gray-400 text-sm">Loading signals...</p>}
                   
                   <div className="space-y-2">
                      <p className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Recent AI Decisions</p>
                      {signals.slice(0, 5).reverse().map((sig, idx) => (
                        <div key={idx} className="flex justify-between items-center text-xs p-3 bg-gray-50 border border-gray-100 rounded-xl">
                          <span className="text-gray-500 font-medium">{String(sig.Date).split(' ')[0]}</span>
                          {renderSignalBadge(sig.Action)}
                        </div>
                      ))}
                   </div>
                </div>

              </div>

            </motion.div>
          )}

          {activeTab === 'simulation' && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
              
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                
                <div className="lg:col-span-2 space-y-6">
                  
                  {/* Strategy Backtester */}
                  <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
                     <h2 className="text-xl font-bold flex items-center text-gray-900 mb-4">
                       <PlayCircle className="mr-2 text-indigo-500 w-6 h-6" /> Backtest AI Strategy vs Market
                     </h2>
                     <p className="text-sm text-gray-500 mb-6">Evaluate returns of an AI agent dynamically executing trades compared to simple holding.</p>
                     
                     {backtestMetrics ? (
                       <div className="grid grid-cols-2 gap-4 mb-6">
                         <div className="bg-gray-50 p-4 rounded-xl border border-gray-200 text-center">
                           <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider block mb-1">Buy & Hold ROI</span>
                           <span className="text-xl font-bold font-mono text-gray-900">{backtestMetrics.Market_ROI_Percent.toFixed(2)}%</span>
                         </div>
                         <div className="bg-emerald-50 p-4 rounded-xl border border-emerald-100 text-center">
                           <span className="text-xs font-semibold text-emerald-600 uppercase tracking-wider block mb-1">AI Strategy ROI</span>
                           <span className="text-xl font-bold font-mono text-emerald-600">{backtestMetrics.Strategy_ROI_Percent.toFixed(2)}%</span>
                         </div>
                       </div>
                     ) : null}

                     <button 
                       onClick={handleRunBacktest} disabled={isBacktesting}
                       className="w-full bg-[#5A67D8] hover:bg-indigo-700 text-white font-bold py-3 rounded-xl transition-all shadow-sm flex justify-center items-center disabled:opacity-50"
                     >
                       {isBacktesting ? "Simulating Strategy..." : "Run Historical Vectorized Backtest"}
                     </button>
                  </div>

                  {/* Strategy Rules Builder */}
                  <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
                    <h2 className="text-xl font-bold flex items-center text-gray-900 mb-4">
                      <Activity className="mr-2 text-indigo-500 w-6 h-6" /> Custom Strategy Builder
                    </h2>
                    <p className="text-sm text-gray-500 mb-6">Define conditions for executing trades. Simulator backtests matching dates.</p>
                    <div className="space-y-4">
                      {strategyRules.map((rule, i) => (
                        <div key={i} className="flex flex-col sm:flex-row flex-wrap gap-4 items-center bg-gray-50 border border-gray-200 p-4 rounded-xl w-full">
                          <select className="bg-white text-gray-700 rounded-xl p-2.5 border border-gray-200 w-full sm:w-auto focus:outline-none focus:ring-2 focus:ring-[#5A67D8]" value={rule.indicator} onChange={e => handleUpdateRule(i, 'indicator', e.target.value)}>
                            <option value="RSI">RSI</option>
                            <option value="MACD">MACD</option>
                            <option value="ADX">ADX</option>
                            <option value="Close">Close Price</option>
                            <option value="SMA_20">SMA 20</option>
                            <option value="SMA_50">SMA 50</option>
                          </select>
                          <select className="bg-white text-gray-700 rounded-xl p-2.5 border border-gray-200 w-full sm:w-auto focus:outline-none focus:ring-2 focus:ring-[#5A67D8]" value={rule.operator} onChange={e => handleUpdateRule(i, 'operator', e.target.value)}>
                            <option value=">">&gt;</option>
                            <option value="&lt;">&lt;</option>
                            <option value=">=">&gt;=</option>
                            <option value="&lt;=">&lt;=</option>
                            <option value="==">==</option>
                          </select>
                          <input type="number" className="bg-white text-gray-700 rounded-xl p-2.5 border border-gray-200 w-full sm:w-28 focus:outline-none focus:ring-2 focus:ring-[#5A67D8] font-mono" value={rule.value === undefined || isNaN(rule.value) ? '' : rule.value} onChange={e => handleUpdateRule(i, 'value', e.target.value === '' ? '' : parseFloat(e.target.value))} />
                          <button onClick={() => handleRemoveRule(i)} className="text-red-500 hover:text-red-700 ml-auto font-bold">&times; Remove</button>
                        </div>
                      ))}
                      
                      <div className="flex justify-between items-center mt-6">
                        <button onClick={handleAddRule} className="text-sm text-gray-500 hover:text-indigo-600 font-bold">+ Add Rule Condition</button>
                        <button onClick={runStrategyBacktest} disabled={isBacktesting} className="bg-[#5A67D8] hover:bg-indigo-700 text-white px-6 py-2.5 rounded-xl font-bold transition-all shadow-sm disabled:opacity-50">
                          {isBacktesting ? "Simulating Rules..." : "Backtest Strategy"}
                        </button>
                      </div>

                      {backtestResult && (
                        <div className="mt-6 pt-6 border-t border-gray-100 grid grid-cols-3 gap-4">
                          <div className="bg-gray-50 border border-gray-200 p-4 rounded-xl text-center">
                            <p className="text-xs text-gray-400 uppercase tracking-wider mb-1">Win Rate</p>
                            <p className={`text-xl font-bold ${backtestResult.win_rate > 50 ? 'text-emerald-500' : 'text-red-500'}`}>{backtestResult.win_rate}%</p>
                          </div>
                          <div className="bg-gray-50 border border-gray-200 p-4 rounded-xl text-center">
                            <p className="text-xs text-gray-400 uppercase tracking-wider mb-1">Total Return</p>
                            <p className={`text-xl font-bold ${backtestResult.total_return > 0 ? 'text-emerald-500' : 'text-red-500'}`}>{backtestResult.total_return}%</p>
                          </div>
                          <div className="bg-gray-50 border border-gray-200 p-4 rounded-xl text-center">
                            <p className="text-xs text-gray-400 uppercase tracking-wider mb-1">Total Trades</p>
                            <p className="text-xl font-bold text-gray-900">{backtestResult.total_trades}</p>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Leaderboard Table */}
                  <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
                    <h2 className="text-xl font-bold flex items-center text-gray-900 mb-6">
                      <Trophy className="mr-2 text-indigo-500 w-6 h-6" /> AI Model Leaderboard
                    </h2>
                    <div className="overflow-x-auto">
                      <table className="w-full text-left border-collapse">
                        <thead>
                          <tr className="border-b border-gray-100 text-sm text-gray-400">
                            <th className="p-3 font-semibold">Rank</th>
                            <th className="p-3 font-semibold">Model Name</th>
                            <th className="p-3 font-semibold">RMSE Error</th>
                            <th className="p-3 font-semibold">Accuracy</th>
                          </tr>
                        </thead>
                        <tbody>
                          {leaderboard.map((row, idx) => (
                            <tr key={idx} className="border-b border-gray-50 hover:bg-gray-50/50 transition-colors">
                              <td className="p-3 font-mono text-gray-400">#{idx + 1}</td>
                              <td className="p-3 font-semibold text-gray-700">{row.Model}</td>
                              <td className="p-3 font-mono text-emerald-600 font-bold">{row.RMSE.toFixed(4)}</td>
                              <td className="p-3 font-mono text-emerald-500 font-bold">{(row.Directional_Accuracy * 100).toFixed(1)}%</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                </div>

                <div className="space-y-6 h-fit">
                   
                   {/* Custom date predict */}
                   <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
                      <h2 className="text-lg font-bold flex items-center text-gray-900 mb-4">
                        <Calendar className="mr-2 text-indigo-500 w-5 h-5" /> Predict Custom Date
                      </h2>
                      <div className="space-y-4">
                        <input 
                          type="date" 
                          value={customDate}
                          onChange={(e) => setCustomDate(e.target.value)}
                          className="w-full bg-gray-50 border border-gray-200 text-gray-900 rounded-xl px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-[#5A67D8] font-mono"
                        />
                        <button 
                          onClick={handleCustomForecast} disabled={isFetchingCustom || !customDate}
                          className="w-full bg-[#5A67D8] hover:bg-indigo-700 text-white font-bold py-2.5 rounded-xl shadow-sm transition-colors disabled:opacity-50"
                        >
                          {isFetchingCustom ? "Calculating..." : "Predict Price"}
                        </button>
                        {customForecast && (
                          <div className="mt-4 p-4 bg-gray-50 rounded-xl border border-gray-200 text-center">
                            <p className="text-xs text-gray-400 uppercase tracking-wider mb-1 font-semibold">Predicted Close</p>
                            <p className="text-2xl font-bold font-mono text-emerald-500">₹{customForecast.Projected_Price.toFixed(2)}</p>
                          </div>
                        )}
                      </div>
                   </div>

                   {/* History Pattern Match */}
                   {wave2Data?.similar_days?.similar_date && (
                     <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
                        <h2 className="text-lg font-bold flex items-center text-gray-900 mb-4">
                          <Calendar className="mr-2 text-indigo-500 w-5 h-5" /> Historical Matcher
                        </h2>
                        <p className="text-xs text-gray-400 mb-4 font-medium">Technicals mimic historical match:</p>
                        <div className="text-center py-4 bg-gray-50 rounded-xl border border-gray-200 mb-4">
                          <p className="text-xl font-bold font-mono text-emerald-500">{wave2Data.similar_days.similar_date}</p>
                          <p className="text-xs text-gray-400 mt-1 font-semibold">{wave2Data.similar_days.similarity_score}% correlation</p>
                        </div>
                        <div className="p-3 bg-gray-50 rounded-xl border border-gray-200 text-center">
                          <p className="text-xs text-gray-400 mb-1">Subsequent 30D return</p>
                          <p className={`text-lg font-bold ${wave2Data.similar_days.outcome_pct > 0 ? 'text-emerald-500' : 'text-red-500'}`}>
                            {wave2Data.similar_days.outcome_pct > 0 ? '+' : ''}{wave2Data.similar_days.outcome_pct}%
                          </p>
                        </div>
                     </div>
                   )}

                   {/* What-if Simulator */}
                   <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
                      <h2 className="text-lg font-bold flex items-center text-gray-900 mb-4">
                        <Activity className="mr-2 text-indigo-500 w-5 h-5" /> What-If Simulator
                      </h2>
                      <div className="space-y-4">
                        <div className="flex space-x-2">
                          <select 
                            value={simVariable} 
                            onChange={e => setSimVariable(e.target.value)}
                            className="bg-gray-50 border border-gray-200 text-gray-700 rounded-xl p-2.5 w-2/3 focus:outline-none focus:ring-2 focus:ring-[#5A67D8]"
                          >
                            <option value="USD_INR">USD/INR Rate</option>
                            <option value="Gold_Spot">Spot Gold Price</option>
                            <option value="Volume">Exchange Volume</option>
                          </select>
                          <input 
                            type="number" 
                            value={simChange} 
                            onChange={e => setSimChange(e.target.value)}
                            placeholder="% Chg" 
                            className="bg-gray-50 border border-gray-200 text-gray-900 rounded-xl p-2.5 w-1/3 focus:outline-none focus:ring-2 focus:ring-[#5A67D8] font-mono"
                          />
                        </div>
                        <button 
                          onClick={handleSimulate} 
                          disabled={isSimulating}
                          className="w-full bg-[#5A67D8] hover:bg-[#4C51BF] text-white font-bold py-2.5 rounded-xl transition-all shadow-sm"
                        >
                          {isSimulating ? 'Simulating...' : 'Simulate Change'}
                        </button>
                        {simResult && (
                          <div className="p-4 bg-gray-50 border border-gray-200 rounded-xl text-center">
                            <p className="text-xs text-gray-400 mb-1 font-semibold">Simulated Outcome Price</p>
                            <p className="text-2xl font-bold font-mono text-gray-900">₹{simResult.new_expected.toFixed(2)}</p>
                            <p className={`text-sm mt-1 font-bold ${simResult.impact_pct > 0 ? 'text-emerald-500' : 'text-red-500'}`}>
                              {simResult.impact_pct > 0 ? '+' : ''}{simResult.impact_pct.toFixed(2)}% Impact
                            </p>
                          </div>
                        )}
                      </div>
                   </div>

                   {/* Probability Dist Heatmap */}
                   {wave2Data?.probability_distribution?.distribution && (
                      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
                        <h2 className="text-lg font-bold flex items-center text-gray-900 mb-4">
                          <BarChart2 className="mr-2 text-indigo-500 w-5 h-5" /> Probability Map
                        </h2>
                        <div className="space-y-3 mt-4">
                          {wave2Data.probability_distribution.distribution.map((bin, i) => (
                            <div key={i} className="flex items-center text-xs">
                              <div className="w-16 text-gray-500 font-mono">₹{bin.price.toFixed(1)}</div>
                              <div className="flex-1 bg-gray-100 rounded-full h-3 mx-3">
                                <div 
                                  className={`h-3 rounded-full ${bin.probability > 30 ? 'bg-[#5A67D8]' : 'bg-indigo-300'}`} 
                                  style={{ width: `${Math.max(bin.probability, 2)}%` }}
                                />
                              </div>
                              <div className="w-10 text-right text-gray-500 font-mono">{bin.probability.toFixed(0)}%</div>
                            </div>
                          ))}
                        </div>
                      </div>
                   )}

                </div>

              </div>

            </motion.div>
          )}

        </div>
      </main>

      {/* Floating Chatbot */}
      <div className="fixed bottom-6 right-6 z-50">
        {isChatOpen ? (
          <div className="bg-white border border-gray-100 shadow-2xl w-80 h-96 rounded-2xl flex flex-col overflow-hidden">
            <div className="bg-[#5A67D8] p-4 text-white flex justify-between items-center cursor-pointer shadow-sm" onClick={() => setIsChatOpen(false)}>
              <span className="font-bold flex items-center"><MessageCircle className="w-5 h-5 mr-2" /> AI Assistant</span>
              <span className="text-indigo-200 hover:text-white">&times;</span>
            </div>
            <div className="flex-1 p-4 overflow-y-auto space-y-3 bg-gray-50">
              {chatMessages.map((msg, i) => (
                <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`p-2.5 max-w-[85%] rounded-xl text-sm ${msg.role === 'user' ? 'bg-[#5A67D8] text-white rounded-br-none' : 'bg-white border border-gray-100 text-gray-700 rounded-bl-none shadow-sm'}`}>
                    {msg.text}
                  </div>
                </div>
              ))}
            </div>
            <div className="p-3 border-t border-gray-100 flex bg-white">
              <input 
                type="text" 
                value={chatInput}
                onChange={e => setChatInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleSendChat()}
                placeholder="Ask about your portfolio..."
                className="flex-1 bg-gray-50 border border-gray-200 text-gray-700 text-sm rounded-l-xl p-2.5 focus:outline-none focus:ring-2 focus:ring-[#5A67D8]/50"
              />
              <button 
                onClick={handleSendChat}
                className="bg-[#5A67D8] hover:bg-indigo-700 text-white px-4 rounded-r-xl font-bold"
              >
                Send
              </button>
            </div>
          </div>
        ) : (
          <button 
            onClick={() => setIsChatOpen(true)}
            className="w-14 h-14 bg-[#5A67D8] rounded-full shadow-2xl flex items-center justify-center text-white hover:scale-110 transition-transform shadow-indigo-500/30"
          >
            <MessageCircle className="w-6 h-6" />
          </button>
        )}
      </div>

      {/* Auth Modal */}
      {showAuthModal && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-6 w-full max-w-sm shadow-xl relative border border-gray-100">
            <button 
              onClick={() => setShowAuthModal(false)}
              className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 text-xl font-bold"
            >
              &times;
            </button>
            <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">
              {authMode === 'login' ? 'Welcome Back' : 'Create Account'}
            </h2>
            <form onSubmit={handleAuthSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-gray-500 mb-1">Username</label>
                <input 
                  type="text" 
                  value={authUsername}
                  onChange={e => setAuthUsername(e.target.value)}
                  className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#5A67D8] text-gray-900"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-500 mb-1">Password</label>
                <input 
                  type="password" 
                  value={authPassword}
                  onChange={e => setAuthPassword(e.target.value)}
                  className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#5A67D8] text-gray-900"
                  required
                />
              </div>
              <button 
                type="submit" 
                className="w-full bg-[#5A67D8] hover:bg-indigo-700 text-white font-bold py-3 rounded-xl transition-colors shadow-sm mt-4"
              >
                {authMode === 'login' ? 'Sign In' : 'Sign Up'}
              </button>
            </form>
            <div className="mt-4 text-center text-sm text-gray-500">
              {authMode === 'login' ? "Don't have an account? " : "Already have an account? "}
              <button 
                onClick={() => setAuthMode(authMode === 'login' ? 'register' : 'login')}
                className="text-[#5A67D8] font-bold hover:underline"
              >
                {authMode === 'login' ? 'Register' : 'Login'}
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );'''

# Replace from "return (" to the end of the file with the new JSX code
code = code[:start_idx] + new_jsx

with open('src/app/page.js', 'w', encoding='utf-8') as f:
    f.write(code)

print("Layout merged successfully!")
