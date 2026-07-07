import re

def update_frontend():
    with open('d:/Goldbees/frontend/src/app/page.js', 'r', encoding='utf-8') as f:
        content = f.read()
        
    # 1. Add state for Strategy Builder
    state_injection = """
  const [strategyRules, setStrategyRules] = useState([{ indicator: 'RSI', operator: '<', value: 30 }]);
  const [backtestResult, setBacktestResult] = useState(null);
  const [isBacktesting, setIsBacktesting] = useState(false);

  const handleAddRule = () => {
    setStrategyRules([...strategyRules, { indicator: 'RSI', operator: '<', value: 30 }]);
  };

  const handleUpdateRule = (index, field, value) => {
    const newRules = [...strategyRules];
    newRules[index][field] = value;
    setStrategyRules(newRules);
  };

  const handleRemoveRule = (index) => {
    const newRules = [...strategyRules];
    newRules.splice(index, 1);
    setStrategyRules(newRules);
  };

  const runStrategyBacktest = async () => {
    setIsBacktesting(true);
    try {
      const response = await fetch('http://localhost:8000/backtest_strategy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rules: strategyRules })
      });
      const res = await response.json();
      if (res.status === 'success') {
        setBacktestResult(res.data);
      }
    } catch (err) {
      console.error(err);
    }
    setIsBacktesting(false);
  };
"""
    if "const [strategyRules" not in content:
        # Inject after `const [isFetchingCustom`
        content = content.replace("const [isFetchingCustom, setIsFetchingCustom] = useState(false);",
                                  "const [isFetchingCustom, setIsFetchingCustom] = useState(false);\n" + state_injection)
                                  
    # 2. Add the UI for Strategy Builder inside the simulation tab.
    ui_injection = """
      {/* Strategy Builder Widget */}
      <div className="bg-gray-900 border border-gray-800 rounded-2xl shadow-lg p-6 mb-8 mt-8">
        <h2 className="text-xl font-semibold mb-4 flex items-center text-gray-200">
          <Activity className="mr-2 text-purple-500 w-6 h-6" /> Custom Strategy Builder
        </h2>
        <div className="bg-gray-950 p-6 rounded-xl border border-gray-800 space-y-4">
          <p className="text-sm text-gray-400 mb-4">Define your buy conditions. The backtester will simulate buying on these days.</p>
          
          {strategyRules.map((rule, i) => (
            <div key={i} className="flex flex-wrap gap-4 items-center bg-gray-900 p-3 rounded-lg border border-gray-700">
              <select className="bg-gray-800 text-white rounded p-2 border border-gray-700" value={rule.indicator} onChange={e => handleUpdateRule(i, 'indicator', e.target.value)}>
                <option value="RSI">RSI</option>
                <option value="MACD">MACD</option>
                <option value="ADX">ADX</option>
                <option value="Close">Close Price</option>
                <option value="SMA_20">SMA 20</option>
                <option value="SMA_50">SMA 50</option>
              </select>
              <select className="bg-gray-800 text-white rounded p-2 border border-gray-700" value={rule.operator} onChange={e => handleUpdateRule(i, 'operator', e.target.value)}>
                <option value="<">&lt; (Less Than)</option>
                <option value=">">&gt; (Greater Than)</option>
                <option value="<=">&lt;=</option>
                <option value=">=">&gt;=</option>
              </select>
              <input type="number" className="bg-gray-800 text-white rounded p-2 border border-gray-700 w-24" value={rule.value} onChange={e => handleUpdateRule(i, 'value', parseFloat(e.target.value))} />
              <button onClick={() => handleRemoveRule(i)} className="text-red-400 hover:text-red-300 ml-auto font-bold">&times; Remove</button>
            </div>
          ))}
          
          <div className="flex justify-between items-center mt-4">
            <button onClick={handleAddRule} className="text-sm text-purple-400 hover:text-purple-300 font-semibold">+ Add Condition</button>
            <button onClick={runStrategyBacktest} disabled={isBacktesting} className="bg-purple-600 hover:bg-purple-500 text-white px-6 py-2 rounded-lg font-semibold transition-colors disabled:opacity-50">
              {isBacktesting ? "Simulating..." : "Run Backtest"}
            </button>
          </div>
          
          {backtestResult && (
            <div className="mt-6 pt-6 border-t border-gray-800 grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-gray-900 p-4 rounded-xl border border-gray-800 text-center">
                <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Win Rate</p>
                <p className={`text-2xl font-bold ${backtestResult.win_rate > 50 ? 'text-emerald-400' : 'text-red-400'}`}>{backtestResult.win_rate}%</p>
              </div>
              <div className="bg-gray-900 p-4 rounded-xl border border-gray-800 text-center">
                <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Total Return</p>
                <p className={`text-2xl font-bold ${backtestResult.total_return > 0 ? 'text-emerald-400' : 'text-red-400'}`}>{backtestResult.total_return}%</p>
              </div>
              <div className="bg-gray-900 p-4 rounded-xl border border-gray-800 text-center">
                <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Total Trades</p>
                <p className="text-2xl font-bold text-gray-200">{backtestResult.total_trades}</p>
              </div>
            </div>
          )}
        </div>
      </div>
"""
    
    # We will inject this before `{/* Leaderboard Table */}`
    if "Custom Strategy Builder" not in content:
        content = content.replace("{/* Leaderboard Table */}", ui_injection + "\n      {/* Leaderboard Table */}")
        
    with open('d:/Goldbees/frontend/src/app/page.js', 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    update_frontend()
