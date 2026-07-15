"use client";

import { motion, AnimatePresence } from 'framer-motion';

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
import dynamic from 'next/dynamic';

const ReactApexChart = dynamic(() => import('react-apexcharts'), { ssr: false });

const getApiBaseUrl = () => {
  if (typeof window !== 'undefined') {
    const hn = window.location.hostname;
    // Check if the hostname is a local IP address (e.g., 192.168.x.x, 10.x.x.x, 172.x.x.x)
    const isLocalIp = /^(192\.168\.|10\.|172\.)/.test(hn);

    if (isLocalIp) {
      return `http://${hn}:8000`;
    }
  }
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
};

const API_BASE_URL = getApiBaseUrl().replace(/\/$/, "");
const WS_BASE_URL = API_BASE_URL.replace('http', 'ws');

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler);

export default function Dashboard() {
  // Existing States
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [wakingUp, setWakingUp] = useState(false);
  const [tomorrowPrediction, setTomorrowPrediction] = useState(null);

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
  const [chartTimeframe, setChartTimeframe] = useState("1M");

  // Custom JWT Auth State
  const [userId, setUserId] = useState(null);
  const [isLoaded, setIsLoaded] = useState(false);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authMode, setAuthMode] = useState('login');
  const [authUsername, setAuthUsername] = useState('');
  const [authPassword, setAuthPassword] = useState('');

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    const uid = localStorage.getItem('user_id');
    if (token && uid) {
      setUserId(uid);
    }
    setIsLoaded(true);
  }, []);

  // Portfolio States
  const [totalInvestedInput, setTotalInvestedInput] = useState("");
  const [units, setUnits] = useState("");

  const chartRef = useRef(null);

  const fetchDashboardData = async () => {
    let timeoutId = setTimeout(() => {
      setWakingUp(true);
    }, 3000);

    try {
      const res = await fetch(`${API_BASE_URL}/dashboard`);
      const json = await res.json();
      if (json.status === "success") {
        setData(json.data);
      }
    } catch (err) {
      console.error("Failed to fetch dashboard data", err);
    } finally {
      clearTimeout(timeoutId);
      setLoading(false);
      setWakingUp(false);
    }
  };

  const fetchExtraFeatures = async () => {
    const fetchSafe = async (url, setter) => {
      try {
        const res = await fetch(url);
        if (res.ok) {
          const json = await res.json();
          if (json.status === "success") {
            setter(json.data.signals || json.data.leaderboard || json.data);
          }
        }
      } catch (e) {
        console.error(`Failed to fetch ${url}`, e);
      }
    };

    try {
      const sigRes = await fetch(`${API_BASE_URL}/signals?days=5`);
      if (sigRes.ok) {
        const sigJson = await sigRes.json();
        if (sigJson.status === "success") setSignals(sigJson.data.signals);
      }
    } catch(e) {}

    try {
      const predRes = await fetch(`${API_BASE_URL}/predict-tomorrow`);
      if (predRes.ok) {
        const predJson = await predRes.json();
        if (predJson.status === "success") setTomorrowPrediction(predJson.data);
      }
    } catch(e) {}

    try {
      const ldRes = await fetch(`${API_BASE_URL}/models`);
      if (ldRes.ok) {
        const ldJson = await ldRes.json();
        if (ldJson.status === "success") setLeaderboard(ldJson.data.leaderboard);
      }
    } catch(e) {}

    try {
      const macroRes = await fetch(`${API_BASE_URL}/macro`);
      if (macroRes.ok) {
        const macroJson = await macroRes.json();
        if (macroJson.status === "success") setMacroData(macroJson.data);
      }
    } catch(e) {}

    try {
      const intellRes = await fetch(`${API_BASE_URL}/intelligence`);
      if (intellRes.ok) {
        const intellJson = await intellRes.json();
        if (intellJson.status === "success") setIntelligenceData(intellJson.data);
      }
    } catch(e) {}

    try {
      const wave2Res = await fetch(`${API_BASE_URL}/wave2_data`);
      if (wave2Res.ok) {
        const wave2Json = await wave2Res.json();
        if (wave2Json.status === "success") setWave2Data(wave2Json.data);
      }
    } catch(e) {}

    try {
      const newsRes = await fetch(`${API_BASE_URL}/news`);
      if (newsRes.ok) {
        const newsJson = await newsRes.json();
        if (newsJson.status === "success") setNewsData(newsJson.data);
      }
    } catch(e) {}

    try {
      const agentsRes = await fetch(`${API_BASE_URL}/agents`);
      if (agentsRes.ok) {
        const agentsJson = await agentsRes.json();
        if (agentsJson.status === "success") setAgentsData(agentsJson.data);
      }
    } catch(e) {}

    try {
      const rlRes = await fetch(`${API_BASE_URL}/rl_status`);
      if (rlRes.ok) {
        const rlJson = await rlRes.json();
        if (rlJson.status === "success") setRlData(rlJson.data);
      }
    } catch(e) {}
  };

  // Portfolio Database Syncing
  const setupPushNotifications = async () => {
    if (typeof window === 'undefined' || !('serviceWorker' in navigator) || !('PushManager' in window)) {
      console.log('Push notifications are not supported in this browser.');
      return;
    }

    try {
      // 1. Register service worker
      const registration = await navigator.serviceWorker.register('/sw.js');

      // 2. Fetch VAPID Public Key from backend
      const res = await fetch(`${API_BASE_URL}/vapid-public-key`);
      const json = await res.json();
      if (json.status !== 'success' || !json.data.public_key) {
        console.error('Failed to get VAPID public key.');
        return;
      }
      const vapidPublicKey = json.data.public_key;

      // Convert VAPID key from base64url to Uint8Array
      const urlBase64ToUint8Array = (base64String) => {
        const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
        const base64 = (base64String + padding)
          .replace(/\-/g, '+')
          .replace(/_/g, '/');
        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);
        for (let i = 0; i < rawData.length; ++i) {
          outputArray[i] = rawData.charCodeAt(i);
        }
        return outputArray;
      };

      const convertedVapidKey = urlBase64ToUint8Array(vapidPublicKey);

      // 3. Request permissions & subscribe
      let subscription = await registration.pushManager.getSubscription();
      if (!subscription) {
        subscription = await registration.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: convertedVapidKey
        });
      }

      // 4. Send subscription to backend
      const token = localStorage.getItem('access_token');
      if (token) {
        await fetch(`${API_BASE_URL}/subscribe`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify(subscription)
        });
        console.log('Successfully subscribed to background Web Push notifications!');
      }
    } catch (err) {
      console.warn('Error setting up Web Push notifications:', err);
    }
  };

  useEffect(() => {
    if (!userId) return;

    setupPushNotifications();

    // Fetch Portfolio on login
    const token = localStorage.getItem('access_token');
    if (!token) return;

    fetch(`${API_BASE_URL}/portfolio`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
      .then(async (res) => {
        if (res.status === 401) {
          // Token is invalid/expired (e.g. database reset)
          localStorage.removeItem('access_token');
          localStorage.removeItem('user_id');
          setUserId(null);
          toast.error("Session expired. Please log in again.");
          return null;
        }
        return res.json();
      })
      .then(data => {
        if (data && data.status === "success" && data.data.total_invested !== undefined) {
          setTotalInvestedInput(data.data.total_invested.toString());
          setUnits(data.data.units.toString());
        }
      })
      .catch(err => console.error("Failed to fetch portfolio", err));
  }, [userId]);

  useEffect(() => {
    // Auto-save portfolio when changed, debounced
    if (!userId || !totalInvestedInput || !units) return;

    const delayDebounceFn = setTimeout(() => {
      const token = localStorage.getItem('access_token');
      if (!token) return;

      fetch(`${API_BASE_URL}/portfolio`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          total_invested: parseFloat(totalInvestedInput) || 0,
          units: parseFloat(units) || 0
        })
      }).catch(err => console.error("Failed to save portfolio", err));
    }, 1000);

    return () => clearTimeout(delayDebounceFn);
  }, [totalInvestedInput, units, userId]);

  const handleSavePortfolio = async (e) => {
    if (e) e.preventDefault();
    if (!userId) {
      toast.error("Please sign in to save your portfolio");
      return;
    }
    const token = localStorage.getItem('access_token');
    if (!token) return;

    try {
      const res = await fetch(`${API_BASE_URL}/portfolio`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          total_invested: parseFloat(totalInvestedInput) || 0,
          units: parseFloat(units) || 0
        })
      });
      if (res.ok) {
        toast.success("Portfolio saved successfully!");
      } else {
        toast.error("Failed to save portfolio");
      }
    } catch (err) {
      console.error(err);
      toast.error("Error saving portfolio");
    }
  };

  const handleAuthSubmit = async (e) => {
    e.preventDefault();
    const endpoint = authMode === 'login' ? '/login' : '/register';

    try {
      let body, headers;
      if (authMode === 'login') {
        body = new URLSearchParams();
        body.append('username', authUsername);
        body.append('password', authPassword);
        headers = { 'Content-Type': 'application/x-www-form-urlencoded' };
      } else {
        body = JSON.stringify({ username: authUsername, password: authPassword });
        headers = { 'Content-Type': 'application/json' };
      }

      const res = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        headers,
        body
      });
      const data = await res.json();

      if (res.ok) {
        if (authMode === 'login') {
          localStorage.setItem('access_token', data.access_token);
          localStorage.setItem('user_id', data.user_id);
          setUserId(data.user_id);
          setShowAuthModal(false);
          toast.success("Logged in successfully!");
        } else {
          toast.success("Registered! You can now log in.");
          setAuthMode('login');
        }
      } else {
        toast.error(data.detail || "Authentication failed");
      }
    } catch (err) {
      toast.error("Network error");
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_id');
    setUserId(null);
    setTotalInvestedInput("");
    setUnits("");
    toast.success("Logged out");
  };

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
          if (json.macro) {
            setMacroData(json.macro);
          }
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
        toast.success('≡ƒôê BUY ALERT: AI detects upward momentum!', { duration: 5000 });
      } else if (latestSignal.Action === 'SELL') {
        toast.error('≡ƒÜ¿ URGENT: Market dropping! AI predicts a fall.', { duration: 6000 });
      } else if (previousSignalRef.current !== null) {
        toast('Market stabilized. AI suggests HOLD.', { icon: 'ΓÜû∩╕Å', duration: 4000 });
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

    const token = localStorage.getItem('access_token');
    const headers = { 'Content-Type': 'application/json' };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    try {
      const res = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: headers,
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
      <div className="flex flex-col h-screen items-center justify-center bg-[#E8EFE9] text-gray-900 space-y-4">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-[#5A67D8]"></div>
        {wakingUp && (
          <p className="text-sm text-gray-600 font-medium animate-pulse">
            Waking up AI Engine (this may take up to a minute)...
          </p>
        )}
      </div>
    );
  }

  if (!data) return <div className="p-10 text-gray-900 bg-[#E8EFE9] h-screen">Failed to load dashboard. Ensure FastAPI is running on port 8000.</div>;

  const { current_price, forecast, risk_metrics, active_model, ohlc } = data;

  // Chart Setup
  const candlestickOptions = {
    chart: { type: 'candlestick', background: 'transparent', toolbar: { show: false } },
    theme: { mode: 'light' },
    plotOptions: {
      candlestick: { colors: { upward: '#10B981', downward: '#EF4444' } }
    },
    xaxis: { type: 'datetime', labels: { style: { colors: '#6B7280' } } },
    yaxis: {
      tooltip: { enabled: true },
      labels: { style: { colors: '#6B7280' }, formatter: (value) => "₹" + value.toFixed(2) }
    },
    grid: { borderColor: '#E5E7EB' },
  };


  const getFilteredOhlc = () => {
    if (!ohlc || ohlc.length === 0) return [];

    // Parse date strings to local midnight timestamps for correct alignment
    const sorted = [...ohlc].map(item => {
      const parts = item.x.split('-');
      let ts = 0;
      if (parts.length === 3) {
        ts = new Date(parts[0], parts[1] - 1, parts[2]).getTime();
      } else {
        ts = new Date(item.x).getTime();
      }
      return {
        ...item,
        timestamp: ts
      };
    }).sort((a, b) => a.timestamp - b.timestamp);

    const latestDate = sorted[sorted.length - 1].timestamp;

    let cutoff = 0;
    const day = 24 * 60 * 60 * 1000;

    switch (chartTimeframe) {
      case '1D': cutoff = latestDate - 1 * day; break;
      case '5D': cutoff = latestDate - 5 * day; break;
      case '1M': cutoff = latestDate - 30 * day; break;
      case '6M': cutoff = latestDate - 180 * day; break;
      case 'YTD':
        const yearStart = new Date(new Date(latestDate).getFullYear(), 0, 1).getTime();
        cutoff = yearStart;
        break;
      case '1Y': cutoff = latestDate - 365 * day; break;
      case '5Y': cutoff = latestDate - 5 * 365 * day; break;
      case 'MAX': cutoff = 0; break;
      default: cutoff = latestDate - 30 * day;
    }

    return sorted.filter(item => item.timestamp >= cutoff);
  };

  const lineSeriesData = [{
    name: 'Close Price',
    data: getFilteredOhlc().map(item => ({ x: item.timestamp, y: item.y[3] }))
  }];

  const lineOptions = {
    chart: { type: 'area', background: 'transparent', toolbar: { show: false }, animations: { enabled: false } },
    theme: { mode: 'light' },
    colors: ['#5A67D8'], // Indigo color
    fill: {
      type: 'gradient',
      gradient: { shadeIntensity: 1, opacityFrom: 0.4, opacityTo: 0.05, stops: [0, 100] }
    },
    stroke: { curve: 'smooth', width: 2 },
    xaxis: { 
      type: 'datetime', 
      labels: { style: { colors: '#6B7280' } }, 
      axisBorder: { show: true, color: '#E5E7EB' }, 
      axisTicks: { show: true, color: '#E5E7EB' } 
    },
    yaxis: {
      opposite: true,
      decimalsInFloat: 2,
      labels: { formatter: (value) => '₹' + value.toFixed(2), style: { colors: '#6B7280' } }
    },
    grid: { borderColor: '#E5E7EB', strokeDashArray: 4, padding: { left: 10, right: 10 } },
    dataLabels: { enabled: false },
    tooltip: { theme: 'light', x: { format: 'dd MMM yyyy' } }
  };

  const candlestickSeries = [{
    name: 'candle',
    data: ohlc || []
  }];

  const renderSignalBadge = (sig) => {
    if (sig === 'BUY') return <span className="px-2 py-1 bg-emerald-50 text-emerald-700 rounded-md text-xs font-bold border border-[#5A67D8]/50">BUY</span>;
    if (sig === 'SELL') return <span className="px-2 py-1 bg-rose-50 text-rose-700 rounded-md text-xs font-bold border border-red-500/50">SELL</span>;
    return <span className="px-2 py-1 bg-emerald-900/30 text-emerald-400 rounded-md text-xs font-bold border border-[#5A67D8]/30">HOLD</span>;
  };

  // Portfolio Calculations
  let investedAmount = 0;
  let currentValue = 0;
  let profitLoss = 0;
  let profitLossPercent = 0;
  let smartAdvice = "Enter your portfolio details in the Manage Portfolio section below to generate custom AI advice.";

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
    <div className="min-h-screen text-gray-900 font-sans flex overflow-hidden" style={{ background: '#F0F4F8' }}>
      <Toaster position="top-right" toastOptions={{
        style: { background: '#FFFFFF', color: '#111827', border: '1px solid #E5E7EB', borderRadius: '12px', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)' }
      }} />

      {/* LEFT SIDEBAR */}
      {/* SIDEBAR */}
      <aside className="w-64 bg-white border-r border-gray-100 flex flex-col hidden md:flex z-30 shadow-sm relative">
        <div className="p-5 border-b border-gray-100">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center font-black text-sm shadow-sm" style={{ background: 'linear-gradient(135deg,#f59e0b,#d97706)', color: 'white' }}>G</div>
            <div>
              <h1 className="text-base font-black text-gray-900 tracking-tight">GoldBeES</h1>
              <p className="text-[10px] font-medium text-gray-400">Market Intelligence</p>
            </div>
          </div>
        </div>
        <div className="px-4 pt-5 flex-1">
          <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest px-3 mb-3">Navigation</p>
          <nav className="space-y-1">
            {[
              { key: 'overview', label: 'Dashboard', Icon: BarChart2 },
              { key: 'ailab', label: 'AI Lab', Icon: Cpu },
              { key: 'simulation', label: 'Risk Console', Icon: ShieldCheck },
            ].map(({ key, label, Icon }) => (
              <div key={key} onClick={() => setActiveTab(key)} className={`flex items-center px-3 py-3 rounded-xl cursor-pointer transition-all font-semibold text-sm ${activeTab === key ? 'bg-indigo-50 text-indigo-600' : 'text-gray-500 hover:bg-gray-50 hover:text-gray-800'}`}>
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center mr-3 ${activeTab === key ? 'bg-indigo-100' : 'bg-gray-100'}`}>
                  <Icon className={`w-4 h-4 ${activeTab === key ? 'text-indigo-600' : 'text-gray-400'}`} />
                </div>
                {label}
                {activeTab === key && <div className="ml-auto w-1.5 h-1.5 rounded-full bg-indigo-500" />}
              </div>
            ))}
          </nav>
        </div>
        <div className="mx-4 mb-4 p-3 rounded-xl bg-emerald-50 border border-emerald-100">
          <div className="flex items-center space-x-2 mb-1">
            <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs font-bold text-emerald-600">Live Data Feed</span>
          </div>
          <p className="text-[10px] text-emerald-500">Market data · updates every 30s</p>
        </div>
        <div className="p-4 border-t border-gray-100 flex items-center justify-between">
          <span className="text-xs text-gray-400 flex items-center cursor-pointer hover:text-gray-600"><Info className="w-3.5 h-3.5 mr-1.5" />Help</span>
          <span className="text-xs text-gray-400 flex items-center cursor-pointer hover:text-gray-600"><Lock className="w-3.5 h-3.5 mr-1.5" />Settings</span>
        </div>
      </aside>

      {/* MAIN CONTENT AREA */}
      <main className="flex-1 flex flex-col h-screen overflow-y-auto overflow-x-hidden">

        {/* TOP HEADER */}
        <header className="bg-white px-4 sm:px-6 py-3 flex items-center justify-between border-b border-gray-100 sticky top-0 z-20 shadow-sm">
          <div className="hidden md:flex items-center space-x-3">
            <div className="flex items-center text-sm font-medium text-gray-500 bg-gray-50 px-4 py-2 rounded-lg border border-gray-100">
              <Calendar className="w-4 h-4 mr-2 text-indigo-400" /> GoldBeES Market Analyzer
            </div>
            {data && (
              <div className="flex items-center space-x-2 px-3 py-2 rounded-lg bg-amber-50 border border-amber-100">
                <div className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
                <span className="text-sm font-black text-amber-700 font-mono">₹{current_price.toFixed(2)}</span>
                <span className="text-xs text-amber-500">GOLDBEES</span>
              </div>
            )}
          </div>
          <div className="flex md:hidden items-center">
            <div className="w-8 h-8 rounded-lg mr-2 flex items-center justify-center text-white font-black text-xs" style={{ background: 'linear-gradient(135deg,#f59e0b,#d97706)' }}>G</div>
            <span className="font-black text-gray-900 text-sm">GoldBeES</span>
          </div>
          <div className="flex items-center space-x-3 sm:space-x-4">
            <a href={`${API_BASE_URL}/report`} target="_blank" rel="noreferrer" className="text-gray-400 hover:text-gray-600 transition-colors"><Download className="w-5 h-5" /></a>
            {userId ? (
              <button onClick={handleLogout} className="text-xs sm:text-sm text-red-500 font-semibold hover:text-red-600">Log Out</button>
            ) : (
              <button onClick={() => setShowAuthModal(true)} className="text-xs sm:text-sm text-white font-bold px-3 py-1.5 sm:px-4 sm:py-2 rounded-lg shadow-sm" style={{ background: 'linear-gradient(135deg,#5A67D8,#7C3AED)' }}>Log In</button>
            )}
            <div className="flex items-center space-x-2 cursor-pointer">
              <div className="w-9 h-9 rounded-full flex items-center justify-center border-2 border-indigo-100 shadow-sm" style={{ background: 'linear-gradient(135deg,#EEF2FF,#E0E7FF)' }}>
                <span className="text-indigo-600 font-black text-xs">{userId ? String(userId)[0].toUpperCase() : 'G'}</span>
              </div>
              <div className="hidden sm:block text-sm font-bold text-gray-700">{userId || 'Guest'}</div>
            </div>
          </div>
        </header>

        {/* CONTAINER */}
        <div className="p-6 md:p-8 pb-24 md:pb-8 max-w-[1400px] w-full mx-auto">
          <AnimatePresence mode="wait">
            {activeTab === 'overview' && (
              <motion.div
                key="overview"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                transition={{ duration: 0.25, ease: "easeOut" }}
                className="space-y-6"
              >

                {/* HERO SUMMARY CARDS */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                  <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-1 h-full rounded-l-2xl" style={{ background: 'linear-gradient(180deg,#6366f1,#8b5cf6)' }} />
                    <p className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3 ml-3">Portfolio Value</p>
                    <div className="flex items-end space-x-3 ml-3">
                      <h2 className="text-3xl font-black text-gray-900 font-mono tracking-tight">₹{currentValue.toFixed(2)}</h2>
                      <span className={`font-bold text-xs px-2.5 py-1 rounded-lg mb-1 flex items-center ${profitLoss >= 0 ? 'text-emerald-600 bg-emerald-50' : 'text-rose-600 bg-rose-50'}`}>
                        {profitLoss >= 0 ? <TrendingUp className="w-3 h-3 mr-1" /> : <TrendingDown className="w-3 h-3 mr-1" />}
                        {profitLoss >= 0 ? '+' : ''}₹{profitLoss.toFixed(2)} ({profitLossPercent.toFixed(2)}%)
                      </span>
                    </div>
                  </div>
                  <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-1 h-full rounded-l-2xl bg-amber-400" />
                    <p className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3 ml-3">Total Invested</p>
                    <h2 className="text-3xl font-black text-gray-900 font-mono tracking-tight ml-3">₹{investedAmount.toFixed(2)}</h2>
                  </div>
                  <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-1 h-full rounded-l-2xl bg-emerald-400" />
                    <p className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3 ml-3">Units Held</p>
                    <h2 className="text-3xl font-black text-gray-900 font-mono tracking-tight ml-3">{units || 0} <span className="text-sm text-gray-400 font-semibold">UNITS</span></h2>
                  </div>
                </div>

                {/* MAIN CHART & SIDEBAR GRID */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                  {/* LEFT: CHART AREA */}
                  <motion.div variants={{ hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0, transition: { duration: 0.4, ease: "easeOut" } } }} className="lg:col-span-2 space-y-6">
                    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
                      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start mb-6 space-y-4 sm:space-y-0">
                        <div>
                          <div className="flex items-center mb-2">
                            <div className="w-6 h-6 bg-yellow-100 rounded-md flex items-center justify-center mr-2"><span className="text-yellow-600 font-bold text-xs">G</span></div>
                            <h3 className="font-bold text-gray-900 text-lg">GoldBeES (ETF)</h3>
                          </div>
                          <h2 className="text-3xl font-bold text-gray-900 font-mono">₹{current_price.toFixed(2)}</h2>
                          <div className="mt-1 text-sm">
                            <span className="text-gray-500 font-medium">Next Day Prediction: </span>
                            <span className="font-bold text-indigo-600">₹{forecast?.Forecast_1_Day?.toFixed(2) || '---'}</span>
                          </div>
                        </div>
                        <div className="flex space-x-1 overflow-x-auto pb-1 max-w-full no-scrollbar whitespace-nowrap">
                          {['1D', '5D', '1M', 'YTD', '6M', '1Y', '5Y', 'MAX'].map(tf => (
                            <span
                              key={tf}
                              onClick={() => setChartTimeframe(tf)}
                              className={`inline-block px-2.5 py-1.5 text-[10px] sm:text-xs font-semibold rounded-lg cursor-pointer transition-colors ${chartTimeframe === tf ? 'bg-[#5A67D8] text-white shadow-sm shadow-indigo-200' : 'text-gray-500 hover:bg-gray-100'}`}
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
                          <Zap className="w-6 h-6 text-[#5A67D8]" />
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
                          <span className={`inline-block px-4 py-2 rounded-xl text-lg font-bold border ${intelligenceData.market_regime.regime === 'Bull' ? 'bg-emerald-50 text-emerald-700 border-emerald-500/20' :
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
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mt-8">
                  {/* Left: Manage Portfolio */}
                  <motion.div variants={{ hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0, transition: { duration: 0.4, ease: "easeOut" } } }} className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 lg:col-span-2">
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

                  {/* Right: Tomorrow's Forecast */}
                  {tomorrowPrediction && (
                    <motion.div variants={{ hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0, transition: { duration: 0.4, ease: "easeOut", delay: 0.1 } } }} className="bg-[#fcfdfc] rounded-2xl border-2 border-yellow-100 shadow-sm p-6 relative overflow-hidden flex flex-col justify-between">
                      <div>
                        <div className="flex justify-between items-center mb-4">
                          <h3 className="font-bold text-gray-900 text-sm">Tomorrow's Forecast</h3>
                          <span className={`text-xs font-bold px-2 py-1 rounded-md ${tomorrowPrediction.Direction === 'BULLISH' ? 'bg-emerald-50 text-emerald-600' : tomorrowPrediction.Direction === 'BEARISH' ? 'bg-rose-50 text-rose-600' : 'bg-yellow-50 text-yellow-600'}`}>
                            {tomorrowPrediction.Direction}
                          </span>
                        </div>
                        <div className="flex items-end space-x-3 mb-6">
                          <h2 className="text-3xl font-bold text-gray-900 font-mono">₹{tomorrowPrediction.Predicted_Close.toFixed(2)}</h2>
                          <span className="text-gray-400 font-mono text-xs mb-1">[{tomorrowPrediction.Conformal_Lower.toFixed(2)} - {tomorrowPrediction.Conformal_Upper.toFixed(2)}]</span>
                        </div>
                        
                        <div className="grid grid-cols-2 gap-4 mb-6">
                          <div>
                            <p className="text-xs font-semibold text-gray-400 mb-1">Expected Return</p>
                            <p className={`text-sm font-bold ${tomorrowPrediction.Expected_Return_Pct >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>{tomorrowPrediction.Expected_Return_Pct > 0 ? '+' : ''}{tomorrowPrediction.Expected_Return_Pct}%</p>
                          </div>
                          <div>
                            <p className="text-xs font-semibold text-gray-400 mb-1">Forecasted Vol</p>
                            <p className="text-sm font-bold text-gray-900">{tomorrowPrediction.Predicted_Volatility}%</p>
                          </div>
                          <div>
                            <p className="text-xs font-semibold text-gray-400 mb-1">Prob Breakout 1%</p>
                            <p className="text-sm font-bold text-gray-900">{tomorrowPrediction.Prob_Move_1pct}%</p>
                          </div>
                          <div>
                            <p className="text-xs font-semibold text-gray-400 mb-1">Prob Breakout 2%</p>
                            <p className="text-sm font-bold text-gray-900">{tomorrowPrediction.Prob_Move_2pct}%</p>
                          </div>
                        </div>
                      </div>

                      <div className="pt-4 border-t border-gray-100">
                        <h4 className="text-xs font-bold text-gray-900 mb-2">AI Explainer (SHAP)</h4>
                        <p className="text-xs text-gray-500 leading-relaxed italic mb-4">
                          {tomorrowPrediction.Reasoning}
                        </p>
                      </div>
                      
                      {tomorrowPrediction.Consensus && tomorrowPrediction.Deep_Confidence && (
                        <div className="pt-4 border-t border-gray-100">
                          <h4 className="text-xs font-bold text-gray-900 mb-3 flex items-center"><Target className="w-4 h-4 mr-2 text-indigo-500" /> Deep Stacking Consensus</h4>
                          <div className="space-y-3">
                            {Object.entries(tomorrowPrediction.Consensus).map(([model, pred]) => (
                              <div key={model} className="flex justify-between items-center bg-gray-50 px-3 py-2 rounded-lg">
                                <span className="text-xs font-semibold text-gray-600">{model}</span>
                                <span className="text-sm font-bold text-gray-900 font-mono">₹{pred.toFixed(2)}</span>
                              </div>
                            ))}
                          </div>
                          
                          <div className="mt-4 bg-indigo-50 p-4 rounded-xl border border-indigo-100">
                            <h4 className="text-xs font-bold text-indigo-900 mb-2 flex items-center"><Activity className="w-4 h-4 mr-2 text-indigo-500" /> Deep Confidence (MC Dropout)</h4>
                            <div className="flex justify-between items-center">
                              <span className="text-xs text-indigo-700">LSTM Volatility</span>
                              <span className="text-xs font-bold text-indigo-900">{(tomorrowPrediction.Deep_Confidence.LSTM_Uncertainty * 100).toFixed(4)}%</span>
                            </div>
                            <div className="flex justify-between items-center mt-1">
                              <span className="text-xs text-indigo-700">Transformer Volatility</span>
                              <span className="text-xs font-bold text-indigo-900">{(tomorrowPrediction.Deep_Confidence.PatchTST_Uncertainty * 100).toFixed(4)}%</span>
                            </div>
                          </div>
                        </div>
                      )}
                    </motion.div>
                  )}
                </div>

              </motion.div>
            )}

            {activeTab === 'ailab' && (
              <motion.div
                key="ailab"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                transition={{ duration: 0.25, ease: "easeOut" }}
                className="space-y-6"
              >

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
                          <div className={`px-4 py-1.5 rounded-full text-xs font-bold mb-3 border ${agent.signal === 'BUY' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' :
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
                        <div className={`px-6 py-3 rounded-xl text-2xl font-bold border ${agentsData.final_signal === 'BUY' ? 'bg-emerald-500 text-white border-emerald-600' :
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
                          <p className="font-bold text-gray-700 mb-1 flex items-center"><Info className="w-3 h-3 mr-1" /> Recommendation Detail:</p>
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
              <motion.div
                key="simulation"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                transition={{ duration: 0.25, ease: "easeOut" }}
                className="space-y-6"
              >

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
          </AnimatePresence>

        </div>
      </main>

      {/* MOBILE BOTTOM NAVIGATION */}
      <div className="md:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-gray-100 px-6 py-2 flex justify-around items-center z-40 shadow-lg">
        <div
          onClick={() => setActiveTab('overview')}
          className={`flex flex-col items-center justify-center space-y-0.5 cursor-pointer p-2 rounded-xl transition-all ${activeTab === 'overview' ? 'text-[#5A67D8]' : 'text-gray-400'}`}
        >
          <BarChart2 className="w-5 h-5" />
          <span className="text-[10px] font-bold">Dashboard</span>
        </div>
        <div
          onClick={() => setActiveTab('ailab')}
          className={`flex flex-col items-center justify-center space-y-0.5 cursor-pointer p-2 rounded-xl transition-all ${activeTab === 'ailab' ? 'text-[#5A67D8]' : 'text-gray-400'}`}
        >
          <Cpu className="w-5 h-5" />
          <span className="text-[10px] font-bold">AI Lab</span>
        </div>
        <div
          onClick={() => setActiveTab('simulation')}
          className={`flex flex-col items-center justify-center space-y-0.5 cursor-pointer p-2 rounded-xl transition-all ${activeTab === 'simulation' ? 'text-[#5A67D8]' : 'text-gray-400'}`}
        >
          <ShieldCheck className="w-5 h-5" />
          <span className="text-[10px] font-bold">Risk</span>
        </div>
      </div>

      {/* Floating Chatbot */}
      <div className="fixed bottom-20 md:bottom-6 right-4 sm:right-6 z-50">
        {isChatOpen ? (
          <div className="bg-white border border-gray-100 shadow-2xl w-[calc(100vw-2rem)] sm:w-80 h-96 rounded-2xl flex flex-col overflow-hidden">
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
  );
}
