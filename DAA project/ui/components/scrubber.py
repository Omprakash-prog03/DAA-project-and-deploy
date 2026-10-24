from nicegui import ui
from typing import Callable, Optional

class StepScrubber:
    """
    Interactive algorithm trace scrubber with Play/Pause, Step Back/Forward,
    Speed control, and current step slider.
    """
    def __init__(
        self,
        total_steps: int,
        on_step_change: Callable[[int], None],
        label_prefix: str = "Step"
    ):
        self.total_steps = max(1, total_steps)
        self.current_step = 1
        self.is_playing = False
        self.on_step_change = on_step_change
        self.label_prefix = label_prefix
        self.speed_ms = 800
        self.timer: Optional[ui.timer] = None

    def render(self):
        with ui.row().classes("w-full items-center justify-between glass-panel px-4 py-2.5 rounded-full border border-white/10 gap-3"):
            # Transport Controls
            with ui.row().classes("items-center gap-1.5"):
                ui.button(icon="first_page", on_click=self.go_to_start).props("round flat dense").classes("text-[#8B8F97] hover:text-white text-xs")
                ui.button(icon="chevron_left", on_click=self.step_back).props("round flat dense").classes("text-[#8B8F97] hover:text-white text-xs")
                
                self.play_btn = ui.button(
                    icon="play_arrow",
                    on_click=self.toggle_play
                ).props("round dense").classes("bg-[#3DDC84] text-[#0B0C0E] hover:opacity-90 w-8 h-8")
                
                ui.button(icon="chevron_right", on_click=self.step_forward).props("round flat dense").classes("text-[#8B8F97] hover:text-white text-xs")
                ui.button(icon="last_page", on_click=self.go_to_end).props("round flat dense").classes("text-[#8B8F97] hover:text-white text-xs")

            # Slider and Step Label
            with ui.row().classes("flex-1 items-center gap-3"):
                self.slider = ui.slider(
                    min=1,
                    max=self.total_steps,
                    value=self.current_step,
                    on_change=lambda e: self.set_step(int(e.value))
                ).props("dense dark color=positive").classes("flex-1")
                
                self.step_label = ui.label(
                    f"{self.current_step} / {self.total_steps}"
                ).classes("text-xs font-mono tabular-nums text-[#8B8F97] min-w-[55px] text-right")

            # Speed Chip
            with ui.row().classes("items-center gap-1"):
                ui.label("Speed:").classes("text-[10px] text-[#5A5E66]")
                self.speed_select = ui.select(
                    options={1200: "0.5x", 800: "1.0x", 400: "2.0x"},
                    value=self.speed_ms,
                    on_change=lambda e: self.change_speed(int(e.value))
                ).props("dense borderless dark options-dense").classes("text-[11px] text-[#ECEDEF] w-14")

        # Background timer for play animation
        self.timer = ui.timer(self.speed_ms / 1000.0, self._tick, active=False)

    def _tick(self):
        if not self.is_playing:
            return
        if self.current_step < self.total_steps:
            self.set_step(self.current_step + 1)
        else:
            self.toggle_play()

    def toggle_play(self):
        self.is_playing = not self.is_playing
        self.play_btn.props(f"icon={'pause' if self.is_playing else 'play_arrow'}")
        if self.timer:
            self.timer.active = self.is_playing

    def step_forward(self):
        if self.current_step < self.total_steps:
            self.set_step(self.current_step + 1)

    def step_back(self):
        if self.current_step > 1:
            self.set_step(self.current_step - 1)

    def go_to_start(self):
        self.set_step(1)

    def go_to_end(self):
        self.set_step(self.total_steps)

    def set_step(self, step: int):
        self.current_step = max(1, min(self.total_steps, step))
        if hasattr(self, 'slider'):
            self.slider.value = self.current_step
        if hasattr(self, 'step_label'):
            self.step_label.text = f"{self.current_step} / {self.total_steps}"
        self.on_step_change(self.current_step)

    def change_speed(self, ms: int):
        self.speed_ms = ms
        if self.timer:
            self.timer.interval = ms / 1000.0
