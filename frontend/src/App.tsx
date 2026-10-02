import { FormEvent, useEffect, useState } from "react";
import {
  Bell, Building2, CheckCircle2, ClipboardList, LayoutDashboard, LogOut,
  MapPin, Menu, Moon, Search, Settings, Sun, Users, X,
} from "lucide-react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

type Theme = "light" | "dark";
type FontSize = "small" | "medium" | "large";
type User = { username: string; is_active: boolean };
type Dashboard = { message: string; address_count: number; open_requests: number; pending_requests: number };
type Address = { id: number; address_text: string; address_type: string; is_active: boolean };
type ServiceRequest = { id: number; title: string; description: string; priority: string; status: string; address_id: number; address_text: string; created_by: string; created_at: string };

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
  const [addresses, setAddresses] = useState<Address[]>([]);
  const [requests, setRequests] = useState<ServiceRequest[]>([]);
  const [addressText, setAddressText] = useState("");
  const [addressType, setAddressType] = useState("building");
  const [requestTitle, setRequestTitle] = useState("");
  const [requestDescription, setRequestDescription] = useState("");
  const [requestPriority, setRequestPriority] = useState("normal");
  const [requestAddressId, setRequestAddressId] = useState("");
  const [notice, setNotice] = useState("");
  const [theme, setTheme] = useState<Theme>(() => {
    const saved = localStorage.getItem("jkx_theme");
    return saved === "dark" ? "dark" : "light";
  });
  const [fontSize, setFontSize] = useState<FontSize>(() => {
    const saved = localStorage.getItem("jkx_font_size");
    return saved === "small" || saved === "large" ? saved : "medium";
  });

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

  useEffect(() => {
    localStorage.setItem("jkx_theme", theme);
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  useEffect(() => {
    localStorage.setItem("jkx_font_size", fontSize);
    document.documentElement.dataset.fontSize = fontSize;
  }, [fontSize]);

  useEffect(() => {
    if (!token || !user) return;
    const headers = { Authorization: `Bearer ${token}` };
    if (active === "Адреса" || active === "Заявки") {
      fetch(`${API_URL}/api/addresses`, { headers })
        .then(async response => {
          if (!response.ok) throw new Error("Не удалось загрузить справочник адресов.");
          setAddresses(await response.json());
        })
        .catch(e => setError(e instanceof Error ? e.message : "Ошибка загрузки адресов."));
    }
    if (active === "Заявки") {
      fetch(`${API_URL}/api/requests`, { headers })
        .then(async response => {
          if (!response.ok) throw new Error("Не удалось загрузить заявки.");
          setRequests(await response.json());
        })
        .catch(e => setError(e instanceof Error ? e.message : "Ошибка загрузки заявок."));
    }
  }, [token, user, active]);

  async function handleCreateAddress(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setNotice("");
    try {
      const response = await fetch(`${API_URL}/api/addresses`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ address_text: addressText.trim(), address_type: addressType }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Не удалось сохранить адрес.");
      setAddresses(previous => [...previous, data].sort((a, b) => a.address_text.localeCompare(b.address_text, "ru")));
      setAddressText("");
      setNotice("Адрес добавлен в справочник.");
      setDashboard(previous => previous ? { ...previous, address_count: previous.address_count + 1 } : previous);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка сохранения адреса.");
    }
  }

  async function handleCreateRequest(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setNotice("");
    if (!requestAddressId) {
      setError("Выберите адрес из справочника адресов.");
      return;
    }
    try {
      const response = await fetch(`${API_URL}/api/requests`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          title: requestTitle.trim(),
          description: requestDescription.trim(),
          priority: requestPriority,
          address_id: Number(requestAddressId),
        }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Не удалось создать заявку.");
      setRequests(previous => [data, ...previous]);
      setRequestTitle("");
      setRequestDescription("");
      setRequestPriority("normal");
      setNotice("Заявка создана и привязана к выбранному адресу.");
      setDashboard(previous => previous ? { ...previous, open_requests: previous.open_requests + 1, pending_requests: previous.pending_requests + 1 } : previous);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка создания заявки.");
    }
  }

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
      <main className={`login-page theme-${theme}`}>
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
    <div className={`app-shell theme-${theme}`}>
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
          </> : active === "Адреса" ? <section className="directory-layout">
            <div className="surface-card">
              <div className="card-heading"><div><h3>Добавить адрес</h3><p>Адреса из этого списка доступны при создании заявок</p></div><MapPin size={20} className="subtle-icon" /></div>
              <form className="data-form" onSubmit={handleCreateAddress}>
                <label htmlFor="addressType">Тип адреса</label>
                <select id="addressType" value={addressType} onChange={e => setAddressType(e.target.value)}><option value="locality">Населённый пункт</option><option value="street">Улица</option><option value="building">Дом</option><option value="apartment">Квартира</option><option value="other">Другой адрес</option></select>
                <label htmlFor="addressText">Адрес / название</label>
                <input id="addressText" value={addressText} onChange={e => setAddressText(e.target.value)} placeholder="Например, ул. Лесная, д. 12, кв. 4" required minLength={2} maxLength={500} />
                <button className="primary-button" type="submit">Добавить в справочник</button>
              </form>
            </div>
            <div className="surface-card"><div className="card-heading"><div><h3>Справочник адресов</h3><p>{addresses.length} записей</p></div><Search size={20} className="subtle-icon" /></div>
              {addresses.length ? <div className="address-list">{addresses.map(address => <div className="address-row" key={address.id}><span className="action-icon blue"><MapPin size={17} /></span><div><strong>{address.address_text}</strong><small>{addressTypeLabel(address.address_type)}</small></div></div>)}</div> : <div className="empty-state">Справочник пока пуст. Добавьте адрес — он появится в списке выбора при заведении заявки.</div>}
            </div>
          </section> : active === "Заявки" ? <div className="directory-layout">
            <section className="surface-card"><div className="card-heading"><div><h3>Новая заявка</h3><p>Обязательно выберите адрес из справочника</p></div><ClipboardList size={20} className="subtle-icon" /></div>
              <form className="data-form" onSubmit={handleCreateRequest}>
                <label htmlFor="requestTitle">Тема заявки</label><input id="requestTitle" value={requestTitle} onChange={e => setRequestTitle(e.target.value)} placeholder="Например, протечка в подъезде" required minLength={2} maxLength={200} />
                <label htmlFor="requestAddress">Адрес объекта <span className="required-mark">*</span></label>
                <select id="requestAddress" value={requestAddressId} onChange={e => setRequestAddressId(e.target.value)} required><option value="">Выберите адрес из справочника…</option>{addresses.map(address => <option key={address.id} value={address.id}>{address.address_text}</option>)}</select>
                {addresses.length === 0 && <p className="form-help">Нет адресов для выбора. Сначала добавьте адрес в разделе «Адреса».</p>}
                <label htmlFor="requestPriority">Приоритет</label><select id="requestPriority" value={requestPriority} onChange={e => setRequestPriority(e.target.value)}><option value="low">Низкий</option><option value="normal">Обычный</option><option value="high">Высокий</option><option value="urgent">Срочный</option></select>
                <label htmlFor="requestDescription">Описание</label><textarea id="requestDescription" value={requestDescription} onChange={e => setRequestDescription(e.target.value)} placeholder="Опишите проблему или работы" rows={3} maxLength={5000} />
                <button className="primary-button" type="submit" disabled={addresses.length === 0}>Создать заявку</button>
              </form>
            </section>
            <section className="surface-card"><div className="card-heading"><div><h3>Заявки</h3><p>{requests.length} записей</p></div><ClipboardList size={20} className="subtle-icon" /></div>
              {requests.length ? <div className="request-list">{requests.map(request => <article className="request-row" key={request.id}><div className="request-row-top"><strong>#{request.id} · {request.title}</strong><span className={`priority-pill priority-${request.priority}`}>{priorityLabel(request.priority)}</span></div><div className="request-address"><MapPin size={14} /> {request.address_text}</div>{request.description && <p>{request.description}</p>}<small>{new Date(request.created_at).toLocaleString("ru-RU")} · {request.created_by}</small></article>)}</div> : <div className="empty-state">Созданные заявки появятся здесь вместе с выбранным адресом.</div>}
            </section>
          </div> : <section className="settings-layout">
            <div className="surface-card settings-card">
              <div className="card-heading"><div><h3>Внешний вид</h3><p>Выберите оформление рабочего места</p></div><Settings size={20} className="subtle-icon" /></div>
              <div className="theme-options">
                <button type="button" className={`theme-option ${theme === "light" ? "selected" : ""}`} onClick={() => setTheme("light")}>
                  <span className="theme-preview light-preview"><Sun size={20} /></span>
                  <span><strong>Светлая тема</strong><small>Светлый фон и тёмный текст</small></span>
                  {theme === "light" && <CheckCircle2 size={19} className="theme-check" />}
                </button>
                <button type="button" className={`theme-option ${theme === "dark" ? "selected" : ""}`} onClick={() => setTheme("dark")}>
                  <span className="theme-preview dark-preview"><Moon size={20} /></span>
                  <span><strong>Тёмная тема</strong><small>Тёмный фон и светлый текст</small></span>
                  {theme === "dark" && <CheckCircle2 size={19} className="theme-check" />}
                </button>
              </div>
              <div className="font-size-options">
                <button type="button" className={`font-size-option ${fontSize === "small" ? "selected" : ""}`} onClick={() => setFontSize("small")}>
                  <span className="font-size-sample small">А</span>
                  <span><strong>Мелкий</strong><small>Компактное отображение</small></span>
                  {fontSize === "small" && <CheckCircle2 size={19} className="theme-check" />}
                </button>
                <button type="button" className={`font-size-option ${fontSize === "medium" ? "selected" : ""}`} onClick={() => setFontSize("medium")}>
                  <span className="font-size-sample medium">А</span>
                  <span><strong>Обычный</strong><small>Стандартный размер текста</small></span>
                  {fontSize === "medium" && <CheckCircle2 size={19} className="theme-check" />}
                </button>
                <button type="button" className={`font-size-option ${fontSize === "large" ? "selected" : ""}`} onClick={() => setFontSize("large")}>
                  <span className="font-size-sample large">А</span>
                  <span><strong>Крупный</strong><small>Увеличенный размер текста</small></span>
                  {fontSize === "large" && <CheckCircle2 size={19} className="theme-check" />}
                </button>
              </div>
            </div>
            <div className="surface-card settings-card">
              <div className="card-heading"><div><h3>Текущая тема</h3><p>Выбор сохраняется на этом компьютере</p></div><div className="settings-theme-badge">{theme === "dark" ? <Moon size={16} /> : <Sun size={16} />}{theme === "dark" ? "Тёмная" : "Светлая"}</div></div>
              <div className="settings-note"><CheckCircle2 size={18} /> Оформление и размер текста применяются сразу ко всему приложению, включая меню, карточки, формы, справочники, заявки и панель настроек.</div>
            </div>
          </section>}
          {notice && <div className="success-message" role="status">{notice}</div>}{error && <div className="error-message inline-error" role="alert">{error}</div>}<footer className="page-footer">ЖКХ · Диспетчер <span>Версия 0.2.0 · Прототип</span></footer>
        </div>
      </main>
    </div>
  );
}

function addressTypeLabel(type: string) {
  const labels: Record<string, string> = { locality: "Населённый пункт", street: "Улица", building: "Дом", apartment: "Квартира", other: "Другой адрес" };
  return labels[type] || "Адрес";
}

function priorityLabel(priority: string) {
  const labels: Record<string, string> = { low: "Низкий", normal: "Обычный", high: "Высокий", urgent: "Срочный" };
  return labels[priority] || priority;
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
