"use client";

import { useEffect, useState, useRef } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { 
  TrendingUp, TrendingDown, DollarSign, Activity, AlertCircle, RefreshCw, BarChart2, Zap, 
  Calendar, Info, Target, List, PlayCircle, Lock, Download, Globe, ShieldCheck, AlertTriangle, MessageCircle, ArrowUpRight, Briefcase, Users, Cpu, Trophy
} from 'lucide-react';
import toast, { Toaster } from 'react-hot-toast';
// Clerk removed - auth disabled for deployment
import dynamic from 'next/dynamic';

const ReactApexChart = dynamic(() => import('react-apexcharts'), { ssr: false });

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const WS_BASE_URL = API_BASE_URL.replace('http', 'ws');

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler);

export default function Dashboard() {
  // Existing States
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  
  // Custom Forecast States
  const [customDate, setCustomDate] = useState("");
  const [customForecast, setCustomForecast] = useState(null);
  const [isFetchingCustom, setIsFetchingCustom] = useState(false);

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
      const response = await fetch(`${API_BASE_URL}/backtest_strategy`, {
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

  
  // New Feature States
  const [signals, setSignals] = useState([]);
  const [leaderboard, setLeaderboard] = useState([]);
  const [backtestMetrics, setBacktestMetrics] = useState(null);

  const [macroData, setMacroData] = useState(null);
  const [intelligenceData, setIntelligenceData] = useState(null);
  
  // Wave 2 States
  const [wave2Data, setWave2Data] = useState(null);
  const [simVariable, setSimVariable] = useState('USD_INR');
  const [simChange, setSimChange] = useState(0);
  const [simResult, setSimResult] = useState(null);
  const [isSimulating, setIsSimulating] = useState(false);
  
  const [aiReasoning, setAiReasoning] = useState(null);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [chatMessages, setChatMessages] = useState([{ role: 'ai', text: 'Hello! I am your AI Trading Assistant. How can I help you today?' }]);
  const [chatInput, setChatInput] = useState('');
  
  // Wave 4 States
  const [newsData, setNewsData] = useState(null);

  // Wave 5 States
  const [agentsData, setAgentsData] = useState(null);

  // Wave 6 States
  const [rlData, setRlData] = useState(null);

  // Tab State
  const [activeTab, setActiveTab] = useState("overview");

  // Clerk Auth removed - using static userId
  const userId = null;

  // Portfolio States
  const [totalInvestedInput, setTotalInvestedInput] = useState("");
  const [units, setUnits] = useState("");

  const chartRef = useRef(null);

  const fetchDashboardData = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/dashboard`);
      const json = await res.json();
      if (json.status === "success") {
        setData(json.data);
      }
    } catch (err) {
      console.error("Failed to fetch dashboard data", err);
    } finally {
      setLoading(false);
    }
  };

  const fetchExtraFeatures = async () => {
    try {
      const sigRes = await fetch(`${API_BASE_URL}/signals?days=5`);
      const sigJson = await sigRes.json();
      if (sigJson.status === "success") setSignals(sigJson.data.signals);

      const ldRes = await fetch(`${API_BASE_URL}/models`);
      const ldJson = await ldRes.json();
      if (ldJson.status === "success") setLeaderboard(ldJson.data.leaderboard);

      const macroRes = await fetch(`${API_BASE_URL}/macro`);
      const macroJson = await macroRes.json();
      if (macroJson.status === "success") setMacroData(macroJson.data);

      const intellRes = await fetch(`${API_BASE_URL}/intelligence`);
      const intellJson = await intellRes.json();
      if (intellJson.status === "success") setIntelligenceData(intellJson.data);

      const wave2Res = await fetch(`${API_BASE_URL}/wave2_data`);
      const wave2Json = await wave2Res.json();
      if (wave2Json.status === "success") setWave2Data(wave2Json.data);

      const newsRes = await fetch(`${API_BASE_URL}/news`);
      const newsJson = await newsRes.json();
      if (newsJson.status === "success") setNewsData(newsJson.data);

      const agentsRes = await fetch(`${API_BASE_URL}/agents`);
      const agentsJson = await agentsRes.json();
      if (agentsJson.status === "success") setAgentsData(agentsJson.data);

      const rlRes = await fetch(`${API_BASE_URL}/rl_status`);
      const rlJson = await rlRes.json();
      if (rlJson.status === "success") setRlData(rlJson.data);
    } catch (err) {
      console.error("Failed to fetch extra features", err);
    }
  };

  // Portfolio Database Syncing
  useEffect(() => {
    if (!userId) return;
    
    // Fetch Portfolio on login
    fetch(`${API_BASE_URL}/portfolio/${userId}`)
      .then(res => res.json())
      .then(json => {
        if (json.status === "success" && json.data && json.data.total_invested !== undefined) {
          setTotalInvestedInput(json.data.total_invested.toString());
          setUnits(json.data.units.toString());
        }
      })
      .catch(err => console.error("Failed to fetch portfolio", err));
  }, [userId]);

  useEffect(() => {
    // Auto-save portfolio when changed, debounced
    if (!userId || !totalInvestedInput || !units) return;
    
    const delayDebounceFn = setTimeout(() => {
      fetch(`${API_BASE_URL}/portfolio`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          clerk_user_id: userId,
          total_invested: parseFloat(totalInvestedInput) || 0,
          units: parseFloat(units) || 0
        })
      }).catch(err => console.error("Failed to save portfolio", err));
    }, 1000);

    return () => clearTimeout(delayDebounceFn);
  }, [totalInvestedInput, units, userId]);

  const fetchAIReasoning = async (signal, price, rsi, macd) => {
    try {
      setAiReasoning("Analyzing...");
      const res = await fetch(`${API_BASE_URL}/reasoning`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ signal, price, rsi, macd })
      });
      if (!res.ok) {
        setAiReasoning(`API Error: ${res.status} ${res.statusText}`);
        return;
      }
      const json = await res.json();
      if (json.status === "success") {
        setAiReasoning(json.data.reasoning);
      } else {
        setAiReasoning(json.message || "Failed to generate reasoning.");
      }
    } catch (e) {
      setAiReasoning(`Error: ${e.message}`);
    }
  };

  useEffect(() => {
    fetchDashboardData();
    fetchExtraFeatures();

    const interval = setInterval(() => {
      fetchDashboardData();
    }, 60000);

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const ws = new WebSocket(`${WS_BASE_URL}/ws/live`);
    
    ws.onmessage = (event) => {
      try {
        const json = JSON.parse(event.data);
        if (json.status === 'success') {
          setData(prev => {
            if (!prev) return prev;
            return {
              ...prev,
              current_price: json.current_price,
              forecast: json.forecast
            };
          });
        }
      } catch (err) {
        console.error("Error parsing websocket data", err);
      }
    };

    ws.onerror = (err) => {
      console.error("WebSocket error", err);
    };

    ws.onclose = () => {
      console.log("WebSocket connection closed");
    };

    return () => {
      ws.close();
    };
  }, []);

  // Toast Notification Effect
  const latestSignal = signals.length > 0 ? signals[signals.length - 1] : null;
  const previousSignalRef = useRef(null);

  useEffect(() => {
    if (latestSignal && data && intelligenceData) {
      if (!aiReasoning) {
        fetchAIReasoning(
          latestSignal.Action, 
          data.current_price, 
          intelligenceData.market_regime?.rsi || 50, 
          0 // simplified MACD
        );
      }
    }
  }, [latestSignal, data, intelligenceData]);

  useEffect(() => {
    if (latestSignal && previousSignalRef.current !== latestSignal.Action) {
      if (latestSignal.Action === 'BUY') {
        toast.success('📈 BUY ALERT: AI detects upward momentum!', { duration: 5000 });
      } else if (latestSignal.Action === 'SELL') {
        toast.error('🚨 URGENT: Market dropping! AI predicts a fall.', { duration: 6000 });
      } else if (previousSignalRef.current !== null) {
        toast('Market stabilized. AI suggests HOLD.', { icon: '⚖️', duration: 4000 });
      }
      previousSignalRef.current = latestSignal.Action;
    }
  }, [latestSignal]);

  const handleCustomForecast = async () => {
    if (!customDate) return;
    setIsFetchingCustom(true);
    setCustomForecast(null); // Clear previous result
    try {
      const res = await fetch(`${API_BASE_URL}/custom-forecast`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target_date: customDate,
          model_name: data?.active_model || "LinearRegression"
        }),
      });
      const json = await res.json();
      if (res.ok && json.status === "success") {
        setCustomForecast(json.data);
      } else {
        alert(json.detail || "Failed to generate forecast.");
      }
    } catch (err) {
      console.error(err);
      alert("Error connecting to server.");
    } finally {
      setIsFetchingCustom(false);
    }
  };

  const handleSimulate = async () => {
    setIsSimulating(true);
    try {
      const res = await fetch(`${API_BASE_URL}/simulate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          variable: simVariable, 
          change_pct: parseFloat(simChange), 
          model_name: data?.active_model || 'LinearRegression' 
        })
      });
      const json = await res.json();
      if (json.status === "success") setSimResult(json.data);
    } catch (err) {
      console.error(err);
    } finally {
      setIsSimulating(false);
    }
  };

  const handleRunBacktest = async () => {
    setIsBacktesting(true);
    setBacktestMetrics(null);
    try {
      const res = await fetch(`${API_BASE_URL}/backtest?model_name=${data?.active_model || "LinearRegression"}`);
      const json = await res.json();
      if (json.status === "success") {
        setBacktestMetrics(json.data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsBacktesting(false);
    }
  };



  const handleSendChat = async () => {
    if (!chatInput.trim()) return;
    const userMsg = chatInput;
    setChatMessages(prev => [...prev, { role: 'user', text: userMsg }]);
    setChatInput('');
    setChatMessages(prev => [...prev, { role: 'ai', text: '...' }]);

    try {
      const res = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMsg })
      });
      const json = await res.json();
      if (json.status === "success") {
        setChatMessages(prev => {
          const newMsgs = [...prev];
          newMsgs[newMsgs.length - 1] = { role: 'ai', text: json.data.reply };
          return newMsgs;
        });
      }
    } catch (e) {
      setChatMessages(prev => {
        const newMsgs = [...prev];
        newMsgs[newMsgs.length - 1] = { role: 'ai', text: "Sorry, I'm offline." };
        return newMsgs;
      });
    }
  };

  if (loading && !data) {
    return (
      <div className="flex h-screen items-center justify-center bg-[#FAF9F5] text-stone-800">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-emerald-500"></div>
      </div>
    );
  }

  if (!data) return <div className="p-10 text-stone-800 bg-[#FAF9F5] h-screen">Failed to load dashboard. Ensure FastAPI is running on port 8000.</div>;

  const { current_price, forecast, risk_metrics, active_model, ohlc } = data;

  // Chart Setup
  const candlestickOptions = {
    chart: { type: 'candlestick', background: 'transparent', toolbar: { show: false } },
    theme: { mode: 'light' },
    plotOptions: {
      candlestick: { colors: { upward: '#10B981', downward: '#EF4444' } }
    },
    xaxis: { type: 'datetime', labels: { style: { colors: '#78716c' } } },
    yaxis: {
      tooltip: { enabled: true },
      labels: { style: { colors: '#78716c' }, formatter: (value) => "₹" + value.toFixed(2) }
    },
    grid: { borderColor: '#E2E8F0' },
  };

  
  const lineSeriesData = [{
    name: 'Close Price',
    data: (ohlc || []).map(item => ({ x: item.x, y: item.y[3] }))
  }];

  const lineOptions = {
    chart: { type: 'area', background: 'transparent', toolbar: { show: false }, animations: { enabled: false } },
    theme: { mode: 'light' },
    colors: ['#D97706'], // Indigo color
    fill: {
      type: 'gradient',
      gradient: { shadeIntensity: 1, opacityFrom: 0.4, opacityTo: 0.05, stops: [0, 100] }
    },
    stroke: { curve: 'smooth', width: 2 },
    xaxis: { type: 'datetime', labels: { style: { colors: '#78716c' } }, axisBorder: { show: false }, axisTicks: { show: false } },
    yaxis: {
      labels: { formatter: (value) => '₹' + value.toFixed(2), style: { colors: '#78716c' } }
    },
    grid: { borderColor: '#e2e8f0', strokeDashArray: 4 },
    dataLabels: { enabled: false },
    tooltip: { theme: 'light', x: { format: 'dd MMM yyyy' } }
  };

const candlestickSeries = [{
    name: 'candle',
    data: ohlc || []
  }];

  const renderSignalBadge = (sig) => {
    if (sig === 'BUY') return <span className="px-2 py-1 bg-emerald-50 text-emerald-700 rounded-md text-xs font-bold border border-emerald-500/50">BUY</span>;
    if (sig === 'SELL') return <span className="px-2 py-1 bg-rose-50 text-rose-700 rounded-md text-xs font-bold border border-red-500/50">SELL</span>;
    return <span className="px-2 py-1 bg-amber-50 text-amber-700 rounded-md text-xs font-bold border border-yellow-500/50">HOLD</span>;
  };

  // Portfolio Calculations
  let investedAmount = 0;
  let currentValue = 0;
  let profitLoss = 0;
  let profitLossPercent = 0;
  let smartAdvice = "Awaiting input...";

  const parsedTotalInvested = parseFloat(totalInvestedInput);
  const parsedUnits = parseFloat(units);

  if (!isNaN(parsedTotalInvested) && !isNaN(parsedUnits) && parsedUnits > 0 && parsedTotalInvested > 0) {
    investedAmount = parsedTotalInvested;
    currentValue = current_price * parsedUnits;
    profitLoss = currentValue - investedAmount;
    profitLossPercent = (profitLoss / investedAmount) * 100;
    
    const sig = latestSignal?.Action || 'HOLD';
    if (profitLoss > 0 && sig === 'SELL') {
        smartAdvice = "TAKE PROFIT - You are up and AI predicts a downturn.";
    } else if (profitLoss > 0 && sig === 'BUY') {
        smartAdvice = "HOLD STRONG - You are in profit and momentum is still upwards.";
    } else if (profitLoss > 0 && sig === 'HOLD') {
        smartAdvice = "RIDING PROFITS - Neutral momentum, let it ride.";
    } else if (profitLoss < 0 && sig === 'BUY') {
        smartAdvice = "AVERAGE DOWN - You are down, but AI signals a strong buy/recovery.";
    } else if (profitLoss < 0 && sig === 'SELL') {
        smartAdvice = "CUT LOSSES - You are down and the AI predicts further drops.";
    } else if (profitLoss < 0 && sig === 'HOLD') {
        smartAdvice = "WAIT FOR RECOVERY - Neutral market, wait for a better exit.";
    }
  }

  return (
    <div className="min-h-screen bg-stone-50 text-stone-850 text-stone-800 font-sans p-4 md:p-8 lg:p-12 overflow-x-hidden">
      <Toaster position="top-right" toastOptions={{
        style: { background: '#fff', color: '#1c1917', border: '1px solid #e7e5e4', borderRadius: '12px' }
      }} />
      
      {/* Header */}
      <header className="mb-8 flex justify-between items-end border-b border-stone-200 pb-4">
        <div>
          <h1 className="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-amber-600 to-amber-700">
            GoldBeES Intelligence
          </h1>
          <p className="text-stone-500 text-sm mt-1">Quantitative Prediction Engine & Portfolio Tracker</p>
        </div>
        <div className="flex flex-col sm:flex-row items-center sm:space-x-4 space-y-4 sm:space-y-0 w-full sm:w-auto mt-4 sm:mt-0">
          <a 
            href={`${API_BASE_URL}/report`}
            target="_blank"
            rel="noreferrer"
            className="flex items-center space-x-2 bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-xl text-sm font-semibold transition-all"
          >
            <Download className="w-4 h-4" />
            <span>AI PDF Report</span>
          </a>
          {!isLoaded ? (
            <div className="w-24 h-10 bg-slate-800 animate-pulse rounded-xl"></div>
          ) : !userId ? (
            <SignInButton mode="modal">
              <button className="bg-amber-500 hover:bg-amber-600 text-stone-950 font-bold px-4 py-2 rounded-lg text-sm font-semibold transition-colors">
                Sign In to Save Portfolio
              </button>
            </SignInButton>
          ) : (
            <UserButton afterSignOutUrl="/" appearance={{ elements: { avatarBox: "w-10 h-10 border-2 border-amber-500" } }}/>
          )}
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        {/* Tab Navigation */}
        <div className="flex flex-wrap justify-center gap-1 sm:space-x-1 bg-stone-200/60 p-1 rounded-2xl mb-8 border border-stone-200 w-full sm:w-fit mx-auto backdrop-blur-sm">
          {['overview', 'ailab', 'simulation'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-6 py-2.5 rounded-xl text-sm font-semibold transition-all duration-300 ${
                activeTab === tab
                  ? 'bg-gradient-to-r from-amber-500 to-amber-600 text-stone-800 shadow-lg'
                  : 'text-stone-500 hover:text-stone-800 hover:bg-stone-200'
              }`}
            >
              {tab === 'overview' && '📊 Overview'}
              {tab === 'ailab' && '🧠 AI Lab'}
              {tab === 'simulation' && '🛡️ Risk & Simulation'}
            </button>
          ))}
        </div>

        {activeTab === 'overview' && (
          <>
            {/* Main Dashboard Section */}
            <div className="mb-10 text-center relative z-10 p-8 bg-gradient-to-br from-amber-500 to-amber-600 text-white rounded-3xl shadow-xl border border-amber-600/30">
              <p className="text-sm text-amber-100/90 font-medium">Live Current Price (INR)</p>
              <p className="text-5xl font-mono font-bold mt-1 transition-all duration-300">
                ₹{current_price.toFixed(2)}
              </p>
            </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white border border-stone-200 shadow-sm border border-stone-200/80 p-6 rounded-2xl shadow-sm hover:shadow-md transition-all duration-300">
          <p className="text-stone-500 text-sm flex justify-between">Tomorrow's Forecast <ArrowUpRight className="text-emerald-600 w-5 h-5" /></p>
          <p className="text-2xl font-bold mt-2 font-mono">₹{forecast.Forecast_1_Day.toFixed(2)}</p>
          <p className="text-xs text-stone-400 mt-1">Upper CI: ₹{forecast.CI_1_Day_Upper.toFixed(2)}</p>
        </div>
        <div className="bg-white border border-stone-200 shadow-sm border border-stone-200/80 p-6 rounded-2xl shadow-sm hover:shadow-md transition-all duration-300">
          <p className="text-stone-500 text-sm flex justify-between">30-Day Outlook <TrendingUp className="text-amber-700 w-5 h-5" /></p>
          <p className="text-2xl font-bold mt-2 font-mono">₹{forecast.Forecast_30_Days.toFixed(2)}</p>
          <p className="text-xs text-emerald-600 mt-1">+ {(((forecast.Forecast_30_Days / current_price) - 1) * 100).toFixed(2)}% Expected Return</p>
        </div>
        <div className="bg-white border border-stone-200 shadow-sm border border-stone-200/80 p-6 rounded-2xl shadow-sm hover:shadow-md transition-all duration-300">
          <p className="text-stone-500 text-sm flex justify-between">Value at Risk (95%) <AlertTriangle className="text-red-600 w-5 h-5" /></p>
          <p className="text-2xl font-bold mt-2 font-mono">{(((risk_metrics["VaR_95%"])*100)).toFixed(2)}%</p>
          <p className="text-xs text-stone-400 mt-1">Maximum Expected Daily Loss</p>
        </div>
        <div className="bg-white border border-stone-200 shadow-sm border border-stone-200/80 p-6 rounded-2xl shadow-sm hover:shadow-md transition-all duration-300">
          <p className="text-stone-500 text-sm flex justify-between">Annual Volatility <ShieldCheck className="text-stone-500 w-5 h-5" /></p>
          <p className="text-2xl font-bold mt-2 font-mono">{(risk_metrics.Annualized_Volatility * 100).toFixed(2)}%</p>
          <p className="text-xs text-stone-400 mt-1">Trailing historical risk</p>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 lg:gap-8 mb-8">
        
        {/* Left Column (Chart & Portfolio Tracker) */}
        <div className="lg:col-span-2 space-y-8">
          
          <div className="bg-white border border-stone-200 rounded-2xl shadow-sm p-6 lg:col-span-2">
            <h2 className="text-xl font-semibold mb-4 flex items-center text-stone-700">
              <TrendingUp className="mr-2 text-emerald-500 w-6 h-6" /> Professional Candlestick Chart
            </h2>
            <div className="h-80 w-full relative">
              {ohlc && ohlc.length > 0 ? (
                <ReactApexChart 
                  options={candlestickOptions} 
                  series={candlestickSeries} 
                  type="candlestick" 
                  height="100%" 
                />
              ) : (
                <div className="absolute inset-0 flex items-center justify-center text-stone-400">Loading chart data...</div>
              )}
            </div>
          </div>

          {/* Simple Price Trend Chart */}
          <div className="bg-white border border-stone-200 rounded-2xl shadow-sm p-6 lg:col-span-2">
            <h2 className="text-xl font-semibold mb-4 flex items-center text-stone-700">
              <TrendingUp className="mr-2 text-amber-700 w-6 h-6" /> Simple Price Trend
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
                <div className="absolute inset-0 flex items-center justify-center text-stone-400">Loading chart data...</div>
              )}
            </div>
          </div>

          {/* Personal Portfolio Tracker */}
          <div className="bg-white border border-stone-200 rounded-2xl shadow-sm p-6">
            <h2 className="text-xl font-semibold flex items-center text-stone-700 mb-6">
              <Briefcase className="mr-2 text-stone-600 w-6 h-6" /> Personal Portfolio Tracker
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-stone-500 mb-1">Total Invested Amount (INR)</label>
                  <input 
                    type="number" step="0.01" value={totalInvestedInput} onChange={(e) => setTotalInvestedInput(e.target.value)}
                    placeholder="e.g. 115000.00"
                    className="w-full bg-white border border-stone-300 text-stone-800 rounded-xl px-4 py-2 focus:outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
                  />
                </div>
                <div>
                  <label className="block text-sm text-stone-500 mb-1">Total Units Held</label>
                  <input 
                    type="number" value={units} onChange={(e) => setUnits(e.target.value)}
                    placeholder="e.g. 1000"
                    className="w-full bg-white border border-stone-300 text-stone-800 rounded-xl px-4 py-2 focus:outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
                  />
                </div>
              </div>

              <div className="bg-stone-50 p-4 rounded-xl border border-stone-200 flex flex-col justify-center">
                {!isNaN(parsedTotalInvested) && !isNaN(parsedUnits) && parsedUnits > 0 ? (
                  <>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm text-stone-500">Average Buy Price:</span>
                      <span className="font-mono text-stone-600">₹{(investedAmount / parsedUnits).toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between items-center mb-4 border-b border-stone-200 pb-2">
                      <span className="text-sm text-stone-500">Current Value:</span>
                      <span className="font-mono text-stone-800">₹{currentValue.toFixed(2)}</span>
                    </div>
                    <div className="text-center">
                      <p className="text-sm text-stone-500 mb-1">Live Profit/Loss</p>
                      <p className={`text-2xl font-bold font-mono ${profitLoss >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                        {profitLoss >= 0 ? '+₹' : '-₹'}{Math.abs(profitLoss).toFixed(2)} ({profitLossPercent.toFixed(2)}%)
                      </p>
                    </div>
                  </>
                ) : (
                  <p className="text-center text-stone-400 text-sm">Enter your buy price and units to track live performance.</p>
                )}
              </div>
            </div>

            {/* Smart Advisor Alert */}
            {!isNaN(parsedTotalInvested) && !isNaN(parsedUnits) && parsedUnits > 0 && (
              <div className={`mt-6 p-4 rounded-lg flex items-start border ${
                smartAdvice.includes('PROFIT') || smartAdvice.includes('STRONG') ? 'bg-emerald-50 border-emerald-200' :
                smartAdvice.includes('LOSSES') ? 'bg-rose-50 border-rose-200' : 
                'bg-amber-50 border-amber-200'
              }`}>
                <Info className={`w-5 h-5 mr-3 mt-0.5 ${
                   smartAdvice.includes('PROFIT') || smartAdvice.includes('STRONG') ? 'text-emerald-600' :
                   smartAdvice.includes('LOSSES') ? 'text-red-600' : 'text-amber-700'
                }`} />
                <div>
                  <h4 className={`text-sm font-bold uppercase tracking-wider mb-1 ${
                   smartAdvice.includes('PROFIT') || smartAdvice.includes('STRONG') ? 'text-emerald-600' :
                   smartAdvice.includes('LOSSES') ? 'text-red-600' : 'text-amber-700'
                  }`}>AI Smart Advisor</h4>
                  <p className="text-stone-600 text-sm italic">It&apos;s important to track momentum.</p>
                </div>
              </div>
            )}
          </div>

        </div>

        {/* Right Column (Widgets) */}
        <div className="space-y-8">
          
          {/* Macro Data Widget */}
          <div className="bg-white border border-stone-200 rounded-2xl shadow-sm p-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center text-stone-700">
              <Globe className="mr-2 text-stone-600 w-6 h-6" /> Macro Economics
            </h2>
            {macroData ? (
              <div className="space-y-3">
                <div className="flex justify-between items-center p-3 bg-[#FAF9F5] rounded-lg border border-stone-200">
                  <span className="text-stone-500 text-sm">USD to INR</span>
                  <span className="font-mono text-stone-700">₹{macroData.USD_INR.toFixed(2)}</span>
                </div>
                <div className="flex justify-between items-center p-3 bg-[#FAF9F5] rounded-lg border border-stone-200">
                  <span className="text-stone-500 text-sm">Global Gold (USD/oz)</span>
                  <span className="font-mono text-yellow-500">${macroData.Gold_Futures_USD.toFixed(2)}</span>
                </div>
              </div>
            ) : <p className="text-stone-400 text-sm">Loading macro data...</p>}
          </div>

          {/* AI Confidence Meter */}
          {intelligenceData?.confidence && (
            <div className="bg-white border border-stone-200 rounded-2xl shadow-sm p-6">
              <h2 className="text-xl font-semibold mb-4 flex items-center text-stone-700">
                <ShieldCheck className="mr-2 text-stone-600 w-6 h-6" /> AI Confidence Meter
              </h2>
              <div className="text-center mb-4">
                <div className={`text-5xl font-bold font-mono mb-1 ${
                  intelligenceData.confidence.score >= 80 ? 'text-emerald-600' :
                  intelligenceData.confidence.score >= 60 ? 'text-yellow-400' : 'text-red-600'
                }`}>{intelligenceData.confidence.score}%</div>
                <p className="text-stone-500 text-sm">{intelligenceData.confidence.label}</p>
              </div>
              <div className="w-full bg-stone-100 rounded-full h-3 mb-4">
                <div
                  className={`h-3 rounded-full transition-all duration-700 ${
                    intelligenceData.confidence.score >= 80 ? 'bg-emerald-500' :
                    intelligenceData.confidence.score >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                  }`}
                  style={{ width: `${intelligenceData.confidence.score}%` }}
                />
              </div>
              <div className="space-y-1">
                {intelligenceData.confidence.factors.map((f, i) => (
                  <div key={i} className="flex justify-between text-xs">
                    <span className="text-stone-500">{f.label}</span>
                    <span className={f.positive ? 'text-emerald-600' : 'text-red-600'}>{f.impact}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Market Regime Widget */}
          {intelligenceData?.market_regime && (
            <div className="bg-white border border-stone-200 rounded-2xl shadow-sm p-6">
              <h2 className="text-xl font-semibold mb-4 flex items-center text-stone-700">
                <Activity className="mr-2 text-stone-600 w-6 h-6" /> Market Regime
              </h2>
              <div className="text-center mb-4">
                <span className={`inline-block px-6 py-3 rounded-xl text-2xl font-bold border ${
                  intelligenceData.market_regime.regime === 'Bull' ? 'bg-emerald-50 text-emerald-700 border-emerald-500/50' :
                  intelligenceData.market_regime.regime === 'Bear' ? 'bg-rose-50 text-rose-700 border-red-500/50' :
                  intelligenceData.market_regime.regime === 'High Volatility' ? 'bg-orange-50 text-orange-700 border-orange-300' :
                  'bg-amber-50 text-amber-800 border-amber-300'
                }`}>
                  {intelligenceData.market_regime.regime === 'Bull' ? '🐂' :
                   intelligenceData.market_regime.regime === 'Bear' ? '🐻' :
                   intelligenceData.market_regime.regime === 'High Volatility' ? '⚡' : '↔️'}
                  &nbsp;{intelligenceData.market_regime.regime}
                </span>
                <p className="text-stone-500 text-sm mt-2">{intelligenceData.market_regime.confidence}% Confidence</p>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div className="p-2 bg-[#FAF9F5] rounded-lg text-center">
                  <p className="text-xs text-stone-400">RSI</p>
                  <p className="text-stone-700 font-mono">{intelligenceData.market_regime.rsi}</p>
                </div>
                <div className="p-2 bg-[#FAF9F5] rounded-lg text-center">
                  <p className="text-xs text-stone-400">Volatility</p>
                  <p className="text-stone-700 font-mono">{intelligenceData.market_regime.volatility}%</p>
                </div>
              </div>
            </div>
          )}

          {/* Anomaly Detection */}
          {intelligenceData?.anomalies?.anomaly_detected && (
            <div className="bg-orange-950/40 border border-orange-800/60 rounded-2xl shadow-lg p-6">
              <h2 className="text-xl font-semibold mb-4 flex items-center text-orange-300">
                <AlertTriangle className="mr-2 text-orange-400 w-6 h-6" /> Anomaly Detected!
              </h2>
              <div className="space-y-3">
                {intelligenceData.anomalies.anomalies.map((a, i) => (
                  <div key={i} className={`p-3 rounded-lg border ${
                    a.severity === 'high' ? 'bg-red-950/40 border-red-700' : 'bg-orange-950/40 border-orange-700'
                  }`}>
                    <p className="font-semibold text-sm text-orange-200">{a.icon} {a.type}</p>
                    <p className="text-xs text-orange-300/80 mt-1">{a.message}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          </div> {/* End Right Column */}
        </div> {/* End Main Content Grid */}

        {/* Wave 4: AI News Intelligence */}
        {newsData?.summary && (
          <div className="bg-white border border-stone-200 rounded-2xl shadow-sm p-6 w-full mb-8">
            <h2 className="text-xl font-semibold mb-4 flex items-center text-stone-700">
              <Globe className="mr-2 text-amber-700 w-6 h-6" /> AI News Intelligence
            </h2>
            <div className="flex flex-col md:flex-row gap-6">
              <div className="flex-1 bg-stone-50 p-4 rounded-xl border border-stone-200">
                <p className="text-sm text-stone-500 font-semibold mb-2">Latest Market Summary (Gold, RBI, Fed)</p>
                <p className="text-sm text-stone-600 leading-relaxed whitespace-pre-line">
                  {newsData.summary}
                </p>
              </div>
              <div className="md:w-64 flex flex-col justify-center space-y-4">
                <div className="bg-stone-50 p-4 rounded-xl border border-stone-200 text-center">
                  <p className="text-xs text-stone-400 uppercase tracking-wider mb-1">Sentiment</p>
                  <p className={`text-2xl font-bold ${newsData.sentiment === 'Bullish' ? 'text-emerald-600' : newsData.sentiment === 'Bearish' ? 'text-red-600' : 'text-yellow-400'}`}>
                    {newsData.sentiment}
                  </p>
                </div>
                <div className="bg-stone-50 p-4 rounded-xl border border-stone-200 text-center">
                  <p className="text-xs text-stone-400 uppercase tracking-wider mb-1">Confidence</p>
                  <p className="text-2xl font-bold text-stone-700">{newsData.confidence}%</p>
                </div>
              </div>
            </div>
          </div>
        )}
        </>
        )}

        {activeTab === 'ailab' && (
          <div className="space-y-8">
          {/* Wave 5: Multi-Agent Architecture */}
          {agentsData && (
            <div className="bg-white border border-stone-200 rounded-2xl shadow-sm p-6 col-span-1 lg:col-span-2">
              <h2 className="text-xl font-semibold mb-6 flex items-center text-stone-700">
                <Users className="mr-2 text-amber-700 w-6 h-6" /> Multi-Agent AI Decision System
              </h2>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6 mb-8">
                {agentsData.sub_agents.map((agent, i) => (
                  <div key={i} className="bg-stone-50 p-4 rounded-xl border border-stone-200 flex flex-col items-center text-center">
                    <p className="text-sm font-semibold text-stone-600 mb-2">{agent.agent}</p>
                    <div className={`px-4 py-1 rounded-full text-sm font-bold mb-3 border ${
                      agent.signal === 'BUY' ? 'bg-emerald-50 text-emerald-700 border-emerald-500/50' : 
                      agent.signal === 'SELL' ? 'bg-rose-50 text-rose-700 border-red-500/50' : 
                      'bg-gray-500/20 text-stone-500 border-gray-500/50'
                    }`}>
                      {agent.signal} ({agent.confidence}%)
                    </div>
                    <p className="text-xs text-stone-400">{agent.reason}</p>
                  </div>
                ))}
              </div>

              <div className="bg-gradient-to-r from-indigo-900/50 to-blue-900/50 border border-stone-200 p-6 rounded-xl flex flex-col md:flex-row items-center justify-between">
                <div>
                  <p className="text-sm text-indigo-300 font-semibold mb-1">Chief Investment AI Final Decision</p>
                  <p className="text-xs text-stone-500">Aggregated consensus from all specialized agents.</p>
                </div>
                <div className="mt-4 md:mt-0 flex items-center space-x-4">
                  <div className="text-right">
                    <p className="text-xs text-stone-500 uppercase tracking-wider">Confidence</p>
                    <p className="text-xl font-bold text-stone-700">{agentsData.confidence}%</p>
                  </div>
                  <div className={`px-6 py-3 rounded-xl text-2xl font-bold shadow-lg border ${
                    agentsData.final_signal === 'BUY' ? 'bg-emerald-600 text-stone-800 border-emerald-400' : 
                    agentsData.final_signal === 'SELL' ? 'bg-red-600 text-stone-800 border-red-400' : 
                    'bg-gray-600 text-stone-800 border-gray-400'
                  }`}>
                    {agentsData.final_signal}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Wave 6: RL Agent */}
          {rlData && (
            <div className="bg-white border border-stone-200 rounded-2xl shadow-sm p-6">
              <h2 className="text-xl font-semibold mb-6 flex items-center text-stone-700">
                <Cpu className="mr-2 text-stone-600 w-6 h-6" /> Local RL Agent (PPO)
              </h2>
              <div className="flex flex-col space-y-4">
                <div className="bg-stone-50 p-4 rounded-xl border border-stone-200 flex justify-between items-center">
                  <div>
                    <p className="text-xs text-stone-400 uppercase tracking-wider mb-1">Cumulative Reward</p>
                    <p className="text-xl font-bold text-emerald-600">+₹{rlData.cumulative_reward.toLocaleString()}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-stone-400 uppercase tracking-wider mb-1">Episodes</p>
                    <p className="text-xl font-bold text-stone-700">{rlData.episodes_trained.toLocaleString()}</p>
                  </div>
                </div>
                <div className="bg-stone-50 p-4 rounded-xl border border-stone-200 flex justify-between items-center">
                  <div>
                    <p className="text-xs text-stone-400 uppercase tracking-wider mb-1">PPO Policy Action</p>
                    <p className={`text-xl font-bold ${
                      rlData.current_action === 'BUY' ? 'text-emerald-600' : 
                      rlData.current_action === 'SELL' ? 'text-red-600' : 'text-stone-500'
                    }`}>
                      {rlData.current_action} ({rlData.action_confidence}%)
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-stone-400 uppercase tracking-wider mb-1">Loss (P / V)</p>
                    <p className="text-sm font-mono text-stone-600">
                      {rlData.metrics.policy_loss} / {rlData.metrics.value_loss}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* SHAP Explainability Widget */}
          {intelligenceData?.shap?.top_features?.length > 0 && (
            <div className="bg-white border border-stone-200 rounded-2xl shadow-sm p-6">
              <h2 className="text-xl font-semibold mb-1 flex items-center text-stone-700">
                <Info className="mr-2 text-violet-400 w-6 h-6" /> Why this Prediction?
              </h2>
              <p className="text-xs text-stone-400 mb-4">Top factors driving today's AI forecast</p>
              <div className="space-y-2">
                {intelligenceData.shap.top_features.map((f, i) => (
                  <div key={i}>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-stone-600 font-medium truncate pr-2">{f.feature.replace(/_/g, ' ')}</span>
                      <span className={f.direction === 'positive' ? 'text-emerald-600' : 'text-red-600'}>
                        {f.direction === 'positive' ? '+' : '-'}{f.percentage}%
                      </span>
                    </div>
                    <div className="w-full bg-slate-800 rounded-full h-1.5">
                      <div
                        className={`h-1.5 rounded-full ${f.direction === 'positive' ? 'bg-emerald-500' : 'bg-red-500'}`}
                        style={{ width: `${f.percentage}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="bg-white border border-stone-200 rounded-2xl shadow-sm p-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center text-stone-700">
              <BarChart2 className="mr-2 text-yellow-500 w-6 h-6" /> AI Trading Signals
            </h2>
            {latestSignal ? (
              <div className="text-center py-4 bg-[#FAF9F5] rounded-xl mb-4 border border-stone-200">
                <p className="text-sm text-stone-500 mb-2">Current Market Recommendation</p>
                <div className="text-3xl mb-3">{renderSignalBadge(latestSignal.Action)}</div>
                {/* Wave 3: AI Reasoning */}
                <div className="text-left bg-white shadow-sm border border-stone-200 p-3 rounded-lg border border-stone-200 text-xs text-stone-600">
                  <p className="text-stone-500 font-semibold mb-1 flex items-center"><Info className="w-3 h-3 mr-1"/> AI Reasoning:</p>
                  <div className="whitespace-pre-line">{aiReasoning || "Loading reasoning..."}</div>
                </div>
              </div>
            ) : <p className="text-stone-400 text-sm">Loading signals...</p>}
            
            <div className="space-y-2 mt-4">
              <p className="text-xs text-stone-400 font-semibold uppercase tracking-wider mb-2">Recent History</p>
              {signals.slice(0, 4).reverse().map((sig, idx) => (
                <div key={idx} className="flex justify-between items-center text-sm p-2 bg-stone-100/80 rounded-lg">
                  <span className="text-stone-500">{String(sig.Date).split(' ')[0]}</span>
                  {renderSignalBadge(sig.Action)}
                </div>
              ))}
            </div>
          </div>

          </div>
        )}

        {activeTab === 'simulation' && (
          <>
          <div className="space-y-8">
            <div className="bg-white border border-stone-200 rounded-2xl shadow-sm p-6">
              <h2 className="text-xl font-semibold mb-4 flex items-center text-stone-700">
                <PlayCircle className="mr-2 text-stone-600 w-6 h-6" /> Strategy Backtester
              </h2>
            <p className="text-sm text-stone-500 mb-4">Simulate historical trading using AI signals vs Buy & Hold.</p>
            
            {backtestMetrics ? (
              <div className="space-y-4 mb-4">
                <div className="flex justify-between items-center bg-stone-50 p-3 rounded-lg border border-stone-200">
                  <span className="text-stone-500 text-sm">Market ROI</span>
                  <span className="font-mono">{backtestMetrics.Market_ROI_Percent.toFixed(2)}%</span>
                </div>
                <div className="flex justify-between items-center bg-emerald-50 p-3 rounded-lg border border-emerald-200">
                  <span className="text-emerald-600 text-sm">AI Strategy ROI</span>
                  <span className="font-mono text-emerald-600 font-bold">{backtestMetrics.Strategy_ROI_Percent.toFixed(2)}%</span>
                </div>
              </div>
            ) : null}

            <button 
              onClick={handleRunBacktest} disabled={isBacktesting}
              className="w-full bg-stone-800 hover:bg-stone-900 text-white font-bold py-2.5 px-4 rounded-xl transition-all shadow-sm flex justify-center items-center disabled:opacity-50"
            >
              {isBacktesting ? "Simulating..." : "Run Vectorized Backtest"}
            </button>
          </div>
          
          <div className="bg-white border border-stone-200 rounded-2xl shadow-sm p-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center text-stone-700">
              <Calendar className="mr-2 text-stone-600 w-6 h-6" /> Custom Date Forecast
            </h2>
            <div className="space-y-4">
              <input 
                type="date" 
                value={customDate}
                onChange={(e) => setCustomDate(e.target.value)}
                className="w-full bg-white border border-stone-300 text-stone-800 rounded-xl px-4 py-2 focus:outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
              />
              <button 
                onClick={handleCustomForecast} disabled={isFetchingCustom || !customDate}
                className="w-full bg-amber-500 hover:bg-amber-600 text-stone-950 font-bold py-2.5 px-4 rounded-xl shadow-sm transition-colors flex justify-center items-center disabled:opacity-50"
              >
                {isFetchingCustom ? "Calculating..." : "Predict Price"}
              </button>
              {customForecast && (
                <div className="mt-4 p-4 bg-[#FAF9F5] rounded-lg border border-stone-200 text-center">
                  <p className="text-sm text-stone-500">Projected Price</p>
                  <p className="text-2xl font-bold font-mono text-amber-700">₹{customForecast.Projected_Price.toFixed(2)}</p>
                </div>
              )}
            </div>
          </div>

        </div>

      
      {/* Strategy Builder Widget */}
      <div className="bg-white border border-stone-200 rounded-2xl shadow-sm p-6 mb-8 mt-8">
        <h2 className="text-xl font-semibold mb-4 flex items-center text-stone-700">
          <Activity className="mr-2 text-stone-600 w-6 h-6" /> Custom Strategy Builder
        </h2>
        <div className="bg-[#FAF9F5] p-6 rounded-xl border border-stone-200 space-y-4">
          <p className="text-sm text-stone-500 mb-4">Define your buy conditions. The backtester will simulate buying on these days.</p>
          
          {strategyRules.map((rule, i) => (
            <div key={i} className="flex flex-col sm:flex-row flex-wrap gap-4 items-start sm:items-center bg-white shadow-sm border border-stone-200 p-4 rounded-lg border border-stone-200 w-full">
              <select className="bg-white text-stone-800 rounded-xl p-2 border border-stone-300 w-full sm:w-auto focus:outline-none focus:border-amber-500" value={rule.indicator} onChange={e => handleUpdateRule(i, 'indicator', e.target.value)}>
                <option value="RSI">RSI</option>
                <option value="MACD">MACD</option>
                <option value="ADX">ADX</option>
                <option value="Close">Close Price</option>
                <option value="SMA_20">SMA 20</option>
                <option value="SMA_50">SMA 50</option>
              </select>
              <select className="bg-white text-stone-800 rounded-xl p-2 border border-stone-300 w-full sm:w-auto focus:outline-none focus:border-amber-500" value={rule.operator} onChange={e => handleUpdateRule(i, 'operator', e.target.value)}>
                <option value=">">&gt;</option>
                <option value="<">&lt;</option>
                <option value=">=">&gt;=</option>
                <option value="<=">&lt;=</option>
                <option value="==">==</option>
              </select>
              <input type="number" className="bg-white text-stone-800 rounded-xl p-2 border border-stone-300 w-full sm:w-24 focus:outline-none focus:border-amber-500" value={rule.value === undefined || isNaN(rule.value) ? '' : rule.value} onChange={e => handleUpdateRule(i, 'value', e.target.value === '' ? '' : parseFloat(e.target.value))} />
              <button onClick={() => handleRemoveRule(i)} className="text-red-600 hover:text-red-300 ml-auto font-bold">&times; Remove</button>
            </div>
          ))}
          
          <div className="flex justify-between items-center mt-4">
            <button onClick={handleAddRule} className="text-sm text-stone-500 hover:text-purple-300 font-semibold">+ Add Condition</button>
            <button onClick={runStrategyBacktest} disabled={isBacktesting} className="bg-stone-850 hover:bg-stone-950 text-white px-6 py-2.5 rounded-xl font-bold transition-all shadow-sm disabled:opacity-50">
              {isBacktesting ? "Simulating..." : "Run Backtest"}
            </button>
          </div>
          
          {backtestResult && (
            <div className="mt-6 pt-6 border-t border-stone-200 grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-white border border-stone-200 shadow-sm shadow-sm border border-stone-200 p-4 rounded-xl border border-stone-200 text-center">
                <p className="text-xs text-stone-400 uppercase tracking-wider mb-1">Win Rate</p>
                <p className={`text-2xl font-bold ${backtestResult.win_rate > 50 ? 'text-emerald-600' : 'text-red-600'}`}>{backtestResult.win_rate}%</p>
              </div>
              <div className="bg-white border border-stone-200 shadow-sm shadow-sm border border-stone-200 p-4 rounded-xl border border-stone-200 text-center">
                <p className="text-xs text-stone-400 uppercase tracking-wider mb-1">Total Return</p>
                <p className={`text-2xl font-bold ${backtestResult.total_return > 0 ? 'text-emerald-600' : 'text-red-600'}`}>{backtestResult.total_return}%</p>
              </div>
              <div className="bg-white border border-stone-200 shadow-sm shadow-sm border border-stone-200 p-4 rounded-xl border border-stone-200 text-center">
                <p className="text-xs text-stone-400 uppercase tracking-wider mb-1">Total Trades</p>
                <p className="text-2xl font-bold text-stone-700">{backtestResult.total_trades}</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Leaderboard Table */}
      <div className="bg-white border border-stone-200 rounded-2xl shadow-sm p-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center text-stone-700">
          <Trophy className="mr-2 text-orange-500 w-6 h-6" /> AI Model Leaderboard
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-stone-200 text-sm text-stone-500">
                <th className="p-3 font-medium">Rank</th>
                <th className="p-3 font-medium">Model Name</th>
                <th className="p-3 font-medium">RMSE Error</th>
                <th className="p-3 font-medium">Directional Accuracy</th>
              </tr>
            </thead>
            <tbody>
              {leaderboard.length > 0 ? leaderboard.map((row, idx) => (
                <tr key={idx} className="border-b border-stone-200/50 hover:bg-stone-200/30 transition-colors">
                  <td className="p-3 font-mono text-stone-400">#{idx + 1}</td>
                  <td className="p-3 font-medium text-stone-700">{row.Model}</td>
                  <td className="p-3 font-mono text-emerald-600">{row.RMSE.toFixed(4)}</td>
                  <td className="p-3 font-mono text-amber-700">{(row.Directional_Accuracy * 100).toFixed(1)}%</td>
                </tr>
              )) : (
                <tr>
                  <td colSpan="4" className="p-4 text-center text-stone-400">No leaderboard data found.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Wave 2: Similar Historical Days */}
      {wave2Data?.similar_days && wave2Data.similar_days.similar_date && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-8 grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="bg-white border border-stone-200 rounded-2xl shadow-sm p-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center text-stone-700">
              <Calendar className="mr-2 text-stone-600 w-6 h-6" /> Historical Pattern Match
            </h2>
            <p className="text-xs text-stone-400 mb-4">Today's technicals closely resemble:</p>
            <div className="text-center py-4 bg-[#FAF9F5] rounded-xl border border-stone-200">
              <p className="text-2xl font-bold font-mono text-pink-400">{wave2Data.similar_days.similar_date}</p>
              <p className="text-sm text-stone-500 mt-1">{wave2Data.similar_days.similarity_score}% Match</p>
            </div>
            <div className="mt-4 p-3 bg-stone-100/80 rounded-lg text-center">
              <p className="text-xs text-stone-500 mb-1">What happened next?</p>
              <p className={`text-lg font-bold ${wave2Data.similar_days.outcome_pct > 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                {wave2Data.similar_days.outcome_pct > 0 ? '+' : ''}{wave2Data.similar_days.outcome_pct}% 
              </p>
            </div>
          </div>

          {/* Wave 2: Pattern Detection */}
          {wave2Data?.patterns?.patterns && (
            <div className="bg-white border border-stone-200 rounded-2xl shadow-sm p-6">
              <h2 className="text-xl font-semibold mb-4 flex items-center text-stone-700">
                <TrendingUp className="mr-2 text-stone-600 w-6 h-6" /> Chart Patterns
              </h2>
              <div className="space-y-2">
                {wave2Data.patterns.patterns.map((p, i) => (
                  <div key={i} className="p-3 bg-indigo-500/10 border border-amber-500/20 text-indigo-300 rounded-lg text-sm font-semibold">
                    {p}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
      
      {/* Bottom Full Width Section: Advanced Analytics */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-8 grid grid-cols-1 lg:grid-cols-2 gap-8 mb-20">
        
        {/* Wave 2: What-If Simulator */}
        <div className="bg-white border border-stone-200 rounded-2xl shadow-sm p-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center text-stone-700">
            <Activity className="mr-2 text-stone-600 w-6 h-6" /> What-If Scenario Simulator
          </h2>
          <div className="flex space-x-4 mb-4">
            <select 
              value={simVariable} 
              onChange={e => setSimVariable(e.target.value)}
              className="bg-white border border-stone-300 text-stone-800 rounded-xl p-2 w-1/2 focus:outline-none focus:border-amber-500"
            >
              <option value="USD_INR">USD to INR</option>
              <option value="Gold_Spot">Global Gold</option>
              <option value="Volume">Trading Volume</option>
            </select>
            <input 
              type="number" 
              value={simChange} 
              onChange={e => setSimChange(e.target.value)}
              placeholder="% Change" 
              className="bg-white border border-stone-300 text-stone-800 rounded-xl p-2 w-1/4 focus:outline-none focus:border-amber-500"
            />
            <button 
              onClick={handleSimulate} 
              disabled={isSimulating}
              className="bg-stone-850 hover:bg-stone-950 text-white font-bold rounded-xl px-4 w-1/4 transition-all shadow-sm"
            >
              {isSimulating ? '...' : 'Simulate'}
            </button>
          </div>
          {simResult && (
            <div className="p-4 bg-[#FAF9F5] rounded-xl border border-stone-200 text-center">
              <p className="text-sm text-stone-500 mb-2">Simulated Outcome</p>
              <p className="text-2xl font-bold font-mono text-stone-800">₹{simResult.new_expected.toFixed(2)}</p>
              <p className={`text-sm mt-1 font-semibold ${simResult.impact_pct > 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                {simResult.impact_pct > 0 ? '+' : ''}{simResult.impact_pct.toFixed(2)}% Impact
              </p>
            </div>
          )}
        </div>

        {/* Wave 2: Probability Distribution Heatmap */}
        {wave2Data?.probability_distribution?.distribution && (
          <div className="bg-white border border-stone-200 rounded-2xl shadow-sm p-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center text-stone-700">
              <BarChart2 className="mr-2 text-yellow-500 w-6 h-6" /> Tomorrow&apos;s Probability
            </h2>
            <div className="space-y-3 mt-4">
              {wave2Data.probability_distribution.distribution.map((bin, i) => (
                <div key={i} className="flex items-center text-sm">
                  <div className="w-20 text-stone-500 font-mono">₹{bin.price.toFixed(1)}</div>
                  <div className="flex-1 bg-stone-100 rounded-full h-4 mx-3">
                    <div 
                      className={`h-4 rounded-full ${bin.probability > 30 ? 'bg-yellow-500' : 'bg-yellow-700'}`} 
                      style={{ width: `${Math.max(bin.probability, 2)}%` }}
                    />
                  </div>
                  <div className="w-12 text-right text-stone-600 font-mono">{bin.probability.toFixed(0)}%</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
      </>
      )}

      {/* Wave 3: Floating AI Chatbot */}
      <div className="fixed bottom-6 right-6 z-50">
        {isChatOpen ? (
          <div className="bg-white border border-stone-200 shadow-sm w-80 h-96 rounded-2xl shadow-2xl flex flex-col overflow-hidden">
            <div className="bg-gradient-to-r from-stone-800 to-stone-900 p-4 text-white flex justify-between items-center cursor-pointer" onClick={() => setIsChatOpen(false)}>
              <span className="font-bold flex items-center"><MessageCircle className="w-5 h-5 mr-2" /> AI Assistant</span>
              <span className="text-stone-300 hover:text-white">&times;</span>
            </div>
            <div className="flex-1 p-4 overflow-y-auto space-y-3 bg-[#FAF9F5]">
              {chatMessages.map((msg, i) => (
                <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`p-2 max-w-[85%] rounded-xl text-sm ${msg.role === 'user' ? 'bg-blue-600 text-white rounded-br-none' : 'bg-slate-800 text-stone-700 rounded-bl-none'}`}>
                    {msg.text}
                  </div>
                </div>
              ))}
            </div>
            <div className="p-3 border-t border-stone-200 flex bg-white shadow-sm border border-stone-200">
              <input 
                type="text" 
                value={chatInput}
                onChange={e => setChatInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleSendChat()}
                placeholder="Ask about your portfolio..."
                className="flex-1 bg-slate-800 border-none text-stone-800 text-sm rounded-l-lg p-2 focus:ring-0"
              />
              <button 
                onClick={handleSendChat}
                className="bg-slate-800 hover:bg-slate-700 text-stone-700 text-stone-800 px-3 rounded-r-lg"
              >
                Send
              </button>
            </div>
          </div>
        ) : (
          <button 
            onClick={() => setIsChatOpen(true)}
            className="w-14 h-14 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-full shadow-2xl flex items-center justify-center text-stone-800 hover:scale-110 transition-transform"
          >
            <MessageCircle className="w-6 h-6" />
          </button>
        )}
      </div>

    </div>
    </div>
  );
}
