from nicegui import ui
from ui.components.glass_card import glass_card, card_header

def render_about_algorithms():
    with ui.column().classes("w-full p-6 max-h-[calc(100vh-80px)] overflow-y-auto gap-6"):
        # Header
        with ui.column().classes("gap-1"):
            ui.label("Algorithmic Foundations & Viva Defense Guide").classes("page-hero-title")
            ui.label("Theoretical specifications, proof invariants, and complexity bounds for the examination panel.").classes(
                "text-xs text-[#8B8F97]"
            )

        # Cooperating Triad Banner
        with glass_card(padding="p-5", extra_classes="w-full bg-[#3DDC84]/5 border-[#3DDC84]/20"):
            card_header("THE THREE COOPERATING ALGORITHMS", "How MST, Knapsack and Dijkstra Form One Dependent Pipeline", badge_text="Core Architecture", badge_color="#3DDC84")
            ui.label(
                "1. KRUSKAL (Grid Backbone): Computes the minimum-length acyclic power feeder backbone across the road graph, "
                "establishing the high-voltage transmission lines.\n"
                "2. KNAPSACK (Capital Allocation): Consumes the shortest incident MST edge to calculate feeder connection costs for each station. "
                "Maximizes public benefit under a strict budget constraint using 2D Dynamic Programming.\n"
                "3. DIJKSTRA (Physical Access & True Coverage): Runs multi-source search on the full road network from all selected stations to measure "
                "actual shortest paths and resolve real topological coverage overlap."
            ).classes("text-xs text-[#ECEDEF] leading-relaxed whitespace-pre-line")

        # Complexity Table Card
        with glass_card(padding="p-5", extra_classes="w-full"):
            card_header("Honest Complexity Specifications", "Asymptotic Bounds for Actual Implementations", badge_text="DAA Rigor", badge_color="#3DDC84")
            
            with ui.column().classes("w-full overflow-x-auto"):
                with ui.row().classes("w-full text-[11px] uppercase tracking-wider text-[#5A5E66] font-medium py-2 px-3 border-b border-white/5"):
                    ui.label("Algorithm").classes("w-40")
                    ui.label("Category").classes("w-32")
                    ui.label("Time Complexity").classes("w-44")
                    ui.label("Space Complexity").classes("w-40")
                    ui.label("Key Invariant / Mechanism").classes("flex-1")

                rows = [
                    ("Kruskal's MST", "Greedy / DSU", "O(E log V) = O(E log E)", "O(V + E)", "Union-Find by rank & path compression, acyclic minimal cut"),
                    ("Dijkstra's Search", "Greedy / Heap", "O((V + E) log V)", "O(V + E)", "Binary min-heap lazy deletion, triangle inequality relaxation"),
                    ("0/1 Knapsack", "Dynamic Prog", "O(n • B') [Pseudo-Poly]", "O(n • B')", "Bellman optimality, GCD scaling, backtrack reconstruction"),
                ]
                for alg, cat, tc, sc, inv in rows:
                    with ui.row().classes("w-full items-center py-2.5 px-3 text-xs border-b border-white/[0.03]"):
                        ui.label(alg).classes("w-40 font-bold text-white")
                        ui.label(cat).classes("w-32 text-[#8B8F97]")
                        ui.label(tc).classes("w-44 font-mono text-[#3DDC84]")
                        ui.label(sc).classes("w-40 font-mono text-[#ECEDEF]")
                        ui.label(inv).classes("flex-1 text-[11px] text-[#8B8F97]")

        # Detailed Algorithm Deep Dive Cards (3 Columns)
        with ui.grid().classes("w-full grid-cols-1 md:grid-cols-3 gap-5"):
            # Kruskal Card
            with glass_card(padding="p-5"):
                card_header("1. Kruskal's MST", "Minimum Spanning Forest", badge_text="Greedy", badge_color="#3DDC84")
                with ui.column().classes("gap-2 text-xs text-[#8B8F97] mt-2"):
                    ui.label("Purpose:").classes("font-bold text-white")
                    ui.label("Build minimal-cost power feeder backbone.")
                    ui.label("Data Structures:").classes("font-bold text-white mt-1")
                    ui.label("Disjoint Set Union (DSU) with rank and two-pass path compression.")
                    ui.label("Tie-Breaking:").classes("font-bold text-white mt-1")
                    ui.label("Deterministic sorting by (weight, min_node_id, max_node_id).")
                    ui.label("Viva Point:").classes("font-bold text-[#3DDC84] mt-1")
                    ui.label("Handles disconnected graphs cleanly as a Minimum Spanning Forest (MSF) with V - C edges.")

            # Dijkstra Card
            with glass_card(padding="p-5"):
                card_header("2. Dijkstra's Algorithm", "Single & Multi-Source", badge_text="Priority Queue", badge_color="#3DDC84")
                with ui.column().classes("gap-2 text-xs text-[#8B8F97] mt-2"):
                    ui.label("Purpose:").classes("font-bold text-white")
                    ui.label("Compute exact shortest road routes and true multi-source coverage.")
                    ui.label("Data Structures:").classes("font-bold text-white mt-1")
                    ui.label("Binary Min-Heap storing (distance, node_id) with lazy stale deletion.")
                    ui.label("Tie-Breaking:").classes("font-bold text-white mt-1")
                    ui.label("Lexicographical node ID comparison on equal distances.")
                    ui.label("Viva Point:").classes("font-bold text-[#3DDC84] mt-1")
                    ui.label("Multi-source Dijkstra initializes all selected stations at d=0 in one single O((V+E)logV) run.")

            # Knapsack Card
            with glass_card(padding="p-5"):
                card_header("3. 0/1 Knapsack DP", "Budget Optimization", badge_text="Dynamic Prog", badge_color="#3DDC84")
                with ui.column().classes("gap-2 text-xs text-[#8B8F97] mt-2"):
                    ui.label("Purpose:").classes("font-bold text-white")
                    ui.label("Select candidate stations to maximize benefit under budget.")
                    ui.label("Table Dimension:").classes("font-bold text-white mt-1")
                    ui.label("(N + 1) rows × (Scaled Budget + 1) columns.")
                    ui.label("Tie-Breaking:").classes("font-bold text-white mt-1")
                    ui.label("Strict inequality take_val > skip_val (prefers fewer stations on ties).")
                    ui.label("Viva Point:").classes("font-bold text-[#3DDC84] mt-1")
                    ui.label("Rupee scaling uses exact GCD or conservative ceil/floor, provably preventing budget overrun.")
