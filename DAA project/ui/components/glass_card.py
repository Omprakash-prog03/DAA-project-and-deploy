from nicegui import ui
from typing import Optional

def glass_card(
    extra_classes: str = "",
    padding: str = "p-5",
    hover_effect: bool = False
) -> ui.element:
    """Creates a stylized glassmorphic card container."""
    hover_cls = "glass-card-hover" if hover_effect else ""
    return ui.column().classes(
        f"glass-panel {padding} {hover_cls} rounded-[24px] border border-white/5 {extra_classes}"
    )

def card_header(title: str, subtitle: Optional[str] = None, badge_text: Optional[str] = None, badge_color: str = "#3DDC84"):
    with ui.row().classes("w-full items-center justify-between mb-2"):
        with ui.column().classes("gap-0"):
            ui.label(title).classes("text-sm font-medium tracking-tight text-[#ECEDEF]")
            if subtitle:
                ui.label(subtitle).classes("text-[11px] text-[#8B8F97] tracking-normal")
        if badge_text:
            ui.label(badge_text).classes(
                "text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full"
            ).style(f"background: {badge_color}22; color: {badge_color}; border: 1px solid {badge_color}44;")
