import { createBrowserRouter, RouterProvider } from "react-router-dom";

import AppLayout from "./components/AppLayout";
import AnalyticsPage from "./pages/AnalyticsPage";
import AuditPage from "./pages/AuditPage";
import DashboardPage from "./pages/DashboardPage";
import InboxPage from "./pages/InboxPage";

const router = createBrowserRouter([
  {
    path: "/",
    element: <AppLayout />,
    children: [
      {
        index: true,
        element: <DashboardPage />,
      },
      {
        path: "inbox",
        element: <InboxPage />,
      },
      {
        path: "analytics",
        element: <AnalyticsPage />,
      },
      {
        path: "audit",
        element: <AuditPage />,
      },
    ],
  },
]);

export default function App() {
  return <RouterProvider router={router} />;
}