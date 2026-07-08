const x = () => { 
  return (
    <div className="min-h-screen bg-[#F4F6F8] text-gray-900 font-sans flex overflow-hidden">
      <Toaster position="top-right" toastOptions={{
        style: { background: '#FFFFFF', color: '#111827', border: '1px solid #E5E7EB', borderRadius: '12px', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)' }
      }} />

      {/* LEFT SIDEBAR */}
      <aside className="w-64 bg-white border-r border-gray-100 flex flex-col hidden md:flex z-30 shadow-sm relative">
        <div className="p-6">
          <h1 className="text-2xl font-bold flex items-center tracking-tight text-gray-900">
            <div className="w-8 h-8 bg-[#5A67D8] rounded-lg mr-3 flex items-center justify-center text-white font-black">K</div>
            Kryptosan
          </h1>
        </div>
        <div className="px-6 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Main Menu</div>
        <nav className="flex-1 px-4 space-y-1">
          <div 
            onClick={() => setActiveTab('overview')}
            className={`flex items-center px-4 py-3 rounded-xl font-medium cursor-pointer transition-all ${activeTab === 'overview' ? 'bg-[#EEF2FF] text-[#5A67D8]' : 'text-gray-500 hover:bg-gray-50 hover:text-gray-900'}`}
          >
            <Home className="w-5 h-5 mr-3" /> Dashboard
          </div>
          <div 
            onClick={() => setActiveTab('ailab')}
            className={`flex items-center px-4 py-3 rounded-xl font-medium cursor-pointer transition-all ${activeTab === 'ailab' ? 'bg-[#EEF2FF] text-[#5A67D8]' : 'text-gray-500 hover:bg-gray-50 hover:text-gray-900'}`}
          >
            <Cpu className="w-5 h-5 mr-3" /> AI Lab
          </div>
          <div 
            onClick={() => setActiveTab('risk')}
            className={`flex items-center px-4 py-3 rounded-xl font-medium cursor-pointer transition-all ${activeTab === 'risk' ? 'bg-[#EEF2FF] text-[#5A67D8]' : 'text-gray-500 hover:bg-gray-50 hover:text-gray-900'}`}
          >
            <ShieldCheck className="w-5 h-5 mr-3" /> Risk Console
          </div>
        </nav>
        
        {/* Promo banner at bottom */}
        <div className="p-5 m-4 bg-[#5A67D8] text-white rounded-2xl relative overflow-hidden shadow-lg shadow-indigo-500/30">
          <div className="absolute top-0 right-0 w-24 h-24 bg-white opacity-10 rounded-full -mr-10 -mt-10 blur-xl"></div>
          <p className="text-sm font-semibold mb-1">Transfer crypto into Kryptosan, It's Free!</p>
          <button className="mt-3 px-4 py-1.5 bg-white text-[#5A67D8] text-xs font-bold rounded-lg shadow-sm hover:shadow-md transition-shadow">Try for free</button>
        </div>
        
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
             <Calendar className="w-4 h-4 mr-2" /> Today's Stocks
           </div>
           
           <div className="flex items-center space-x-6">
             {userId ? (
               <button onClick={handleLogout} className="text-sm text-red-500 font-medium hover:text-red-600">Log Out</button>
             ) : (
               <button onClick={() => setShowAuthModal(true)} className="text-sm text-[#5A67D8] font-bold hover:text-indigo-700 bg-indigo-50 px-4 py-2 rounded-lg">Log In / Register</button>
             )}
             <div className="w-px h-6 bg-gray-200"></div>
             <Search className="w-5 h-5 text-gray-400 cursor-pointer hover:text-gray-600 transition-colors" />
             <div className="flex items-center text-sm font-semibold text-gray-700 cursor-pointer hover:text-gray-900 transition-colors">
               English <span className="text-gray-400 font-normal ml-1">(USD)</span> <ChevronDown className="w-4 h-4 ml-1 text-gray-400"/>
             </div>
             <div className="flex items-center space-x-3 cursor-pointer">
               <div className="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center border-2 border-white shadow-sm overflow-hidden">
                  <span className="text-gray-500 font-bold text-xs">U</span>
               </div>
               <div className="hidden sm:block text-sm font-bold text-gray-700">{userId || "Guest"}</div>
             </div>
           </div>
        </header>

        {/* DASHBOARD CONTENT */}
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
                    <p className="text-sm font-semibold text-gray-500 mb-2">Total Balance</p>
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
                       <h2 className="text-4xl font-bold text-gray-900 font-mono tracking-tight">{parsedUnits || 0} <span className="text-lg text-gray-400">UNITS</span></h2>
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
                          {['1D', '1M', 'YTD', '1Y', 'MAX'].map(tf => (
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
                     <div className="flex space-x-3">
                       <button className="px-6 py-2 bg-[#5A67D8] text-white text-sm font-bold rounded-xl shadow-sm hover:bg-indigo-700 hover:shadow-md transition-all">Buy Now</button>
                       <button className="px-6 py-2 bg-white text-gray-700 border border-gray-200 text-sm font-bold rounded-xl shadow-sm hover:bg-gray-50 transition-all">Sell Now</button>
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

          {activeTab !== 'overview' && (
             <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex items-center justify-center h-64 bg-white rounded-2xl border border-gray-100 shadow-sm">
                <p className="text-gray-400 font-medium">This module is under construction in the Kryptosan theme.</p>
             </motion.div>
          )}

        </div>
      </main>

      {/* Auth Modal (Preserved logic, updated styles) */}
      {showAuthModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/40 backdrop-blur-sm px-4">
          <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="bg-white rounded-2xl shadow-xl w-full max-w-md overflow-hidden border border-gray-100">
            <div className="p-8">
              <h2 className="text-2xl font-bold mb-6 text-gray-900">{authMode === 'login' ? 'Welcome Back' : 'Create Account'}</h2>
              <form onSubmit={handleAuth} className="space-y-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-500 mb-2">Username</label>
                  <input required type="text" value={username} onChange={e=>setUsername(e.target.value)} className="w-full bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 text-gray-900 focus:outline-none focus:ring-2 focus:ring-[#5A67D8]" />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-500 mb-2">Password</label>
                  <input required type="password" value={password} onChange={e=>setPassword(e.target.value)} className="w-full bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 text-gray-900 focus:outline-none focus:ring-2 focus:ring-[#5A67D8]" />
                </div>
                <button type="submit" disabled={authLoading} className="w-full bg-[#5A67D8] hover:bg-indigo-700 text-white font-bold py-3 rounded-xl transition-colors shadow-sm disabled:opacity-70 mt-2">
                  {authLoading ? 'Processing...' : (authMode === 'login' ? 'Log In' : 'Register')}
                </button>
              </form>
              <div className="mt-6 text-center">
                <button type="button" onClick={() => setAuthMode(authMode==='login'?'register':'login')} className="text-[#5A67D8] text-sm font-semibold hover:underline">
                  {authMode === 'login' ? 'Need an account? Register' : 'Already have an account? Log in'}
                </button>
              </div>
            </div>
            <div className="bg-gray-50 p-4 border-t border-gray-100 flex justify-end">
              <button onClick={() => setShowAuthModal(false)} className="text-gray-500 hover:text-gray-900 text-sm font-bold px-4 py-2">Close</button>
            </div>
          </motion.div>
        </div>
      )}

    </div>
  );
}
