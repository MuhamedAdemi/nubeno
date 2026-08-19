import type { Table } from "../api/types";
import { useLang } from "../i18n/LangContext";

interface Props {
  freeTables: Table[];
  onClose: () => void;
  onSelect: (tableId: number) => void;
}

export function TransferTableModal({ freeTables, onClose, onSelect }: Props) {
  const { t } = useLang();

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h2>{t("transfer_table")}</h2>
        <p className="modifier-hint">{t("transfer_table_hint")}</p>

        {freeTables.length === 0 && <p className="cart-empty">{t("no_free_tables")}</p>}

        <div className="transfer-table-grid">
          {freeTables.map((table) => (
            <button key={table.id} className="transfer-table-tile" onClick={() => onSelect(table.id)}>
              {table.number}
            </button>
          ))}
        </div>

        <div className="modal-actions">
          <button className="btn btn-ghost" onClick={onClose}>
            {t("close")}
          </button>
        </div>
      </div>
    </div>
  );
}
