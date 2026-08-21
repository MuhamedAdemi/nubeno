import { Routes, Route, Navigate } from "react-router-dom";
import { LoginPage } from "./pages/LoginPage";
import { TableGridPage } from "./pages/TableGridPage";
import { OrderPage } from "./pages/OrderPage";
import { PrintReceiptPage } from "./pages/PrintReceiptPage";
import { KitchenPrintPage } from "./pages/KitchenPrintPage";
import { AnalyticsPage } from "./pages/AnalyticsPage";
import { CashRegisterPage } from "./pages/CashRegisterPage";
import { RequireAuth } from "./auth/RequireAuth";
import { RequireAdmin } from "./auth/RequireAdmin";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <RequireAuth>
            <TableGridPage />
          </RequireAuth>
        }
      />
      <Route
        path="/tables/:tableId"
        element={
          <RequireAuth>
            <OrderPage />
          </RequireAuth>
        }
      />
      <Route
        path="/orders/:orderId/print"
        element={
          <RequireAuth>
            <PrintReceiptPage />
          </RequireAuth>
        }
      />
      <Route
        path="/orders/:orderId/kitchen-print"
        element={
          <RequireAuth>
            <KitchenPrintPage />
          </RequireAuth>
        }
      />
      <Route
        path="/analytics"
        element={
          <RequireAdmin>
            <AnalyticsPage />
          </RequireAdmin>
        }
      />
      <Route
        path="/cash-register"
        element={
          <RequireAuth>
            <CashRegisterPage />
          </RequireAuth>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
