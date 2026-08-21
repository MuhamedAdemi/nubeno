import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../api/client";
import type { MenuItem, OrderItem, PaymentMethod } from "../api/types";
import { useLang } from "../i18n/LangContext";
import { LanguageSwitcher } from "../components/LanguageSwitcher";
import { MenuItemCard } from "../components/MenuItemCard";
import { ModifierModal } from "../components/ModifierModal";
import { CartPanel } from "../components/CartPanel";
import { DraftCartPanel, type DraftItem } from "../components/DraftCartPanel";
import { TransferTableModal } from "../components/TransferTableModal";
import { PaymentMethodModal } from "../components/PaymentMethodModal";

let draftKeyCounter = 0;

type ModalState =
  | { mode: "add"; item: MenuItem }
  | { mode: "edit-registered"; item: MenuItem; orderItem: OrderItem }
  | { mode: "edit-draft"; item: MenuItem; draftItem: DraftItem }
  | null;

interface PendingPayment {
  itemIds: number[];
  total: number;
}

export function OrderPage() {
  const { tableId } = useParams();
  const { t } = useLang();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [group, setGroup] = useState<"FOOD" | "DRINK">("FOOD");
  const [modalState, setModalState] = useState<ModalState>(null);
  const [draftItems, setDraftItems] = useState<DraftItem[]>([]);
  const [showTransfer, setShowTransfer] = useState(false);
  const [pendingPayment, setPendingPayment] = useState<PendingPayment | null>(null);

  const { data: tables } = useQuery({ queryKey: ["tables"], queryFn: api.getTables, refetchInterval: 5000 });
  const table = tables?.find((tb) => tb.id === Number(tableId));
  const isRegistered = !!table?.open_order_id;

  const { data: menu } = useQuery({ queryKey: ["menu"], queryFn: api.getMenu });

  const { data: order } = useQuery({
    queryKey: ["order", table?.open_order_id],
    queryFn: () => api.getOrder(table!.open_order_id!),
    enabled: !!table?.open_order_id,
  });

  const categories = menu ?? [];
  // The reference POS layout uses just two top-level tabs (Food/Drinks) with
  // every item in that group shown together in one grid, ordered by type
  // (pizzas, then salads, then the rest) — not a tab per category. Category
  // order + item order from the API already produces that grouping.
  const groupItems = categories.filter((c) => c.group === group).flatMap((c) => c.items);

  function invalidateOrder() {
    queryClient.invalidateQueries({ queryKey: ["order", table?.open_order_id] });
    queryClient.invalidateQueries({ queryKey: ["tables"] });
  }

  const addItemMutation = useMutation({
    mutationFn: (payload: {
      menu_item_id: number;
      quantity: number;
      note?: string;
      removed_modifier_option_ids: number[];
    }) => api.addOrderItem(table!.open_order_id!, payload),
    onSuccess: invalidateOrder,
  });

  const updateItemMutation = useMutation({
    mutationFn: ({
      itemId,
      payload,
    }: {
      itemId: number;
      payload: { quantity: number; note: string; removed_modifier_option_ids: number[] };
    }) => api.updateOrderItem(table!.open_order_id!, itemId, payload),
    onSuccess: invalidateOrder,
  });

  const deleteItemMutation = useMutation({
    mutationFn: (itemId: number) => api.deleteOrderItem(table!.open_order_id!, itemId),
    onSuccess: invalidateOrder,
  });

  const payMutation = useMutation({
    mutationFn: ({
      itemIds,
      paymentMethod,
      cashAmount,
    }: {
      itemIds: number[];
      paymentMethod: PaymentMethod;
      cashAmount?: number;
    }) => api.payOrder(table!.open_order_id!, itemIds, paymentMethod, cashAmount),
    onSuccess: (result) => {
      invalidateOrder();
      navigate(`/orders/${result.id}/print?items=${result.paid_item_ids.join(",")}`);
    },
  });

  const transferMutation = useMutation({
    mutationFn: (destinationTableId: number) => api.transferOrder(table!.open_order_id!, destinationTableId),
    onSuccess: (movedOrder) => {
      queryClient.invalidateQueries({ queryKey: ["tables"] });
      setShowTransfer(false);
      navigate(`/tables/${movedOrder.table}`);
    },
  });

  const cancelMutation = useMutation({
    mutationFn: () => api.cancelOrder(table!.open_order_id!),
    onSuccess: () => {
      invalidateOrder();
      navigate("/");
    },
  });

  const registerMutation = useMutation({
    mutationFn: async () => {
      const newOrder = await api.openTableOrder(Number(tableId));
      for (const item of draftItems) {
        await api.addOrderItem(newOrder.id, {
          menu_item_id: item.menuItem.id,
          quantity: item.quantity,
          note: item.note,
          removed_modifier_option_ids: item.removedOptions.map((o) => o.id),
        });
      }
      return newOrder;
    },
    onSuccess: () => {
      setDraftItems([]);
      queryClient.invalidateQueries({ queryKey: ["tables"] });
    },
  });

  // Tapping an item always adds it with the standard recipe — customizing
  // (removing ingredients, adding a note) is a separate, optional action via
  // the "Personalizo" button, never forced. The same button (and modal) is
  // reused on already-added cart lines to edit them afterwards.
  function handleAdd(item: MenuItem) {
    if (isRegistered) {
      addItemMutation.mutate({ menu_item_id: item.id, quantity: 1, removed_modifier_option_ids: [] });
    } else {
      setDraftItems((prev) => [
        ...prev,
        { key: String(draftKeyCounter++), menuItem: item, quantity: 1, removedOptions: [], note: "" },
      ]);
    }
  }

  function handleModalConfirm(removedOptionIds: number[], quantity: number, note: string) {
    if (!modalState) return;

    if (modalState.mode === "add") {
      if (isRegistered) {
        addItemMutation.mutate({
          menu_item_id: modalState.item.id,
          quantity,
          note,
          removed_modifier_option_ids: removedOptionIds,
        });
      } else {
        const removedOptions = (modalState.item.modifier_group?.options ?? []).filter((o) =>
          removedOptionIds.includes(o.id)
        );
        setDraftItems((prev) => [
          ...prev,
          { key: String(draftKeyCounter++), menuItem: modalState.item, quantity, removedOptions, note },
        ]);
      }
    } else if (modalState.mode === "edit-registered") {
      updateItemMutation.mutate({
        itemId: modalState.orderItem.id,
        payload: { quantity, note, removed_modifier_option_ids: removedOptionIds },
      });
    } else if (modalState.mode === "edit-draft") {
      const removedOptions = (modalState.item.modifier_group?.options ?? []).filter((o) =>
        removedOptionIds.includes(o.id)
      );
      const key = modalState.draftItem.key;
      setDraftItems((prev) => prev.map((i) => (i.key === key ? { ...i, quantity, note, removedOptions } : i)));
    }
    setModalState(null);
  }

  const busy =
    addItemMutation.isPending ||
    updateItemMutation.isPending ||
    deleteItemMutation.isPending ||
    payMutation.isPending ||
    cancelMutation.isPending ||
    registerMutation.isPending ||
    transferMutation.isPending;

  const freeTables = (tables ?? []).filter((tb) => tb.status === "FREE");

  return (
    <div className="page order-page">
      <div className="pos-topbar">
        <span className="pos-topbar-icon">N</span>
        <span className="pos-topbar-brand">NUBENO</span>
      </div>
      <header className="page-header">
        <button className="btn btn-ghost" onClick={() => navigate("/")}>
          ← {t("back_to_tables")}
        </button>
        <div className="header-actions">
          <LanguageSwitcher />
          <button className="btn btn-ghost" onClick={() => navigate("/cash-register")}>
            {t("cash_register")}
          </button>
        </div>
      </header>

      <div className="order-layout">
        {table && !isRegistered && (
          <DraftCartPanel
            tableNumber={table.number}
            items={draftItems}
            busy={busy}
            onDeleteItem={(key) => setDraftItems((prev) => prev.filter((i) => i.key !== key))}
            onEditItem={(draftItem) => setModalState({ mode: "edit-draft", item: draftItem.menuItem, draftItem })}
            onRegister={() => {
              if (confirm(t("confirm_register"))) registerMutation.mutate();
            }}
          />
        )}

        {table && isRegistered && order && (
          <CartPanel
            order={order}
            busy={busy}
            onDeleteItem={(itemId) => {
              if (confirm(t("confirm_delete_item"))) deleteItemMutation.mutate(itemId);
            }}
            onEditItem={(orderItem) =>
              setModalState({ mode: "edit-registered", item: orderItem.menu_item, orderItem })
            }
            onPayClick={(itemIds, total) => setPendingPayment({ itemIds, total })}
            onCancelOrder={() => {
              if (confirm(t("confirm_cancel"))) cancelMutation.mutate();
            }}
            onPrintKitchen={() => navigate(`/orders/${order.id}/kitchen-print`)}
            onTransferClick={() => setShowTransfer(true)}
          />
        )}

        <main className="menu-browser">
          <div className="category-tabs">
            <button
              className={group === "FOOD" ? "category-tab active" : "category-tab"}
              onClick={() => setGroup("FOOD")}
            >
              {t("food")}
            </button>
            <button
              className={group === "DRINK" ? "category-tab active" : "category-tab"}
              onClick={() => setGroup("DRINK")}
            >
              {t("drinks")}
            </button>
          </div>

          <div className="menu-item-grid">
            {groupItems.map((item) => (
              <MenuItemCard
                key={item.id}
                item={item}
                onAdd={() => handleAdd(item)}
                onCustomize={() => setModalState({ mode: "add", item })}
              />
            ))}
          </div>
        </main>
      </div>

      {modalState && (
        <ModifierModal
          item={modalState.item}
          mode={modalState.mode === "add" ? "add" : "edit"}
          initialRemovedOptionIds={
            modalState.mode === "edit-registered"
              ? modalState.orderItem.removed_modifiers.map((m) => m.id)
              : modalState.mode === "edit-draft"
                ? modalState.draftItem.removedOptions.map((o) => o.id)
                : []
          }
          initialQuantity={
            modalState.mode === "edit-registered"
              ? modalState.orderItem.quantity
              : modalState.mode === "edit-draft"
                ? modalState.draftItem.quantity
                : 1
          }
          initialNote={
            modalState.mode === "edit-registered"
              ? modalState.orderItem.note
              : modalState.mode === "edit-draft"
                ? modalState.draftItem.note
                : ""
          }
          onClose={() => setModalState(null)}
          onConfirm={handleModalConfirm}
        />
      )}

      {showTransfer && (
        <TransferTableModal
          freeTables={freeTables}
          onClose={() => setShowTransfer(false)}
          onSelect={(destinationTableId) => {
            if (confirm(t("confirm_transfer"))) transferMutation.mutate(destinationTableId);
          }}
        />
      )}

      {pendingPayment && (
        <PaymentMethodModal
          total={pendingPayment.total}
          onClose={() => setPendingPayment(null)}
          onChoose={(paymentMethod, cashAmount) => {
            payMutation.mutate({ itemIds: pendingPayment.itemIds, paymentMethod, cashAmount });
            setPendingPayment(null);
          }}
        />
      )}
    </div>
  );
}
