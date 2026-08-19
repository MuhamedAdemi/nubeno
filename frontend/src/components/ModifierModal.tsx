import { useState } from "react";
import type { MenuItem } from "../api/types";
import { itemName } from "../api/types";
import { useLang } from "../i18n/LangContext";

interface Props {
  item: MenuItem;
  mode?: "add" | "edit";
  initialRemovedOptionIds?: number[];
  initialQuantity?: number;
  initialNote?: string;
  onClose: () => void;
  onConfirm: (removedOptionIds: number[], quantity: number, note: string) => void;
}

export function ModifierModal({
  item,
  mode = "add",
  initialRemovedOptionIds = [],
  initialQuantity = 1,
  initialNote = "",
  onClose,
  onConfirm,
}: Props) {
  const { lang, t } = useLang();
  const options = item.modifier_group?.options ?? [];
  const [checked, setChecked] = useState<Record<number, boolean>>(
    Object.fromEntries(options.map((o) => [o.id, !initialRemovedOptionIds.includes(o.id)]))
  );
  const [quantity, setQuantity] = useState(initialQuantity);
  const [note, setNote] = useState(initialNote);

  function toggle(id: number) {
    setChecked((prev) => ({ ...prev, [id]: !prev[id] }));
  }

  function selectAll() {
    setChecked(Object.fromEntries(options.map((o) => [o.id, true])));
  }

  function deselectAll() {
    setChecked(Object.fromEntries(options.map((o) => [o.id, false])));
  }

  function handleConfirm() {
    const removedIds = options.filter((o) => !checked[o.id]).map((o) => o.id);
    onConfirm(removedIds, quantity, note.trim());
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h2>{itemName(item, lang)}</h2>
        {item.variant_label && <div className="variant-label">{item.variant_label}</div>}

        {options.length > 0 && (
          <>
            <p className="modifier-hint">{t("modifier_hint")}</p>
            <div className="modifier-select-all">
              <button className="btn btn-ghost" onClick={selectAll}>
                {t("select_all")}
              </button>
              <button className="btn btn-ghost" onClick={deselectAll}>
                {t("deselect_all")}
              </button>
            </div>
            <div className="modifier-list">
              {options.map((opt) => (
                <label key={opt.id} className="modifier-option">
                  <input type="checkbox" checked={!!checked[opt.id]} onChange={() => toggle(opt.id)} />
                  <span>{itemName(opt, lang)}</span>
                </label>
              ))}
            </div>
          </>
        )}

        <label className="note-field">
          {t("note_label")}
          <textarea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder={t("note_placeholder")}
            rows={2}
          />
        </label>

        <div className="quantity-row">
          <span>{t("quantity")}</span>
          <div className="quantity-controls">
            <button className="btn btn-ghost" onClick={() => setQuantity((q) => Math.max(1, q - 1))}>
              −
            </button>
            <span className="quantity-value">{quantity}</span>
            <button className="btn btn-ghost" onClick={() => setQuantity((q) => q + 1)}>
              +
            </button>
          </div>
        </div>

        <div className="modal-actions">
          <button className="btn btn-ghost" onClick={onClose}>
            {t("close")}
          </button>
          <button className="btn btn-primary" onClick={handleConfirm}>
            {mode === "edit" ? t("save_changes") : t("add_to_order")}
          </button>
        </div>
      </div>
    </div>
  );
}
