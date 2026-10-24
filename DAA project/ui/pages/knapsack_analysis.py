from nicegui import ui
from ui.state import state
from ui.components.glass_card import glass_card, card_header
from ui.components.scrubber import StepScrubber

def render_knapsack_analysis():
    knap_res = state.result.knapsack_result
    dp_table = knap_res.dp_table
    traces = knap_res.traces
    total_steps = max(1, len(traces))

    with ui.column().classes("w-[440px] p-5 gap-4 overflow-y-auto max-h-[calc(100vh-80px)]"):
        # Summary Card
        with glass_card(padding="p-4"):
            card_header("0/1 Knapsack Formulation", f"Scale Factor: 1 unit = ₹{knap_res.scale_factor:,}", badge_text="O(n • B') Pseudo-P", badge_color="#3DDC84")
            
            with ui.row().classes("w-full items-baseline justify-between my-2"):
                with ui.column():
                    ui.label("Optimal Benefit").classes("text-[10px] text-[#5A5E66] uppercase")
                    ui.label(f"{knap_res.total_value} pts").classes("text-3xl font-light text-[#3DDC84] font-mono tabular-nums")
                
                with ui.column().classes("items-end"):
                    ui.label("Capital Utilized").classes("text-[10px] text-[#5A5E66] uppercase")
                    ui.label(f"₹{knap_res.total_weight:,}").classes("text-sm font-mono text-white font-medium")

            ui.label(f"Surplus Budget: ₹{knap_res.remaining_budget:,} (Scaled Capacity: {knap_res.scaled_budget})").classes(
                "text-xs text-[#8B8F97] font-medium"
            )

        # Selected & Excluded Station Dossier
        with glass_card(padding="p-4"):
            card_header("Selection Decisions & Viva Rationale")
            
            with ui.column().classes("w-full max-h-[380px] overflow-y-auto pr-1 gap-2 mt-2"):
                # Selected
                ui.label("SELECTED IN OPTIMAL PLAN").classes("text-[10px] uppercase font-bold text-[#3DDC84] tracking-wider")
                for it in knap_res.selected_items:
                    with ui.row().classes("w-full items-center justify-between p-2 rounded bg-[#3DDC84]/5 border border-[#3DDC84]/20 text-xs"):
                        with ui.column().classes("gap-0.5"):
                            ui.label(f"{it.station.id} — {it.station.name}").classes("font-medium text-white")
                            ui.label(f"Net Cost: ₹{it.weight:,} (Feeder: ₹{it.feeder_cost:,})").classes("text-[10px] text-[#8B8F97]")
                        ui.label(f"+{it.value} pts").classes("font-mono text-[#3DDC84] font-bold")

                # Unselected
                ui.label("EXCLUDED PROPOSALS").classes("text-[10px] uppercase font-bold text-[#FF4D4F] tracking-wider mt-2")
                for it, reason in knap_res.unselected_items:
                    with ui.column().classes("w-full p-2 rounded bg-white/[0.02] border border-white/5 text-xs gap-0.5"):
                        with ui.row().classes("w-full items-center justify-between"):
                            ui.label(f"{it.station.id} — {it.station.name}").classes("font-medium text-[#ECEDEF]")
                            ui.label(f"₹{it.weight:,}").classes("font-mono text-[#8B8F97]")
                        ui.label(f"Reason: {reason}").classes("text-[10px] text-[#8B8F97] italic")

    # Right DP Matrix & Trace Scrubber
    with ui.column().classes("flex-1 p-5 max-h-[calc(100vh-80px)] overflow-y-auto"):
        with ui.row().classes("w-full items-center justify-between mb-2"):
            with ui.column().classes("gap-0.5"):
                ui.label("Dynamic Programming Table & Backtracking").classes("page-hero-title")
                ui.label("Bottom-up recurrence dp[i][w] = max(dp[i-1][w], dp[i-1][w-w_i] + v_i)").classes("text-xs text-[#8B8F97]")

        matrix_box = glass_card(padding="p-4", extra_classes="w-full")

        def update_knapsack_view(step_idx: int):
            matrix_box.clear()
            active_trace = traces[step_idx - 1] if 1 <= step_idx <= len(traces) else None

            with matrix_box:
                if active_trace:
                    with ui.row().classes("w-full items-center justify-between mb-3 pb-2 border-b border-white/5"):
                        ui.label(f"Cell Calculation: Item {active_trace.item_id} @ Scaled Capacity {active_trace.capacity_w}").classes(
                            "text-xs font-mono font-medium text-white"
                        )
                        decision_color = "#3DDC84" if active_trace.decision == "TAKE" else "#5A5E66"
                        ui.label(f"Decision: {active_trace.decision} (Take: {active_trace.take_value} vs Skip: {active_trace.skip_value})").classes(
                            "text-xs font-mono font-bold px-2 py-0.5 rounded"
                        ).style(f"background: {decision_color}22; color: {decision_color};")

                # Render compact DP heatmap table
                # Sample cols if scaled_budget is large
                num_rows = len(dp_table)
                num_cols = len(dp_table[0]) if num_rows > 0 else 0
                stride = max(1, num_cols // 14)
                sampled_cols = list(range(0, num_cols, stride))
                if (num_cols - 1) not in sampled_cols:
                    sampled_cols.append(num_cols - 1)

                with ui.column().classes("w-full overflow-x-auto"):
                    # Header row (scaled capacities)
                    with ui.row().classes("gap-1 text-[10px] font-mono text-[#5A5E66] border-b border-white/5 pb-1"):
                        ui.label("Station \\ Cap").classes("w-20")
                        for c in sampled_cols:
                            ui.label(f"w={c}").classes("w-12 text-center")

                    # Rows
                    for r_idx in range(1, num_rows):
                        st_id = traces[0].item_id if traces else f"S{r_idx}"
                        # Look up item id
                        if r_idx - 1 < len(knap_res.selected_items) + len(knap_res.unselected_items):
                            # combine all items
                            all_items = knap_res.selected_items + [u[0] for u in knap_res.unselected_items]
                            all_items_sorted = sorted(all_items, key=lambda it: it.station.id)
                            st_id = all_items_sorted[r_idx - 1].station.id if r_idx - 1 < len(all_items_sorted) else f"S{r_idx}"

                        with ui.row().classes("gap-1 items-center py-1 border-b border-white/[0.02] text-xs font-mono"):
                            ui.label(st_id).classes("w-20 text-[#ECEDEF] font-bold")
                            for c in sampled_cols:
                                val = dp_table[r_idx][c]
                                is_active_cell = (active_trace and active_trace.item_index == r_idx and active_trace.capacity_w == c)
                                cell_bg = "bg-[#3DDC84]/25 text-[#3DDC84] border border-[#3DDC84]" if is_active_cell else "bg-white/[0.02] text-[#8B8F97]"
                                ui.label(str(val)).classes(f"w-12 text-center py-1 rounded {cell_bg} text-[11px]")

        scrubber = StepScrubber(
            total_steps=total_steps,
            on_step_change=update_knapsack_view,
            label_prefix="Cell"
        )
        
        with ui.row().classes("w-full mt-3"):
            scrubber.render()

        update_knapsack_view(total_steps)
