import math
from typing import List, Tuple
from models.station import KnapsackItem
from models.results import KnapsackResult, KnapsackCellTrace

def knapsack_01_optimize(
    items: List[KnapsackItem],
    budget: int,
    max_cells: int = 200_000
) -> KnapsackResult:
    """
    0/1 Knapsack Dynamic Programming with 2D table and backtracking reconstruction.
    
    DAA Properties:
    - Pure bottom-up DP table: dp[i][w] = max(dp[i-1][w], dp[i-1][w - w_i] + v_i)
    - Strict tie-breaker: item taken only if take_value > skip_value.
      If values are equal, skip is chosen, which deterministically prefers fewer stations
      and saves capital budget.
    - Exact GCD scaling: computes g = gcd(w_1, ..., w_n, budget).
    - Conservative Adaptive Scaling (if budget/g > max_cells):
      Uses ceil(w_i / k) and floor(budget / k), mathematically guaranteeing that
      total reconstructed real cost <= budget.
    - Post-reconstruction assertion guarantees the budget invariant.
    
    Time Complexity: O(n * B') where B' is scaled budget (pseudo-polynomial)
    Space Complexity: O(n * B')
    """
    n = len(items)
    if n == 0 or budget <= 0:
        unselected = [(it, "Budget is zero or negative" if budget <= 0 else "No candidate items") for it in items]
        return KnapsackResult(
            selected_items=[],
            unselected_items=unselected,
            total_weight=0,
            total_value=0,
            remaining_budget=max(0, budget),
            scale_factor=1,
            scaled_budget=0,
            dp_table=[[0]],
            traces=[]
        )

    # 1. Compute scaling unit
    weights = [it.weight for it in items]
    g = budget
    for w in weights:
        g = math.gcd(g, w)
    
    if g > 0 and (budget // g) <= max_cells:
        k = g
        scaled_weights = [w // k for w in weights]
        scaled_budget = budget // k
    else:
        # Coarser scaling with ceil on weights and floor on budget
        k = max(1, math.ceil(budget / max_cells))
        scaled_weights = [math.ceil(w / k) for w in weights]
        scaled_budget = math.floor(budget / k)

    # 2. Allocate 2D DP Table: (n + 1) rows x (scaled_budget + 1) columns
    dp: List[List[int]] = [[0] * (scaled_budget + 1) for _ in range(n + 1)]
    traces: List[KnapsackCellTrace] = []

    # UI trace sampling step size to avoid memory bloat when recording cell traces
    sample_step = max(1, scaled_budget // 25)

    # 3. Bottom-Up Table Filling
    for i in range(1, n + 1):
        w_i = scaled_weights[i - 1]
        v_i = items[i - 1].value
        item_id = items[i - 1].station.id

        for w in range(scaled_budget + 1):
            skip_val = dp[i - 1][w]

            if w < w_i:
                dp[i][w] = skip_val
                decision = "SKIP"
                take_val = -1
            else:
                take_val = dp[i - 1][w - w_i] + v_i
                # Strict tie-breaker: prefer fewer stations and lower cost
                if take_val > skip_val:
                    dp[i][w] = take_val
                    decision = "TAKE"
                else:
                    dp[i][w] = skip_val
                    decision = "SKIP"

            # Sample key boundary and stride cells for UI visualization
            if w % sample_step == 0 or w == scaled_budget or w == w_i:
                traces.append(KnapsackCellTrace(
                    item_index=i,
                    item_id=item_id,
                    capacity_w=w,
                    take_value=take_val,
                    skip_value=skip_val,
                    decision=decision
                ))

    # 4. Optimal Backtracking Reconstruction
    selected_items: List[KnapsackItem] = []
    unselected_items: List[Tuple[KnapsackItem, str]] = []
    curr_w = scaled_budget

    for i in range(n, 0, -1):
        item = items[i - 1]
        w_i = scaled_weights[i - 1]

        # An item was taken iff cell value is strictly greater than cell directly above
        if dp[i][curr_w] > dp[i - 1][curr_w]:
            selected_items.append(item)
            curr_w -= w_i
        else:
            if curr_w < w_i:
                reason = f"Insufficient remaining budget (needs ₹{item.weight:,}, available ₹{curr_w * k:,})"
            else:
                reason = "Alternative station combination yields strictly higher total benefit"
            unselected_items.append((item, reason))

    selected_items.reverse()
    unselected_items.reverse()

    total_real_weight = sum(it.weight for it in selected_items)
    total_value = sum(it.value for it in selected_items)

    # Invariant safety assertion: real cost must never exceed real budget
    assert total_real_weight <= budget, (
        f"Knapsack safety assertion failed: Real weight {total_real_weight} > Budget {budget}"
    )

    return KnapsackResult(
        selected_items=selected_items,
        unselected_items=unselected_items,
        total_weight=total_real_weight,
        total_value=total_value,
        remaining_budget=budget - total_real_weight,
        scale_factor=k,
        scaled_budget=scaled_budget,
        dp_table=dp,
        traces=traces
    )

