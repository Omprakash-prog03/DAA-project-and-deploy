from nicegui import ui
from ui.state import state
from ui.components.glass_card import glass_card, card_header
from models.station import Station

def render_station_planning():
    res = state.result

    with ui.column().classes("w-full p-6 max-h-[calc(100vh-80px)] overflow-y-auto gap-5"):
        # Header strip
        with ui.row().classes("w-full items-center justify-between"):
            with ui.column().classes("gap-1"):
                ui.label("Station Candidate Planning").classes("page-hero-title")
                ui.label("Edit proposal parameters and observe dynamic knapsack weight/value shifts.").classes(
                    "text-xs text-[#8B8F97]"
                )
            
            ui.button("Recalculate Knapsack", on_click=lambda: state.recalculate(), icon="bolt").props(
                "rounded outline"
            ).classes("text-xs text-[#3DDC84] border-[#3DDC84]/30 hover:bg-[#3DDC84]/10")

        # Table of Candidates with live inputs
        with glass_card(padding="p-5", extra_classes="w-full"):
            card_header(
                "Candidate Proposals & Formulation Ledger",
                f"{len(state.candidates)} proposals under review",
                badge_text="Knapsack Input",
                badge_color="#3DDC84"
            )

            with ui.column().classes("w-full overflow-x-auto"):
                with ui.row().classes("w-full text-[11px] uppercase tracking-wider text-[#5A5E66] font-medium py-2 px-3 border-b border-white/5 gap-3"):
                    ui.label("ID").classes("w-16")
                    ui.label("Name").classes("w-44")
                    ui.label("Host Location").classes("w-32")
                    ui.label("Install Cost (₹)").classes("w-32")
                    ui.label("Survey Cov").classes("w-24")
                    ui.label("Cap (kW)").classes("w-24")
                    ui.label("Priority").classes("w-20")
                    ui.label("Demand").classes("w-20")
                    ui.label("Status").classes("flex-1 text-right")

                for i, st in enumerate(state.candidates):
                    # Check if selected
                    is_sel = any(it.station.id == st.id for it in res.knapsack_result.selected_items)
                    status_badge = "SELECTED" if is_sel else "EXCLUDED"
                    status_color = "#3DDC84" if is_sel else "#5A5E66"

                    with ui.row().classes("w-full items-center py-2 px-3 text-xs border-b border-white/[0.03] hover:bg-white/[0.02] gap-3"):
                        ui.label(st.id).classes("w-16 font-mono font-bold text-white")
                        ui.label(st.name).classes("w-44 text-[#ECEDEF] truncate")
                        
                        # Location lookup
                        loc_name = state.graph.locations.get(st.location_id, None)
                        loc_str = loc_name.name if loc_name else st.location_id
                        ui.label(loc_str).classes("w-32 text-[#8B8F97] truncate")

                        # Editable cost
                        cost_inp = ui.number(
                            value=st.installation_cost,
                            step=5000,
                            min=10000
                        ).props("dense dark outlined").classes("w-32 text-xs")

                        # Editable survey coverage
                        cov_inp = ui.number(
                            value=st.expected_coverage,
                            step=1,
                            min=1,
                            max=10
                        ).props("dense dark outlined").classes("w-24 text-xs")

                        # Editable capacity
                        cap_inp = ui.number(
                            value=st.capacity_kw,
                            step=10,
                            min=50
                        ).props("dense dark outlined").classes("w-24 text-xs")

                        # Priority
                        prio_inp = ui.select(
                            options={1: "P1", 2: "P2", 3: "P3"},
                            value=st.priority
                        ).props("dense dark outlined options-dense").classes("w-20 text-xs")

                        # Demand
                        dem_inp = ui.number(
                            value=st.demand_score,
                            step=0.5,
                            min=1.0,
                            max=10.0
                        ).props("dense dark outlined").classes("w-20 text-xs")

                        # Update handler
                        def make_updater(idx=i, c=cost_inp, cv=cov_inp, cp=cap_inp, pr=prio_inp, dm=dem_inp):
                            def update(_):
                                old_st = state.candidates[idx]
                                state.candidates[idx] = Station(
                                    id=old_st.id,
                                    name=old_st.name,
                                    location_id=old_st.location_id,
                                    installation_cost=int(c.value),
                                    expected_coverage=int(cv.value),
                                    capacity_kw=int(cp.value),
                                    priority=int(pr.value),
                                    demand_score=float(dm.value)
                                )
                                state.recalculate()
                            return update

                        updater = make_updater()
                        cost_inp.on_value_change(updater)
                        cov_inp.on_value_change(updater)
                        cap_inp.on_value_change(updater)
                        prio_inp.on_value_change(updater)
                        dem_inp.on_value_change(updater)

                        with ui.row().classes("flex-1 justify-end"):
                            ui.label(status_badge).classes(
                                f"text-[10px] font-bold px-2 py-0.5 rounded-full"
                            ).style(f"background: {status_color}22; color: {status_color}; border: 1px solid {status_color}44;")
