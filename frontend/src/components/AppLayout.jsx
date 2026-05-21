import { Link, NavLink, Outlet } from "react-router-dom";
import {
  BarChart3,
  Bot,
  CheckCircle2,
  Inbox,
  LayoutDashboard,
  ShieldCheck,
} from "lucide-react";

const navItems = [
  {
    label: "Dashboard",
    path: "/",
    icon: LayoutDashboard,
  },
  {
    label: "Inbox",
    path: "/inbox",
    icon: Inbox,
  },
  {
    label: "Analytics",
    path: "/analytics",
    icon: BarChart3,
  },
  {
    label: "Audit / Agent",
    path: "/audit",
    icon: Bot,
  },
  {
    label: "Human Review",
    path: "/review",
    icon: CheckCircle2,
  },
];

export default function AppLayout() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <Link to="/" className="brand">
          <div className="brand-icon">
            <ShieldCheck size={24} />
          </div>
          <div>
            <h1>Agentic CRM</h1>
            <p>AI Triage Platform</p>
          </div>
        </Link>

        <nav className="nav-list">
          {navItems.map((item) => {
            const Icon = item.icon;

            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  isActive ? "nav-link nav-link-active" : "nav-link"
                }
              >
                <Icon size={18} />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>

        <div className="sidebar-footer">
          <p>Backend</p>
          <strong>FastAPI :8001</strong>
        </div>
      </aside>

      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
