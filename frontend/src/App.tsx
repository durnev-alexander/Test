import { FormEvent, useEffect, useState } from "react";
import {
  Bell, Building2, CheckCircle2, ClipboardList, LayoutDashboard, LogOut,
  MapPin, Menu, Search, Settings, Users, X,
} from "lucide-react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

type User = { username: string; is_active: boolean };
type Dashboard = { message: string; address_count: number; open_requests: number; pending_requests: number };

export default function App() {
  const [token, setToken] = useState(() => sessionStorage.getItem("jkx_token") || "");
  const [user, setUser] = useState<User | null>(null);
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [username, setUsername] = useState("demo");
  const [password, setPassword] = useState("demo");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [active, setActive] = useState("Главная");
  const [sidebarOpen, setSidebarOpen] = useState(false);

  async function loadSession(accessToken: string) {
    const headers = { Authorization: `Bearer ${accessToken}` };
    const meResponse = await fetch(`${API_URL}/api/auth/me`, { headers });
    if (!meResponse.ok) throw new Error("Сессия истекла. Войдите снова.");
    const me: User = await meResponse.json();
    const dashboardResponse = await fetch(`${API_URL}/api/dashboard`, { headers });
    if (!dashboardResponse.ok) throw new Error("Не удалось загрузить рабочую область.");
    setUser(me);
    setDashboard(await dashboardResponse.json());
  }

  useEffect(() => {
    if (!token) return;
    loadSession(token).catch(() => {
      sessionStorage.removeItem("jkx_token");
      setToken("");
      setUser(null);
    });
  }, [token]);

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      const response = await fetch(`${API_URL}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Не удалось войти.");
      sessionStorage.setItem("jkx_token", data.access_token);
      setToken(data.access_token);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка подключения к серверу.");
    } finally {
      setBusy(false);
    }
  }

  function logout() {
    sessionStorage.removeItem("jkx_token");
    setToken("");
    setUser(null);
    setDashboard(null);
    setPassword("");
  }

  if (!token || !user) {
    return (
      <main className="login-page">
        <section className="login-brand">
          <div className="brand-mark"><Building2 size={30} /></div>
          <p className="eyebrow">СИСТЕМА УПРАВЛЕНИЯ</p>
          <h1>ЖКХ<br />Диспетчер</h1>
          <p className="brand-copy">Все задачи жилищного хозяйства — в одном рабочем пространстве.</p>
          <div className="brand-footer"><CheckCircle2 size={16} /> Организованная работа. Прозрачные процессы.</div>
        </section>
        <section className="login-panel">
          <form className="login-card" onSubmit={handleLogin}>
            <div className="mobile-logo"><Building2 /> ЖКХ · Диспетчер</div>
            <p className="eyebrow">С ДОБРЫМ ДНЁМ</p>
            <h2>Вход в систему</h2>
            <p className="muted">Введите данные вашей учётной записи.</p>
            <label htmlFor="username">Имя пользователя</label>
            <input id="username" autoComplete="username" value={username} onChange={e => setUsername(e.target.value)} required />
            <label htmlFor="password">Пароль</label>
            <input id="password" type="password" autoComplete="current-password" value={password} onChange={e => setPassword(e.target.value)} required />
            {error && <div className="error-message" role="alert">{error}</div>}
            <button className="primary-button login-button" type="submit" disabled={busy}>{busy ? "Входим…" : "Войти в систему"}</button>
            <div className="demo-hint"><span className="demo-dot" /> Для разработки: <strong>demo / demo</strong></div>
          </form>
          <p className="copyright">ЖКХ · Диспетчерская система</p>
        </section>
      </main>
    );
  }

  const nav = [
    { name: "Главная", icon: LayoutDashboard },
    { name: "Адреса", icon: MapPin },
    { name: "Заявки", icon: ClipboardList },
    { name: "Жильцы", icon: Users },
    { name: "Настройки", icon: Settings },
  ];

  return (
    <div className="app-shell">
      {sidebarOpen && <button className="mobile-scrim" aria-label="Закрыть меню" onClick={() => setSidebarOpen(false)} />}
      <aside className={`sidebar ${sidebarOpen ? "sidebar-open" : ""}`}>
        <div className="sidebar-brand"><span className="brand-mark small"><Building2 size={21} /></span><span>ЖКХ <small>Диспетчер</small></span><button className="icon-button mobile-close" onClick={() => setSidebarOpen(false)} aria-label="Закрыть меню"><X size={18} /></button></div>
        <div className="nav-caption">РАБОЧЕЕ МЕСТО</div>
        <nav>{nav.map(item => {
          const Icon = item.icon;
          return <button key={item.name} className={`nav-item ${active === item.name ? "active" : ""}`} onClick={() => { setActive(item.name); setSidebarOpen(false); }}><Icon size={18} /><span>{item.name}</span>{item.name === "Заявки" && <span className="nav-count">0</span>}</button>;
        })}</nav>
        <div className="sidebar-bottom"><div className="help-card"><span className="help-icon"><CheckCircle2 size={18} /></span><strong>Рабочее место готово</strong><p>Вы вошли в систему. Можно приступать к работе.</p></div><button className="nav-item logout" onClick={logout}><LogOut size={18} /><span>Выйти из системы</span></button></div>
      </aside>
      <main className="main-area">
        <header className="topbar"><button className="icon-button menu-toggle" onClick={() => setSidebarOpen(true)} aria-label="Открыть меню"><Menu size={21} /></button><div className="breadcrumbs">Рабочее место <span>/</span> <strong>{active}</strong></div><div className="topbar-right"><button className="icon-button notification" aria-label="Уведомления"><Bell size={19} /><i /></button><div className="user-chip"><div className="avatar">{user.username.slice(0, 1).toUpperCase()}</div><div><strong>{user.username}</strong><small>Диспетчер</small></div></div></div></header>
        <div className="page-content">
          <div className="welcome-row"><div><p className="eyebrow">ОБЗОР СИСТЕМЫ</p><h1>{active === "Главная" ? "Рабочая область" : active}</h1><p className="muted">{active === "Главная" ? dashboard?.message || "Загрузка данных…" : sectionDescription(active)}</p></div><div className="today-badge"><span className="live-dot" /> Система активна</div></div>
          {active === "Главная" ? <>
            <div className="stat-grid">
              <StatCard icon={<MapPin size={20} />} label="Адреса в справочнике" value={dashboard?.address_count ?? "—"} tone="blue" />
              <StatCard icon={<ClipboardList size={20} />} label="Открытые заявки" value={dashboard?.open_requests ?? "—"} tone="orange" />
              <StatCard icon={<Users size={20} />} label="Ожидают обработки" value={dashboard?.pending_requests ?? "—"} tone="purple" />
            </div>
            <div className="content-grid"><section className="surface-card"><div className="card-heading"><div><h3>Быстрые действия</h3><p>Перейдите к нужному разделу</p></div><LayoutDashboard size={20} className="subtle-icon" /></div><div className="quick-actions"><button onClick={() => setActive("Адреса")}><span className="action-icon blue"><MapPin size={19} /></span><span><strong>Справочник адресов</strong><small>Дома, квартиры и улицы</small></span><span className="arrow">→</span></button><button onClick={() => setActive("Заявки")}><span className="action-icon orange"><ClipboardList size={19} /></span><span><strong>Заявки</strong><small>Просмотр и обработка обращений</small></span><span className="arrow">→</span></button><button onClick={() => setActive("Жильцы")}><span className="action-icon purple"><Users size={19} /></span><span><strong>Жильцы</strong><small>Сведения о жителях</small></span><span className="arrow">→</span></button></div></section><section className="surface-card"><div className="card-heading"><div><h3>Состояние системы</h3><p>Основные компоненты</p></div><CheckCircle2 size={20} className="success-icon" /></div><div className="system-row"><span className="system-dot" /><span>Авторизация</span><strong>Работает</strong></div><div className="system-row"><span className="system-dot" /><span>Рабочая область</span><strong>Работает</strong></div><div className="system-row"><span className="system-dot" /><span>Справочник адресов</span><strong>Подготовлен</strong></div><div className="system-note">Данные будут отображаться здесь по мере заполнения справочников.</div></section></div>
          </> : <section className="surface-card section-placeholder"><div className="placeholder-icon">{active === "Адреса" ? <MapPin size={26} /> : active === "Заявки" ? <ClipboardList size={26} /> : active === "Жильцы" ? <Users size={26} /> : <Settings size={26} />}</div><h3>{active === "Адреса" ? "Справочник адресов" : active}</h3><p>{active === "Адреса" ? "Здесь будет доступно добавление населённых пунктов, улиц, домов и квартир." : "Раздел подготовлен для следующего этапа разработки."}</p>{active === "Адреса" && <button className="primary-button" onClick={() => setError("Раздел адресов будет подключён на следующем этапе.")}>Подготовить справочник</button>}</section>}
          <footer className="page-footer">ЖКХ · Диспетчер <span>Версия 0.1.0 · Прототип</span></footer>
        </div>
      </main>
    </div>
  );
}

function sectionDescription(section: string) {
  const descriptions: Record<string, string> = {
    "Адреса": "Единый справочник объектов жилищного хозяйства.",
    "Заявки": "Обращения, аварии и задачи на обслуживание.",
    "Жильцы": "Учёт жильцов и контактных данных.",
    "Настройки": "Настройки приложения и учётных записей.",
  };
  return descriptions[section] || "";
}

function StatCard({ icon, label, value, tone }: { icon: React.ReactNode; label: string; value: string | number; tone: string }) {
  return <section className="stat-card"><div className={`stat-icon ${tone}`}>{icon}</div><div className="stat-label">{label}</div><div className="stat-value">{value}</div><div className="stat-foot"><span className="live-dot" /> Данные системы</div></section>;
}
