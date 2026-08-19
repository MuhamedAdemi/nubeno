import type { MenuItem } from "../api/types";
import { itemName } from "../api/types";
import { useLang } from "../i18n/LangContext";

interface Props {
  item: MenuItem;
  onAdd: () => void;
  onCustomize: () => void;
}

export function MenuItemCard({ item, onAdd, onCustomize }: Props) {
  const { lang, t } = useLang();
  return (
    <div className="menu-item-card">
      <button className="menu-item-main" onClick={onAdd}>
        <span className="menu-item-name">
          {itemName(item, lang)}
          {item.variant_label && <span className="menu-item-variant"> {item.variant_label}</span>}
        </span>
        <span className="menu-item-price">{Number(item.price).toFixed(2)} €</span>
      </button>
      {item.modifier_group && (
        <button className="menu-item-customize" onClick={onCustomize} title={t("customize")}>
          ⚙
        </button>
      )}
    </div>
  );
}
