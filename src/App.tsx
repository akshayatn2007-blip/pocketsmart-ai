import React, { useState, useEffect } from 'react';
import {
  Home,
  PartyPopper,
  Sparkles,
  History,
  Download,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  Upload,
  LogOut,
  LayoutDashboard,
  ArrowRight,
  ShieldCheck,
} from 'lucide-react';

interface User { id: number; name: string; email: string; }
interface BudgetSummary { total_budget: number; estimated_total: number; remaining_budget: number; is_within_budget: boolean; }
interface Allocation { category: string; allocated_amount: number; percentage: number; }
interface Item { name: string; category: string; estimated_price: number; quantity?: number; reason: string; platform: string; purchase_link: string; specs?: string; }
interface PlanResult { planner_type: string; title: string; summary: string; ai_analysis?: string; budget_summary: BudgetSummary; allocations: Allocation[]; items: Item[]; recommendation_id?: number; }
interface HistoryItem { id: number; planner_type: string; budget: number; created_at: string; response_data: PlanResult; }

const fmtINR = (n: number) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(n);

export default function App() {
  const [view, setView] = useState<'landing' | 'dashboard' | 'home_planner' | 'home_results' | 'party_planner' | 'party_results' | 'jewelry_planner' | 'jewelry_results' | 'history' | 'testimonials' | 'login' | 'register'>('landing');
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [authToken, setAuthToken] = useState<string | null>(localStorage.getItem('pocketsmart_token'));
  const [currentPlan, setCurrentPlan] = useState<PlanResult | null>(null);
  const [historyList, setHistoryList] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState<{ type: 'err' | 'ok'; text: string } | null>(null);

  // Forms
  const [auth, setAuth] = useState({ name: '', email: '', password: '', confirm: '' });
  const [home, setHome] = useState({ budget: 50000, room: 'Living Room', num: 1, style: 'Modern Minimalist', items: '3-Seater Sofa, Coffee Table, Floor Lamp, Rug', color: 'Warm Neutrals & Sage Green', notes: '' });
  const [party, setParty] = useState({ budget: 75000, event: 'Birthday', guests: 50, venue: 'Indoor Banquet Hall', food: 'Multi-Cuisine Buffet', decor: 'Themed & Balloon Arch', audio: 'DJ Sound & Lights', city: 'Bengaluru', notes: '' });
  const [jewelry, setJewelry] = useState({ budget: 30000, occasion: 'Wedding', type: 'Complete Set', metal: 'Gold', style: 'Traditional Royal Kundan', color: 'Emerald Green & Gold', desc: 'Sweetheart neckline with gold zari work', notes: '', imgB64: null as string | null, imgName: null as string | null });

  useEffect(() => {
    if (authToken) {
      fetch('/session-info', { headers: { Authorization: `Bearer ${authToken}` } })
        .then((r) => r.json())
        .then((d) => d.authenticated ? setCurrentUser(d.user) : (setCurrentUser(null), localStorage.removeItem('pocketsmart_token'), setAuthToken(null)))
        .catch(() => setCurrentUser(null));
    }
  }, [authToken]);

  useEffect(() => {
    if (view === 'history' || view === 'dashboard') {
      const h: any = authToken ? { Authorization: `Bearer ${authToken}` } : {};
      fetch('/history', { headers: h }).then((r) => r.json()).then((d) => d.records && setHistoryList(d.records)).catch(() => {});
    }
  }, [view, authToken]);

  const handleAuth = async (e: React.FormEvent, isReg: boolean) => {
    e.preventDefault();
    setMsg(null);
    if (isReg && auth.password !== auth.confirm) return setMsg({ type: 'err', text: 'Passwords do not match.' });
    setLoading(true);
    try {
      const endpoint = isReg ? '/register' : '/login';
      const body = isReg ? { name: auth.name, email: auth.email, password: auth.password, confirm_password: auth.confirm } : { email: auth.email, password: auth.password };
      const r = await fetch(endpoint, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
      const d = await r.json();
      if (!r.ok) throw new Error(d.error || 'Authentication error');
      if (d.access_token) {
        localStorage.setItem('pocketsmart_token', d.access_token);
        setAuthToken(d.access_token);
        setCurrentUser(d.user);
        setMsg({ type: 'ok', text: isReg ? 'Account registered!' : 'Welcome back!' });
        setView('dashboard');
      } else {
        setMsg({ type: 'ok', text: 'Registration successful! Please login.' });
        setView('login');
      }
    } catch (err: any) { setMsg({ type: 'err', text: err.message }); }
    finally { setLoading(false); }
  };

  const handlePlanSubmit = async (e: React.FormEvent, url: string, payload: any, resultView: typeof view) => {
    e.preventDefault();
    setLoading(true);
    setMsg(null);
    try {
      const headers: any = { 'Content-Type': 'application/json' };
      if (authToken) headers.Authorization = `Bearer ${authToken}`;
      const r = await fetch(url, { method: 'POST', headers, body: JSON.stringify(payload) });
      const d = await r.json();
      if (!r.ok) throw new Error(d.error || 'Failed to generate recommendations');
      setCurrentPlan(d);
      setView(resultView);
    } catch (err: any) { setMsg({ type: 'err', text: err.message }); }
    finally { setLoading(false); }
  };

  const onImgUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;
    if (f.size > 5 * 1024 * 1024) return setMsg({ type: 'err', text: 'Image exceeds 5MB limit.' });
    setJewelry({ ...jewelry, imgName: f.name });
    const reader = new FileReader();
    reader.onload = (ev) => setJewelry((prev) => ({ ...prev, imgB64: ev.target?.result as string }));
    reader.readAsDataURL(f);
  };

  // Common Results Renderer
  const renderPlanResults = (editView: typeof view, tag: string) => currentPlan && (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider bg-indigo-100 text-indigo-700 px-2.5 py-1 rounded-md">{tag}</span>
          <h2 className="text-2xl font-bold text-slate-900 mt-2">{currentPlan.title}</h2>
          <p className="text-sm text-slate-600 mt-1 max-w-2xl">{currentPlan.summary}</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => setView(editView)} className="text-xs font-semibold px-3 py-2 rounded-lg border border-slate-300 hover:bg-slate-50 transition">Edit Form</button>
          {currentUser && <button onClick={() => setView('history')} className="text-xs font-semibold px-3 py-2 rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 transition">View History</button>}
        </div>
      </div>

      {currentPlan.ai_analysis && (
        <div className="bg-gradient-to-r from-emerald-50 via-teal-50 to-indigo-50 border border-emerald-200 rounded-2xl p-4 shadow-xs">
          <div className="flex items-center gap-2 text-emerald-800 font-bold text-sm mb-1"><Sparkles className="w-4 h-4 text-emerald-600" /><span>Gemini Vision & Styling Notes</span></div>
          <p className="text-xs sm:text-sm text-slate-700 leading-relaxed">{currentPlan.ai_analysis}</p>
        </div>
      )}

      {/* Budget Summary Bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 bg-white border border-slate-200 rounded-2xl p-5 shadow-xs">
        <div><div className="text-[11px] font-bold text-slate-400 uppercase">Budget Limit</div><div className="text-xl font-black text-slate-900 mt-0.5">{fmtINR(currentPlan.budget_summary.total_budget)}</div></div>
        <div><div className="text-[11px] font-bold text-slate-400 uppercase">Estimated Total</div><div className="text-xl font-black text-indigo-600 mt-0.5">{fmtINR(currentPlan.budget_summary.estimated_total)}</div></div>
        <div><div className="text-[11px] font-bold text-slate-400 uppercase">Remaining Savings</div><div className="text-xl font-black text-emerald-600 mt-0.5">{fmtINR(currentPlan.budget_summary.remaining_budget)}</div></div>
        <div>
          <div className="text-[11px] font-bold text-slate-400 uppercase">Status</div>
          <div className="mt-1">{currentPlan.budget_summary.is_within_budget ? <span className="inline-flex items-center gap-1 text-xs font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200"><CheckCircle2 className="w-3.5 h-3.5" />Within Budget</span> : <span className="inline-flex items-center gap-1 text-xs font-bold text-rose-700 bg-rose-50 px-2 py-0.5 rounded-full border border-rose-200"><AlertCircle className="w-3.5 h-3.5" />Over Budget</span>}</div>
        </div>
      </div>

      {/* Allocations */}
      {currentPlan.allocations?.length > 0 && (
        <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs">
          <h3 className="text-sm font-bold text-slate-900 mb-3">Category Budget Distribution</h3>
          <div className="w-full h-3 bg-slate-100 rounded-full overflow-hidden flex">
            {currentPlan.allocations.map((a, i) => {
              const c = ['bg-indigo-600', 'bg-cyan-500', 'bg-violet-500', 'bg-emerald-500'];
              return <div key={i} className={`h-full ${c[i % 4]}`} style={{ width: `${a.percentage}%` }} title={`${a.category}: ${a.percentage}%`}></div>;
            })}
          </div>
          <div className="flex flex-wrap gap-4 mt-3">
            {currentPlan.allocations.map((a, i) => {
              const dots = ['bg-indigo-600', 'bg-cyan-500', 'bg-violet-500', 'bg-emerald-500'];
              return <div key={i} className="flex items-center gap-1.5 text-xs text-slate-700"><span className={`w-2.5 h-2.5 rounded-full ${dots[i % 4]}`}></span><span className="font-semibold">{a.category}:</span><span>{fmtINR(a.allocated_amount)} ({a.percentage}%)</span></div>;
            })}
          </div>
        </div>
      )}

      {/* Items */}
      <div>
        <h3 className="text-lg font-bold text-slate-900 mb-4">Recommended Products & Vendors</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {currentPlan.items.map((item, idx) => (
            <div key={idx} className="bg-white border border-slate-200 rounded-xl p-5 flex flex-col justify-between shadow-xs hover:shadow-md transition">
              <div>
                <div className="flex items-center justify-between gap-2 mb-2">
                  <span className="text-[11px] font-bold text-slate-500 bg-slate-100 px-2 py-0.5 rounded">{item.category}</span>
                  <span className="text-[11px] font-semibold text-indigo-700 bg-indigo-50 border border-indigo-200 px-2 py-0.5 rounded">{item.platform}</span>
                </div>
                <h4 className="font-bold text-slate-900 text-base mb-1">{item.name}</h4>
                <div className="text-lg font-black text-indigo-600 mb-2">{fmtINR(item.estimated_price)}</div>
                <p className="text-xs text-slate-600 mb-3">{item.reason}</p>
                {item.specs && <div className="text-[11px] text-slate-500 bg-slate-50 p-2 rounded mb-4 border border-slate-100"><strong>Specs:</strong> {item.specs}</div>}
              </div>
              <a href={item.purchase_link} target="_blank" rel="noopener noreferrer" className="w-full bg-slate-50 hover:bg-indigo-50 hover:border-indigo-300 text-slate-800 hover:text-indigo-700 border border-slate-200 text-xs font-bold py-2 rounded-lg transition flex items-center justify-center gap-1.5">
                <span>Find on {item.platform}</span><ExternalLink className="w-3.5 h-3.5" />
              </a>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900 font-sans">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-indigo-700 via-indigo-600 to-violet-700 text-white px-4 py-2 text-xs md:text-sm font-medium flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-2">
          <span className="bg-white/20 px-2 py-0.5 rounded text-[11px] font-bold uppercase">FastAPI + Gemini GenAI</span>
          <span className="hidden sm:inline">PocketSmart AI: Smart Budget & Multi-Vendor Recommendation Assistant</span>
        </div>
        <a href="/api/export-project-zip" download="PocketSmart-AI.zip" className="bg-emerald-500 hover:bg-emerald-600 text-white px-3 py-1 rounded text-xs font-semibold flex items-center gap-1.5 transition shadow">
          <Download className="w-3.5 h-3.5" /><span>Download Python ZIP</span>
        </a>
      </div>

      {/* Header */}
      <header className="sticky top-0 z-50 bg-white/95 backdrop-blur border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <div onClick={() => setView('landing')} className="flex items-center gap-2 cursor-pointer select-none">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-600 to-violet-600 flex items-center justify-center text-white font-black text-lg shadow-md shadow-indigo-200">P</div>
            <div className="flex items-center gap-1"><span className="font-extrabold text-xl tracking-tight text-slate-900">PocketSmart</span><span className="bg-indigo-600 text-white text-[11px] font-bold px-1.5 py-0.5 rounded">AI</span></div>
          </div>

          <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-slate-600">
            <button onClick={() => setView('landing')} className={`hover:text-indigo-600 ${view === 'landing' ? 'text-indigo-600 font-bold' : ''}`}>Home</button>
            <button onClick={() => setView('home_planner')} className={`hover:text-indigo-600 flex items-center gap-1.5 ${view.includes('home') ? 'text-indigo-600 font-bold' : ''}`}><Home className="w-4 h-4" /> Home Interior</button>
            <button onClick={() => setView('party_planner')} className={`hover:text-indigo-600 flex items-center gap-1.5 ${view.includes('party') ? 'text-indigo-600 font-bold' : ''}`}><PartyPopper className="w-4 h-4" /> Party Planner</button>
            <button onClick={() => setView('jewelry_planner')} className={`hover:text-indigo-600 flex items-center gap-1.5 ${view.includes('jewelry') ? 'text-indigo-600 font-bold' : ''}`}><Sparkles className="w-4 h-4" /> Jewelry & Outfit</button>
            <button onClick={() => setView('testimonials')} className={`hover:text-indigo-600 ${view === 'testimonials' ? 'text-indigo-600 font-bold' : ''}`}>Testimonials</button>
          </nav>

          <div className="flex items-center gap-3">
            {currentUser ? (
              <div className="flex items-center gap-2">
                <button onClick={() => setView('dashboard')} className={`text-sm font-semibold flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 ${view === 'dashboard' ? 'bg-indigo-50 border-indigo-200 text-indigo-700' : 'text-slate-700'}`}><LayoutDashboard className="w-4 h-4 text-indigo-600" /><span>Dashboard</span></button>
                <button onClick={() => setView('history')} className={`text-sm font-semibold flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 ${view === 'history' ? 'bg-indigo-50 border-indigo-200 text-indigo-700' : 'text-slate-700'}`}><History className="w-4 h-4 text-indigo-600" /><span className="hidden sm:inline">History</span></button>
                <button onClick={() => { localStorage.removeItem('pocketsmart_token'); setAuthToken(null); setCurrentUser(null); setView('landing'); }} className="text-xs font-semibold text-red-600 hover:bg-red-50 p-2 rounded-lg border border-red-200"><LogOut className="w-4 h-4" /></button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <button onClick={() => { setView('login'); setMsg(null); }} className="text-sm font-semibold text-slate-700 hover:text-indigo-600 px-3 py-1.5">Sign In</button>
                <button onClick={() => { setView('register'); setMsg(null); }} className="text-sm font-semibold bg-indigo-600 hover:bg-indigo-700 text-white px-3.5 py-1.5 rounded-lg shadow-sm">Register</button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Notification Toast */}
      {msg && (
        <div className="max-w-4xl mx-auto mt-4 px-4 w-full">
          <div className={`text-sm px-4 py-3 rounded-lg flex items-center justify-between border ${msg.type === 'err' ? 'bg-red-50 border-red-200 text-red-700' : 'bg-emerald-50 border-emerald-200 text-emerald-800'}`}>
            <span>{msg.text}</span>
            <button onClick={() => setMsg(null)} className="font-bold ml-2">×</button>
          </div>
        </div>
      )}

      {/* Main View Area */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 py-6">
        {/* 1. LANDING */}
        {view === 'landing' && (
          <div className="space-y-16 py-6">
            <div className="text-center max-w-3xl mx-auto pt-6 pb-2">
              <div className="inline-flex items-center gap-2 bg-indigo-50 border border-indigo-200/60 text-indigo-700 text-xs font-semibold px-3 py-1.5 rounded-full mb-6">
                <Sparkles className="w-3.5 h-3.5 text-indigo-600" /><span>GenAI-Powered Budget & Multi-Vendor Engine</span>
              </div>
              <h1 className="text-4xl sm:text-5xl font-black text-slate-900 tracking-tight leading-tight">
                Plan Smarter, Spend Within Limits with <span className="bg-gradient-to-r from-indigo-600 via-violet-600 to-indigo-800 bg-clip-text text-transparent">PocketSmart AI</span>
              </h1>
              <p className="mt-5 text-lg text-slate-600 max-w-2xl mx-auto">Intelligent budget apportionment and personalized recommendations for Home Interiors, Events & Parties, and Matching Jewelry with outfit visual analysis.</p>
              <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
                <button onClick={() => setView('home_planner')} className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold px-6 py-3 rounded-xl shadow-md flex items-center gap-2 transition">
                  <span>Start Planning</span><ArrowRight className="w-4 h-4" />
                </button>
                <a href="/api/export-project-zip" download="PocketSmart-AI.zip" className="bg-white hover:bg-slate-50 text-slate-800 font-semibold px-5 py-3 rounded-xl border border-slate-300 shadow-xs flex items-center gap-2 transition">
                  <Download className="w-4 h-4 text-emerald-600" /><span>Download Python Source</span>
                </a>
              </div>
            </div>

            {/* Planners Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {[
                { title: 'Home Interior Planner', icon: Home, color: 'blue', desc: 'Furnish living rooms, bedrooms, or home offices. Automatically balances budget between seating, lighting, rugs, and wall decor.', vendors: ['IKEA', 'Amazon', 'Flipkart'], action: () => setView('home_planner') },
                { title: 'Party & Event Planner', icon: PartyPopper, color: 'violet', desc: 'Plan birthdays, weddings, or college fests. Intelligently divides budget across 4 pillars: Food, Venue, Decor, and Audio.', vendors: ['Zomato', 'Swiggy', 'OYO'], action: () => setView('party_planner') },
                { title: 'Jewelry & Outfit Matcher', icon: Sparkles, color: 'emerald', desc: 'Upload an outfit image or specify colors to discover coordinated jewelry (earrings, necklaces, bangles) matched to neckline and event.', vendors: ['CaratLane', 'Myntra', 'Amazon'], action: () => setView('jewelry_planner') },
              ].map((p, idx) => (
                <div key={idx} className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm flex flex-col justify-between hover:shadow-md transition">
                  <div>
                    <div className="w-12 h-12 rounded-xl bg-indigo-50 text-indigo-700 flex items-center justify-center mb-4"><p.icon className="w-6 h-6" /></div>
                    <h3 className="text-xl font-bold text-slate-900 mb-2">{p.title}</h3>
                    <p className="text-sm text-slate-600 mb-4">{p.desc}</p>
                    <div className="flex flex-wrap gap-1.5 mb-6 text-[11px] font-semibold">
                      {p.vendors.map((v, i) => <span key={i} className="bg-slate-100 text-slate-700 border border-slate-200 px-2 py-0.5 rounded">{v}</span>)}
                    </div>
                  </div>
                  <button onClick={p.action} className="w-full bg-slate-900 hover:bg-indigo-600 text-white text-sm font-semibold py-2.5 rounded-xl transition flex items-center justify-center gap-1.5">
                    <span>Launch Planner</span><ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 2. HOME PLANNER FORM */}
        {view === 'home_planner' && (
          <div className="max-w-2xl mx-auto py-4">
            <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-sm">
              <h2 className="text-xl font-bold text-slate-900 mb-1 flex items-center gap-2"><Home className="w-5 h-5 text-indigo-600" />Home Interior Planner</h2>
              <p className="text-xs text-slate-500 mb-6">Curate room furnishings within exact budget limits.</p>
              <form onSubmit={(e) => handlePlanSubmit(e, '/generate-home', { budget: home.budget, room_type: home.room, num_rooms: home.num, style_preference: home.style, required_items: home.items, color_theme: home.color, additional_requirements: home.notes }, 'home_results')} className="space-y-4">
                <div>
                  <div className="flex justify-between items-center mb-1"><label className="text-sm font-semibold text-slate-700">Total Budget (₹ INR)</label><span className="text-sm font-bold text-indigo-600">{fmtINR(home.budget)}</span></div>
                  <input type="number" min="5000" step="1000" value={home.budget} onChange={(e) => setHome({ ...home, budget: Number(e.target.value) })} className="w-full px-3.5 py-2.5 rounded-lg border border-slate-300 text-sm font-medium" required />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-semibold text-slate-700 block mb-1">Room Type</label>
                    <select value={home.room} onChange={(e) => setHome({ ...home, room: e.target.value })} className="w-full px-3.5 py-2.5 rounded-lg border border-slate-300 text-sm">
                      <option>Living Room</option><option>Bedroom</option><option>Kitchen</option><option>Dining Room</option><option>Home Office</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-sm font-semibold text-slate-700 block mb-1">Rooms Count</label>
                    <input type="number" min="1" max="10" value={home.num} onChange={(e) => setHome({ ...home, num: Number(e.target.value) })} className="w-full px-3.5 py-2.5 rounded-lg border border-slate-300 text-sm" />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-semibold text-slate-700 block mb-1">Style</label>
                    <select value={home.style} onChange={(e) => setHome({ ...home, style: e.target.value })} className="w-full px-3.5 py-2.5 rounded-lg border border-slate-300 text-sm">
                      <option>Modern Minimalist</option><option>Scandinavian</option><option>Bohemian Warmth</option><option>Industrial Contemporary</option><option>Indian Traditional</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-sm font-semibold text-slate-700 block mb-1">Color Palette</label>
                    <input type="text" value={home.color} onChange={(e) => setHome({ ...home, color: e.target.value })} className="w-full px-3.5 py-2.5 rounded-lg border border-slate-300 text-sm" required />
                  </div>
                </div>
                <div>
                  <label className="text-sm font-semibold text-slate-700 block mb-1">Required Items</label>
                  <input type="text" value={home.items} onChange={(e) => setHome({ ...home, items: e.target.value })} className="w-full px-3.5 py-2.5 rounded-lg border border-slate-300 text-sm" required />
                </div>
                <button type="submit" disabled={loading} className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-3 rounded-xl shadow-md transition">
                  {loading ? 'Optimizing with Gemini...' : '✨ Generate Smart Interior Blueprint'}
                </button>
              </form>
            </div>
          </div>
        )}
        {view === 'home_results' && renderPlanResults('home_planner', 'Home Interior Blueprint')}

        {/* 3. PARTY PLANNER FORM */}
        {view === 'party_planner' && (
          <div className="max-w-2xl mx-auto py-4">
            <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-sm">
              <h2 className="text-xl font-bold text-slate-900 mb-1 flex items-center gap-2"><PartyPopper className="w-5 h-5 text-violet-600" />Party & Event Planner</h2>
              <p className="text-xs text-slate-500 mb-6">Coordinate catering, venue, decorations, and DJ audio.</p>
              <form onSubmit={(e) => handlePlanSubmit(e, '/generate-party', { budget: party.budget, event_type: party.event, num_guests: party.guests, venue_preference: party.venue, food_preference: party.food, decoration_preference: party.decor, entertainment_preference: party.audio, location: party.city, additional_requirements: party.notes }, 'party_results')} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-semibold text-slate-700 block mb-1">Total Budget (₹ INR)</label>
                    <input type="number" min="5000" step="1000" value={party.budget} onChange={(e) => setParty({ ...party, budget: Number(e.target.value) })} className="w-full px-3.5 py-2.5 rounded-lg border border-slate-300 text-sm font-medium" required />
                  </div>
                  <div>
                    <label className="text-sm font-semibold text-slate-700 block mb-1">Guest Count</label>
                    <input type="number" min="1" max="1000" value={party.guests} onChange={(e) => setParty({ ...party, guests: Number(e.target.value) })} className="w-full px-3.5 py-2.5 rounded-lg border border-slate-300 text-sm" required />
                  </div>
                </div>
                <div className="text-xs font-semibold text-indigo-700 bg-indigo-50 p-2.5 rounded-lg">Catering est: ~{fmtINR(Math.round((party.budget * 0.45) / Math.max(1, party.guests)))} / guest (45% allocation)</div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-semibold text-slate-700 block mb-1">Event Type</label>
                    <select value={party.event} onChange={(e) => setParty({ ...party, event: e.target.value })} className="w-full px-3.5 py-2.5 rounded-lg border border-slate-300 text-sm">
                      <option>Birthday</option><option>Wedding Reception</option><option>Corporate Mixer</option><option>Anniversary</option><option>College Fest</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-sm font-semibold text-slate-700 block mb-1">Venue</label>
                    <select value={party.venue} onChange={(e) => setParty({ ...party, venue: e.target.value })} className="w-full px-3.5 py-2.5 rounded-lg border border-slate-300 text-sm">
                      <option>Indoor Banquet Hall</option><option>Outdoor Lawn / Garden</option><option>Rooftop Lounge</option><option>Private Villa</option>
                    </select>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-semibold text-slate-700 block mb-1">Food Preference</label>
                    <select value={party.food} onChange={(e) => setParty({ ...party, food: e.target.value })} className="w-full px-3.5 py-2.5 rounded-lg border border-slate-300 text-sm">
                      <option>Multi-Cuisine Buffet</option><option>Pure Veg Deluxe</option><option>Non-Veg BBQ & Starters</option><option>Finger Foods & Mocktails</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-sm font-semibold text-slate-700 block mb-1">Decoration Style</label>
                    <select value={party.decor} onChange={(e) => setParty({ ...party, decor: e.target.value })} className="w-full px-3.5 py-2.5 rounded-lg border border-slate-300 text-sm">
                      <option>Themed & Balloon Arch</option><option>Floral Minimalist</option><option>Fairy Lights & Neon</option><option>Luxury Royal</option>
                    </select>
                  </div>
                </div>
                <button type="submit" disabled={loading} className="w-full bg-violet-600 hover:bg-violet-700 text-white font-semibold py-3 rounded-xl shadow-md transition">
                  {loading ? 'Coordinating with Gemini...' : '🎉 Generate Event Masterplan'}
                </button>
              </form>
            </div>
          </div>
        )}
        {view === 'party_results' && renderPlanResults('party_planner', 'Party & Event Masterplan')}

        {/* 4. JEWELRY PLANNER FORM */}
        {view === 'jewelry_planner' && (
          <div className="max-w-2xl mx-auto py-4">
            <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-sm">
              <h2 className="text-xl font-bold text-slate-900 mb-1 flex items-center gap-2"><Sparkles className="w-5 h-5 text-emerald-600" />Jewelry & Outfit Matcher</h2>
              <p className="text-xs text-slate-500 mb-6">Gemini Vision outfit photo analysis & matching accessories.</p>
              <form onSubmit={(e) => handlePlanSubmit(e, '/generate-jewelry', { budget: jewelry.budget, occasion: jewelry.occasion, jewelry_type: jewelry.type, style_preference: jewelry.style, metal_preference: jewelry.metal, outfit_color: jewelry.color, outfit_description: jewelry.desc, additional_requirements: jewelry.notes, image_data: jewelry.imgB64 }, 'jewelry_results')} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-semibold text-slate-700 block mb-1">Budget (₹ INR)</label>
                    <input type="number" min="2000" step="1000" value={jewelry.budget} onChange={(e) => setJewelry({ ...jewelry, budget: Number(e.target.value) })} className="w-full px-3.5 py-2.5 rounded-lg border border-slate-300 text-sm font-medium" required />
                  </div>
                  <div>
                    <label className="text-sm font-semibold text-slate-700 block mb-1">Occasion</label>
                    <select value={jewelry.occasion} onChange={(e) => setJewelry({ ...jewelry, occasion: e.target.value })} className="w-full px-3.5 py-2.5 rounded-lg border border-slate-300 text-sm">
                      <option>Wedding</option><option>Engagement</option><option>Birthday Party</option><option>Traditional Festival</option><option>Office Formal</option>
                    </select>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-semibold text-slate-700 block mb-1">Jewelry Type</label>
                    <select value={jewelry.type} onChange={(e) => setJewelry({ ...jewelry, type: e.target.value })} className="w-full px-3.5 py-2.5 rounded-lg border border-slate-300 text-sm">
                      <option>Complete Set</option><option>Necklace & Choker</option><option>Earrings & Jhumkas</option><option>Bangles & Bracelets</option><option>Statement Ring</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-sm font-semibold text-slate-700 block mb-1">Metal Preference</label>
                    <select value={jewelry.metal} onChange={(e) => setJewelry({ ...jewelry, metal: e.target.value })} className="w-full px-3.5 py-2.5 rounded-lg border border-slate-300 text-sm">
                      <option>Gold</option><option>Rose Gold</option><option>Diamond & Solitaire</option><option>925 Sterling Silver</option><option>Oxidized Antique</option>
                    </select>
                  </div>
                </div>
                <div>
                  <label className="text-sm font-semibold text-slate-700 block mb-1">Outfit Color & Neckline Details</label>
                  <input type="text" value={jewelry.color} onChange={(e) => setJewelry({ ...jewelry, color: e.target.value })} className="w-full px-3.5 py-2.5 rounded-lg border border-slate-300 text-sm mb-2" required placeholder="Color: e.g. Emerald Green & Gold" />
                  <input type="text" value={jewelry.desc} onChange={(e) => setJewelry({ ...jewelry, desc: e.target.value })} className="w-full px-3.5 py-2.5 rounded-lg border border-slate-300 text-sm" placeholder="Neckline / cut description" />
                </div>

                {/* Image Upload Dropzone */}
                <div>
                  <label className="text-sm font-semibold text-slate-700 block mb-1">Optional: Outfit Photo (Gemini Vision)</label>
                  <div className="border-2 border-dashed border-slate-300 hover:border-emerald-500 rounded-xl p-4 text-center cursor-pointer relative bg-slate-50">
                    <input type="file" accept="image/jpeg,image/png,image/webp" onChange={onImgUpload} className="absolute inset-0 opacity-0 cursor-pointer w-full h-full" />
                    <Upload className="w-6 h-6 text-emerald-600 mx-auto mb-1" />
                    <p className="text-xs font-semibold text-slate-700">{jewelry.imgName || 'Click or drag outfit photo (JPG, PNG under 5MB)'}</p>
                  </div>
                </div>

                <button type="submit" disabled={loading} className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-semibold py-3 rounded-xl shadow-md transition">
                  {loading ? 'Analyzing with Gemini Vision...' : '💎 Curate Matching Jewelry'}
                </button>
              </form>
            </div>
          </div>
        )}
        {view === 'jewelry_results' && renderPlanResults('jewelry_planner', 'Jewelry & Outfit Curation')}

        {/* 5. DASHBOARD */}
        {view === 'dashboard' && currentUser && (
          <div className="space-y-6 py-2">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div><h1 className="text-2xl font-black text-slate-900">Welcome, {currentUser.name}!</h1><p className="text-xs text-slate-500 mt-0.5">Manage your plans and budget tracking.</p></div>
              <button onClick={() => setView('history')} className="text-xs font-bold px-3 py-2 bg-indigo-600 text-white rounded-lg">View History ({historyList.length})</button>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs"><div className="text-xs text-slate-400 font-bold uppercase">Total Plans</div><div className="text-2xl font-black text-indigo-600 mt-1">{historyList.length}</div></div>
              <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs"><div className="text-xs text-slate-400 font-bold uppercase">Budget Managed</div><div className="text-2xl font-black text-emerald-600 mt-1">{fmtINR(historyList.reduce((acc, h) => acc + (h.budget || 0), 0))}</div></div>
              <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs"><div className="text-xs text-slate-400 font-bold uppercase">Email</div><div className="text-sm font-bold text-slate-800 mt-2 truncate">{currentUser.email}</div></div>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <button onClick={() => setView('home_planner')} className="bg-white hover:bg-indigo-50 border border-slate-200 p-4 rounded-xl text-left shadow-xs transition"><Home className="w-5 h-5 text-blue-600 mb-1" /><div className="font-bold text-slate-900 text-sm">Home Interior</div><div className="text-[11px] text-slate-500">Furnishings & decor</div></button>
              <button onClick={() => setView('party_planner')} className="bg-white hover:bg-violet-50 border border-slate-200 p-4 rounded-xl text-left shadow-xs transition"><PartyPopper className="w-5 h-5 text-violet-600 mb-1" /><div className="font-bold text-slate-900 text-sm">Party Planner</div><div className="text-[11px] text-slate-500">Events & catering</div></button>
              <button onClick={() => setView('jewelry_planner')} className="bg-white hover:bg-emerald-50 border border-slate-200 p-4 rounded-xl text-left shadow-xs transition"><Sparkles className="w-5 h-5 text-emerald-600 mb-1" /><div className="font-bold text-slate-900 text-sm">Jewelry Matcher</div><div className="text-[11px] text-slate-500">Outfit styling</div></button>
            </div>
          </div>
        )}

        {/* 6. HISTORY */}
        {view === 'history' && (
          <div className="space-y-4 py-2">
            <h1 className="text-2xl font-bold text-slate-900">Saved History in SQLite ({historyList.length})</h1>
            {historyList.length > 0 ? (
              historyList.map((item) => (
                <div key={item.id} className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-[11px] font-bold uppercase bg-slate-100 px-2 py-0.5 rounded">{item.planner_type}</span>
                    <span className="text-sm font-black text-indigo-600">{fmtINR(item.budget)}</span>
                  </div>
                  <h4 className="font-bold text-slate-900 text-sm mb-1">{item.response_data?.title}</h4>
                  <p className="text-xs text-slate-500 mb-3">{item.response_data?.summary}</p>
                  <button onClick={() => { setCurrentPlan(item.response_data); setView(item.planner_type === 'home' ? 'home_results' : item.planner_type === 'party' ? 'party_results' : 'jewelry_results'); }} className="text-xs font-bold text-indigo-600 hover:underline">Inspect Plan &rarr;</button>
                </div>
              ))
            ) : (
              <div className="bg-white border border-slate-200 rounded-xl p-8 text-center"><p className="text-slate-500 text-sm">No plans saved yet. Generate one above!</p></div>
            )}
          </div>
        )}

        {/* 7. TESTIMONIALS */}
        {view === 'testimonials' && (
          <div className="max-w-4xl mx-auto py-6 space-y-6">
            <div className="text-center"><h2 className="text-3xl font-black text-slate-900">Project Evaluation & Testimonials</h2><p className="text-xs text-slate-500 mt-1">Validated on real budget test cases.</p></div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {[
                { name: 'Rohan Kulkarni', role: 'College Fest Coordinator', text: 'Simulated our college farewell with ₹75,000 for 50 attendees. PocketSmart accurately apportioned 45% for catering with Zomato links.' },
                { name: 'Priya Sundaram', role: 'Design Student', text: 'The jewelry outfit image analysis is a standout feature. It suggested gold jhumkas matching my lehenga while keeping me under ₹30,000.' },
                { name: 'Ankit Verma', role: 'Apartment Tenant', text: 'Furnishing a 1BHK with ₹50,000 used to take days of spreadsheets. PocketSmart split it across sofa, nesting tables, and rug from IKEA.' },
              ].map((t, idx) => (
                <div key={idx} className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs flex flex-col justify-between">
                  <p className="text-xs text-slate-600 italic mb-4">"{t.text}"</p>
                  <div><div className="font-bold text-sm text-slate-900">{t.name}</div><div className="text-[11px] text-slate-400">{t.role}</div></div>
                </div>
              ))}
            </div>
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
              <h3 className="font-bold text-sm text-slate-900 mb-2 flex items-center gap-2"><ShieldCheck className="w-4 h-4 text-emerald-600" />College Project Demonstration Ready</h3>
              <p className="text-xs text-slate-600">FastAPI backend, SQLAlchemy models, Google Gemini GenAI, SQLite persistence, and multi-vendor abstraction (Amazon, IKEA, Zomato, OYO, CaratLane).</p>
            </div>
          </div>
        )}

        {/* 8. AUTH (LOGIN / REGISTER) */}
        {(view === 'login' || view === 'register') && (
          <div className="max-w-md mx-auto py-8">
            <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-sm">
              <h2 className="text-2xl font-bold text-slate-900 mb-1">{view === 'login' ? 'Sign In' : 'Create Account'}</h2>
              <p className="text-xs text-slate-500 mb-6">{view === 'login' ? 'Access your dashboard and saved plans' : 'Save your budget recommendations to SQLite'}</p>
              <form onSubmit={(e) => handleAuth(e, view === 'register')} className="space-y-4">
                {view === 'register' && (
                  <div><label className="text-xs font-semibold text-slate-700 block mb-1">Full Name</label><input type="text" value={auth.name} onChange={(e) => setAuth({ ...auth, name: e.target.value })} className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm" required /></div>
                )}
                <div><label className="text-xs font-semibold text-slate-700 block mb-1">Email</label><input type="email" value={auth.email} onChange={(e) => setAuth({ ...auth, email: e.target.value })} className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm" required /></div>
                <div><label className="text-xs font-semibold text-slate-700 block mb-1">Password</label><input type="password" value={auth.password} onChange={(e) => setAuth({ ...auth, password: e.target.value })} className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm" required minLength={6} /></div>
                {view === 'register' && (
                  <div><label className="text-xs font-semibold text-slate-700 block mb-1">Confirm Password</label><input type="password" value={auth.confirm} onChange={(e) => setAuth({ ...auth, confirm: e.target.value })} className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm" required minLength={6} /></div>
                )}
                <button type="submit" disabled={loading} className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-2.5 rounded-xl text-sm transition">
                  {loading ? 'Processing...' : view === 'login' ? 'Sign In' : 'Register'}
                </button>
              </form>
              <div className="text-center mt-4 text-xs text-slate-500">
                {view === 'login' ? <>Don't have an account? <button onClick={() => setView('register')} className="text-indigo-600 font-bold hover:underline">Register</button></> : <>Already have an account? <button onClick={() => setView('login')} className="text-indigo-600 font-bold hover:underline">Sign In</button></>}
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 py-4 text-center text-xs text-slate-500 mt-auto">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <div className="font-bold text-slate-800">PocketSmart AI • v1.0.0</div>
          <div>FastAPI • SQLite • Google Gemini • Multi-Vendor Links</div>
          <a href="/api/export-project-zip" download="PocketSmart-AI.zip" className="text-indigo-600 font-bold hover:underline flex items-center gap-1">
            <Download className="w-3.5 h-3.5" /><span>Download Python ZIP</span>
          </a>
        </div>
      </footer>
    </div>
  );
}
