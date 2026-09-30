import express, { Request, Response } from 'express';
import { createServer as createViteServer } from 'vite';
import path from 'path';
import fs from 'fs';
import dotenv from 'dotenv';
import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';
import { GoogleGenAI } from '@google/genai';
import JSZip from 'jszip';

dotenv.config();

const app = express();
const PORT = Number(process.env.PORT) || 3000;
const SECRET_KEY = process.env.SECRET_KEY || 'pocketsmart_secret_key_change_in_production';
const MODEL = process.env.GEMINI_MODEL || 'gemini-3.8-flash';

const ai = new GoogleGenAI({
  apiKey: process.env.GEMINI_API_KEY || '',
  httpOptions: { headers: { 'User-Agent': 'aistudio-build' } },
});

app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

const dataDir = path.resolve(process.cwd(), 'data');
if (!fs.existsSync(dataDir)) fs.mkdirSync(dataDir, { recursive: true });
const dbFile = path.resolve(dataDir, 'pocketsmart_store.json');

const loadStore = () => {
  try {
    return fs.existsSync(dbFile) ? JSON.parse(fs.readFileSync(dbFile, 'utf-8')) : { users: [], recommendations: [] };
  } catch {
    return { users: [], recommendations: [] };
  }
};

const saveStore = (data: any) => {
  try { fs.writeFileSync(dbFile, JSON.stringify(data, null, 2)); } catch (e) { console.error(e); }
};

const getUser = (req: Request) => {
  const auth = req.headers.authorization;
  let token = auth?.startsWith('Bearer ') ? auth.split(' ')[1] : '';
  if (!token && req.headers.cookie) {
    token = req.headers.cookie.split(';').find((c) => c.trim().startsWith('access_token='))?.split('=')[1]?.replace('Bearer ', '') || '';
  }
  if (!token) return null;
  try {
    const decoded = jwt.verify(token, SECRET_KEY) as any;
    return loadStore().users.find((u: any) => u.id === decoded.user_id) || null;
  } catch { return null; }
};

const platformUrls: Record<string, (q: string) => string> = {
  Amazon: (q) => `https://www.amazon.in/s?k=${encodeURIComponent(q)}`,
  Flipkart: (q) => `https://www.flipkart.com/search?q=${encodeURIComponent(q)}`,
  IKEA: (q) => `https://www.ikea.com/in/en/search/?q=${encodeURIComponent(q)}`,
  Swiggy: (q) => `https://www.swiggy.com/search?query=${encodeURIComponent(q)}`,
  Zomato: (q) => `https://www.zomato.com/search?q=${encodeURIComponent(q)}`,
  OYO: (q) => `https://www.oyorooms.com/search?location=${encodeURIComponent(q)}`,
  CaratLane: (q) => `https://www.caratlane.com/search?q=${encodeURIComponent(q)}`,
  Myntra: (q) => `https://www.myntra.com/${encodeURIComponent(q).replace(/%20/g, '-')}`,
};

const getSearchUrl = (plat: string, q: string) => (platformUrls[plat] || platformUrls.Amazon)(q);

const cleanJson = (str: string) => str.replace(/^```(json)?\s*/i, '').replace(/```\s*$/, '').trim();

// ==========================================
// AUTH ROUTES
// ==========================================
app.post('/register', async (req: Request, res: Response) => {
  try {
    const { name, email, password, confirm_password } = req.body;
    if (!name || !email || !password) return res.status(400).json({ error: 'All fields are required.' });
    if (password.length < 6) return res.status(400).json({ error: 'Password must be at least 6 characters.' });
    if (confirm_password && password !== confirm_password) return res.status(400).json({ error: 'Passwords do not match.' });

    const store = loadStore();
    const cleanEmail = email.trim().toLowerCase();
    if (store.users.some((u: any) => u.email === cleanEmail)) return res.status(400).json({ error: 'Email already registered.' });

    const user = { id: Date.now(), name: name.trim(), email: cleanEmail, password_hash: await bcrypt.hash(password, 10), created_at: new Date().toISOString() };
    store.users.push(user);
    saveStore(store);

    const token = jwt.sign({ user_id: user.id, email: user.email }, SECRET_KEY, { expiresIn: '24h' });
    res.json({ status: 'success', access_token: token, user: { id: user.id, name: user.name, email: user.email } });
  } catch (err: any) { res.status(500).json({ error: err.message }); }
});

app.post('/login', async (req: Request, res: Response) => {
  try {
    const { email, password } = req.body;
    const user = loadStore().users.find((u: any) => u.email === (email || '').trim().toLowerCase());
    if (!user || !(await bcrypt.compare(password, user.password_hash))) {
      return res.status(401).json({ error: 'Invalid email or password.' });
    }
    const token = jwt.sign({ user_id: user.id, email: user.email }, SECRET_KEY, { expiresIn: '24h' });
    res.json({ status: 'success', access_token: token, token_type: 'bearer', user: { id: user.id, name: user.name, email: user.email } });
  } catch (err: any) { res.status(500).json({ error: err.message }); }
});

app.post('/token', async (req: Request, res: Response) => {
  const { username, email, password } = req.body;
  const user = loadStore().users.find((u: any) => u.email === (username || email || '').trim().toLowerCase());
  if (!user || !(await bcrypt.compare(password, user.password_hash))) return res.status(401).json({ detail: 'Invalid credentials' });
  const access_token = jwt.sign({ user_id: user.id, email: user.email }, SECRET_KEY, { expiresIn: '24h' });
  res.json({ access_token, token_type: 'bearer', user: { id: user.id, name: user.name, email: user.email } });
});

app.get('/logout', (_req, res) => res.json({ status: 'success' }));
app.get('/session-info', (req, res) => {
  const u = getUser(req);
  res.json({ authenticated: Boolean(u), user: u ? { id: u.id, name: u.name, email: u.email } : null });
});
app.get('/session-data', (req, res) => {
  const u = getUser(req);
  res.json({ logged_in: Boolean(u), user_id: u?.id || null, user_name: u?.name || 'Guest' });
});
app.get('/startup', (_req, res) => res.json({ status: 'online', app: 'PocketSmart AI', version: '1.0.0', model: MODEL, has_key: Boolean(process.env.GEMINI_API_KEY) }));

// ==========================================
// RECOMMENDATION ENGINE (GEMINI & FALLBACK)
// ==========================================
async function callGeminiJson(prompt: string, parts?: any[]): Promise<any> {
  if (!process.env.GEMINI_API_KEY) return null;
  try {
    const contents: any = parts ? [...parts, { text: prompt }] : prompt;
    const response = await ai.models.generateContent({ model: MODEL, contents });
    return JSON.parse(cleanJson(response.text || '{}'));
  } catch (err) {
    console.error('Gemini error:', err);
    return null;
  }
}

function saveRecommendation(user: any, planner_type: string, budget: number, reqBody: any, result: any) {
  const store = loadStore();
  const rec = { id: Date.now(), user_id: user?.id || null, planner_type, budget, created_at: new Date().toISOString(), request_data: reqBody, response_data: result };
  store.recommendations.push(rec);
  saveStore(store);
  result.recommendation_id = rec.id;
  return result;
}

// 1. HOME PLANNER
app.post('/generate-home', async (req: Request, res: Response) => {
  try {
    const user = getUser(req);
    const { budget = 50000, room_type = 'Living Room', style_preference = 'Modern', color_theme = 'Warm Neutrals', required_items = 'Sofa, Table, Lamp' } = req.body;
    const b = Math.max(1000, Number(budget) || 50000);

    const prompt = `Act as interior designer for PocketSmart AI. Budget: ₹${b} INR. Room: ${room_type}. Style: ${style_preference}. Color: ${color_theme}. Items: ${required_items}.
Return strict JSON with total price <= ${b}:
{
  "title": "${room_type} Interior Plan",
  "summary": "Design summary",
  "allocations": [{"category": "Core Furniture", "allocated_amount": ${Math.round(b*0.55)}, "percentage": 55}, {"category": "Lighting & Electricals", "allocated_amount": ${Math.round(b*0.2)}, "percentage": 20}, {"category": "Wall & Soft Furnishings", "allocated_amount": ${Math.round(b*0.25)}, "percentage": 25}],
  "items": [{"name": "Product Name", "category": "Core Furniture", "estimated_price": ${Math.round(b*0.35)}, "quantity": 1, "reason": "Why chosen", "platform": "IKEA", "specs": "Specs"}]
}`;

    let data = await callGeminiJson(prompt);
    if (!data?.items?.length) {
      data = {
        title: `${room_type} Interior Plan`,
        summary: `Customized ${style_preference} blueprint optimized for ₹${b.toLocaleString('en-IN')}.`,
        allocations: [
          { category: 'Core Furniture', allocated_amount: Math.round(b * 0.55), percentage: 55 },
          { category: 'Lighting & Electricals', allocated_amount: Math.round(b * 0.2), percentage: 20 },
          { category: 'Wall & Soft Furnishings', allocated_amount: Math.round(b * 0.25), percentage: 25 },
        ],
        items: [
          { name: `${style_preference} 3-Seater Sofa`, category: 'Core Furniture', estimated_price: Math.round(b * 0.4), quantity: 1, reason: `Seating in ${color_theme} tone.`, platform: 'IKEA' },
          { name: 'Dual Nesting Coffee Table', category: 'Core Furniture', estimated_price: Math.round(b * 0.15), quantity: 1, reason: 'Compact dual tiers.', platform: 'Amazon' },
          { name: 'Arc Floor Lamp & Dimmer', category: 'Lighting & Electricals', estimated_price: Math.round(b * 0.12), quantity: 1, reason: 'Warm ambient glow.', platform: 'Amazon' },
          { name: 'Geometric Washable Area Rug', category: 'Wall & Soft Furnishings', estimated_price: Math.round(b * 0.12), quantity: 1, reason: `Matches ${color_theme}.`, platform: 'Flipkart' },
          { name: 'Canvas Wall Art Triptych', category: 'Wall & Soft Furnishings', estimated_price: Math.round(b * 0.09), quantity: 1, reason: 'Focal wall accent.', platform: 'Flipkart' },
        ],
      };
    }

    let spent = 0;
    const items = data.items.map((it: any) => {
      const p = Number(it.estimated_price) || 0;
      spent += p * (it.quantity || 1);
      const plat = it.platform || 'Amazon';
      return { ...it, estimated_price: p, platform: plat, purchase_link: getSearchUrl(plat, `${it.name} ${room_type}`), badge: plat === 'IKEA' ? 'Home & Furniture' : 'E-Commerce' };
    });

    const result = {
      planner_type: 'home',
      title: data.title || `${room_type} Plan`,
      summary: data.summary,
      allocations: data.allocations,
      items,
      budget_summary: { total_budget: b, estimated_total: spent, remaining_budget: Math.max(0, b - spent), is_within_budget: spent <= b },
      created_at: new Date().toISOString(),
    };

    res.json(saveRecommendation(user, 'home', b, req.body, result));
  } catch (err: any) { res.status(500).json({ error: err.message }); }
});

// 2. PARTY PLANNER
app.post('/generate-party', async (req: Request, res: Response) => {
  try {
    const user = getUser(req);
    const { budget = 75000, event_type = 'Birthday', num_guests = 50, location = 'City Center', food_preference = 'Buffet', decoration_preference = 'Balloons' } = req.body;
    const b = Math.max(1000, Number(budget) || 75000);
    const g = Math.max(1, Number(num_guests) || 1);

    const prompt = `Act as event coordinator for PocketSmart AI. Budget: ₹${b} INR. Event: ${event_type}. Guests: ${g}. City: ${location}. Food: ${food_preference}. Decor: ${decoration_preference}.
Return strict JSON with total price <= ${b}:
{
  "title": "${event_type} Celebration Plan",
  "summary": "Summary",
  "allocations": [{"category": "Food/Catering", "allocated_amount": ${Math.round(b*0.45)}, "percentage": 45}, {"category": "Venue", "allocated_amount": ${Math.round(b*0.25)}, "percentage": 25}, {"category": "Decoration", "allocated_amount": ${Math.round(b*0.18)}, "percentage": 18}, {"category": "Entertainment", "allocated_amount": ${Math.round(b*0.12)}, "percentage": 12}],
  "items": [{"name": "Buffet Catering", "category": "Food/Catering", "estimated_price": ${Math.round(b*0.42)}, "quantity": 1, "reason": "Why chosen", "platform": "Zomato", "specs": "₹${Math.round((b*0.45)/g)}/plate"}]
}`;

    let data = await callGeminiJson(prompt);
    if (!data?.items?.length) {
      const perHead = Math.round((b * 0.45) / g);
      data = {
        title: `${event_type} Event Masterplan`,
        summary: `Plan for ${g} attendees at ₹${b.toLocaleString('en-IN')} with catering at ~₹${perHead}/plate.`,
        allocations: [
          { category: 'Food/Catering', allocated_amount: Math.round(b * 0.45), percentage: 45 },
          { category: 'Venue', allocated_amount: Math.round(b * 0.25), percentage: 25 },
          { category: 'Decoration', allocated_amount: Math.round(b * 0.18), percentage: 18 },
          { category: 'Entertainment', allocated_amount: Math.round(b * 0.12), percentage: 12 },
        ],
        items: [
          { name: `${food_preference} Catering Buffet`, category: 'Food/Catering', estimated_price: Math.round(b * 0.43), quantity: 1, reason: `Buffet for ${g} guests (~₹${perHead}/person).`, platform: 'Zomato', specs: `Serves ${g} pax` },
          { name: 'Banquet Hall Reservation', category: 'Venue', estimated_price: Math.round(b * 0.24), quantity: 1, reason: `Accommodates ${g} guests in ${location}.`, platform: 'OYO', specs: `Townhouse/hall in ${location}` },
          { name: `${decoration_preference} Stage Backdrop`, category: 'Decoration', estimated_price: Math.round(b * 0.16), quantity: 1, reason: `Photo arch for ${event_type}.`, platform: 'Amazon', specs: 'Arch & balloon kit' },
          { name: 'Party Speaker & Wireless Mic', category: 'Entertainment', estimated_price: Math.round(b * 0.11), quantity: 1, reason: 'Music & announcements setup.', platform: 'Amazon', specs: 'Bluetooth PA sound' },
        ],
      };
    }

    let spent = 0;
    const items = data.items.map((it: any) => {
      const p = Number(it.estimated_price) || 0;
      spent += p * (it.quantity || 1);
      const plat = it.platform || 'Zomato';
      return { ...it, estimated_price: p, platform: plat, purchase_link: getSearchUrl(plat, `${it.name} ${event_type}`), badge: plat === 'Zomato' ? 'Food & Catering' : plat === 'OYO' ? 'Venues & Stay' : 'E-Commerce' };
    });

    const result = {
      planner_type: 'party',
      title: data.title || `${event_type} Plan`,
      summary: data.summary,
      allocations: data.allocations,
      items,
      budget_summary: { total_budget: b, estimated_total: spent, remaining_budget: Math.max(0, b - spent), is_within_budget: spent <= b },
      created_at: new Date().toISOString(),
    };

    res.json(saveRecommendation(user, 'party', b, req.body, result));
  } catch (err: any) { res.status(500).json({ error: err.message }); }
});

// 3. JEWELRY PLANNER & OUTFIT VISION
app.post('/generate-jewelry', async (req: Request, res: Response) => {
  try {
    const user = getUser(req);
    const { budget = 30000, occasion = 'Wedding', jewelry_type = 'Complete Set', style_preference = 'Royal Kundan', metal_preference = 'Gold', outfit_color = 'Emerald Green', outfit_description = '', image_data } = req.body;
    const b = Math.max(1000, Number(budget) || 30000);

    const parts: any[] = [];
    if (image_data && typeof image_data === 'string') {
      const [hdr, data] = image_data.includes(',') ? image_data.split(',') : ['', image_data];
      parts.push({ inlineData: { data, mimeType: hdr.includes('png') ? 'image/png' : hdr.includes('webp') ? 'image/webp' : 'image/jpeg' } });
    }

    const prompt = `Act as jewelry stylist for PocketSmart AI. Budget: ₹${b} INR. Occasion: ${occasion}. Type: ${jewelry_type}. Style: ${style_preference}. Metal: ${metal_preference}. Outfit: ${outfit_color}. Description: ${outfit_description}.
If image provided, analyze fabric tone, cut, and neckline.
Return strict JSON with total price <= ${b}:
{
  "title": "${jewelry_type} Curation for ${occasion}",
  "summary": "Styling summary",
  "ai_analysis": "Outfit styling analysis notes",
  "allocations": [{"category": "Focal Piece", "allocated_amount": ${Math.round(b*0.55)}, "percentage": 55}, {"category": "Earrings", "allocated_amount": ${Math.round(b*0.25)}, "percentage": 25}, {"category": "Wrist & Ring", "allocated_amount": ${Math.round(b*0.2)}, "percentage": 20}],
  "items": [{"name": "Jewelry Piece", "category": "Focal Piece", "estimated_price": ${Math.round(b*0.5)}, "quantity": 1, "reason": "Why it matches", "platform": "CaratLane", "specs": "${metal_preference}"}]
}`;

    let data = await callGeminiJson(prompt, parts.length ? parts : undefined);
    if (!data?.items?.length) {
      data = {
        title: `${jewelry_type} Ensemble for ${occasion}`,
        summary: `Coordinated ${metal_preference} collection suited for ${occasion} and ${outfit_color} attire.`,
        ai_analysis: image_data
          ? `Vision Analysis: Identified ${outfit_color} fabric tones. The ${metal_preference} finish and ${style_preference} motifs provide balanced contrast for ${occasion}.`
          : `Styling Insights: For ${outfit_color} attire, ${metal_preference} brings warmth and elegance suitable for ${occasion}.`,
        allocations: [
          { category: 'Focal Piece', allocated_amount: Math.round(b * 0.55), percentage: 55 },
          { category: 'Earrings', allocated_amount: Math.round(b * 0.25), percentage: 25 },
          { category: 'Wrist & Ring', allocated_amount: Math.round(b * 0.2), percentage: 20 },
        ],
        items: [
          { name: `${metal_preference} ${style_preference} Statement Piece`, category: 'Focal Piece', estimated_price: Math.round(b * 0.52), quantity: 1, reason: `Centerpiece design tailored for ${occasion}.`, platform: 'CaratLane', specs: `${metal_preference} finish` },
          { name: `Coordinated ${metal_preference} Drop Earrings`, category: 'Earrings', estimated_price: Math.round(b * 0.24), quantity: 1, reason: 'Complements neckline without overpowering face.', platform: 'Myntra', specs: 'Hypoallergenic posts' },
          { name: `Minimalist ${metal_preference} Cuff & Stacking Rings`, category: 'Wrist & Ring', estimated_price: Math.round(b * 0.18), quantity: 1, reason: `Hand adornment tying the ${occasion} look together.`, platform: 'Amazon', specs: 'Polished finish' },
        ],
      };
    }

    let spent = 0;
    const items = data.items.map((it: any) => {
      const p = Number(it.estimated_price) || 0;
      spent += p * (it.quantity || 1);
      const plat = it.platform || 'CaratLane';
      return { ...it, estimated_price: p, platform: plat, purchase_link: getSearchUrl(plat, `${it.name} ${metal_preference} jewelry`), badge: plat === 'CaratLane' ? 'Jewelry' : plat === 'Myntra' ? 'Fashion & Jewelry' : 'E-Commerce' };
    });

    const result = {
      planner_type: 'jewelry',
      title: data.title || `${jewelry_type} Curation`,
      summary: data.summary,
      ai_analysis: data.ai_analysis,
      allocations: data.allocations,
      items,
      budget_summary: { total_budget: b, estimated_total: spent, remaining_budget: Math.max(0, b - spent), is_within_budget: spent <= b },
      created_at: new Date().toISOString(),
    };

    res.json(saveRecommendation(user, 'jewelry', b, req.body, result));
  } catch (err: any) { res.status(500).json({ error: err.message }); }
});

// HISTORY & DETAILS
app.get('/history', (req: Request, res: Response) => {
  const user = getUser(req);
  const records = loadStore().recommendations
    .filter((r: any) => (user ? r.user_id === user.id : r.user_id === null))
    .sort((a: any, b: any) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
  res.json({ records, total: records.length });
});

app.get('/recommendations-details', (req: Request, res: Response) => {
  const { planner_type, rec_id } = req.query;
  const store = loadStore();
  const rec = rec_id
    ? store.recommendations.find((r: any) => r.id === Number(rec_id))
    : store.recommendations.filter((r: any) => !planner_type || r.planner_type === planner_type).pop();
  if (!rec) return res.status(404).json({ error: 'Not found' });
  res.json(rec);
});

// EXPORT REPO ZIP
app.get('/api/export-project-zip', async (_req, res) => {
  try {
    const zip = new JSZip();
    const files = [
      'main.py', 'requirements.txt', '.env.example', 'README.md', 'database.py', 'config.py', 'gemini_utils.py', 'auth.py',
      'models/__init__.py', 'models/user.py', 'models/recommendation.py',
      'schemas/__init__.py', 'schemas/user_schema.py', 'schemas/planner_schema.py', 'schemas/recommendation_schema.py',
      'routes/__init__.py', 'routes/auth_routes.py', 'routes/home_routes.py', 'routes/party_routes.py', 'routes/jewelry_routes.py', 'routes/recommendation_routes.py', 'routes/history_routes.py',
      'services/__init__.py', 'services/gemini_service.py', 'services/recommendation_service.py', 'services/platform_service.py',
      'templates/base.html', 'templates/index.html', 'templates/login.html', 'templates/register.html', 'templates/dashboard.html',
      'templates/home_planner.html', 'templates/home_recommendations.html', 'templates/party_planner.html', 'templates/party_recommendations.html',
      'templates/jewelry_planner.html', 'templates/jewelry_recommendations.html', 'templates/history.html', 'templates/testimonials.html',
      'static/css/style.css', 'static/js/main.js', 'static/js/home.js', 'static/js/party.js', 'static/js/jewelry.js',
    ];
    for (const f of files) {
      const fp = path.resolve(process.cwd(), f);
      if (fs.existsSync(fp)) zip.file(`PocketSmart-AI/${f}`, fs.readFileSync(fp));
    }
    const buf = await zip.generateAsync({ type: 'nodebuffer' });
    res.setHeader('Content-Type', 'application/zip');
    res.setHeader('Content-Disposition', 'attachment; filename="PocketSmart-AI.zip"');
    res.send(buf);
  } catch (err: any) { res.status(500).json({ error: err.message }); }
});

// VITE MIDDLEWARE SETUP
async function start() {
  if (process.env.NODE_ENV !== 'production') {
    const vite = await createViteServer({ server: { middlewareMode: true }, appType: 'spa' });
    app.use(vite.middlewares);
  } else {
    const dist = path.resolve(process.cwd(), 'dist');
    app.use(express.static(dist));
    app.get('*', (_req, res) => res.sendFile(path.resolve(dist, 'index.html')));
  }
  app.listen(PORT, '0.0.0.0', () => console.log(`PocketSmart server running on ${PORT}`));
}
start();
