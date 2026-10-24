import math
from typing import List, Dict, Any, Tuple
from backend.models.station import CandidateStation
from backend.models.optimization import KnapsackResponse

def run_01_knapsack(
    candidates: List[CandidateStation],
    budget: int,
    max_cells: int = 200_000
) -> KnapsackResponse:
    """
    Hand-written 0/1 Knapsack Dynamic Programming with 2D table and backtracking.
    Selects optimal candidate EV charging stations under a user-defined installation budget.
    
    DAA Academic Specifications:
    - Input: Candidate set with user-entered installation costs and benefit values; budget limit B.
    - Recurrence: dp[i][w] = max(dp[i-1][w], dp[i-1][w - w_i] + v_i)
    - Tie-Breaking: Strict inequality (take_val > skip_val). On ties, skip is chosen,
      minimizing capital expenditure and station count.
    - Cost-Unit Scaling: Uses exact GCD or conservative ceil/floor scaling, mathematically
      guaranteeing total real cost <= budget.
    - Time Complexity: O(n * B') where B' is scaled budget (pseudo-polynomial).
    - Space Complexity: O(n * B') for 2D table to enable backtracking reconstruction.
    """
    n = len(candidates)
    if n == 0 or budget <= 0:
        rejected = [
            {"station": c.model_dump(), "reason": "Budget is zero or negative" if budget <= 0 else "No candidate stations"}
            for c in candidates
        ]
        return KnapsackResponse(
            selected_stations=[],
            rejected_stations=rejected,
            total_installation_cost=0,
            total_value_benefit=0,
            remaining_budget=max(0, budget),
            budget_utilization_pct=0.0,
            algorithm_info={
                "algorithm": "0/1 Knapsack DP (Hand-written Python)",
                "status": "Empty candidate set or zero budget",
                "time_complexity": "O(n * B')",
                "space_complexity": "O(n * B')"
            }
        )

    # Effective weight includes base install cost + feeder line connection cost from MST
    weights = [c.installation_cost + c.feeder_connection_cost for c in candidates]
    values = [c.expected_value for c in candidates]

    # Compute scaling unit (GCD)
    g = budget
    for w in weights:
        g = math.gcd(g, w)

    if g > 0 and (budget // g) <= max_cells:
        k = g
        scaled_weights = [w // k for w in weights]
        scaled_budget = budget // k
    else:
        # Conservative adaptive scaling
        k = max(1, math.ceil(budget / max_cells))
        scaled_weights = [math.ceil(w / k) for w in weights]
        scaled_budget = math.floor(budget / k)

    # 2D DP Table: (n + 1) rows x (scaled_budget + 1) cols
    dp: List[List[int]] = [[0] * (scaled_budget + 1) for _ in range(n + 1)]

    # Bottom-Up Dynamic Programming Matrix Filling
    for i in range(1, n + 1):
        w_i = scaled_weights[i - 1]
        v_i = values[i - 1]

        for w in range(scaled_budget + 1):
            skip_val = dp[i - 1][w]
            if w < w_i:
                dp[i][w] = skip_val
            else:
                take_val = dp[i - 1][w - w_i] + v_i
                if take_val > skip_val:  # Strict inequality tie-breaker
                    dp[i][w] = take_val
                else:
                    dp[i][w] = skip_val

    # Optimal Backtracking Reconstruction
    selected_stations: List[CandidateStation] = []
    rejected_stations: List[Dict[str, Any]] = []
    curr_w = scaled_budget

    for i in range(n, 0, -1):
        cand = candidates[i - 1]
        w_i = scaled_weights[i - 1]
        real_cost = weights[i - 1]

        if dp[i][curr_w] > dp[i - 1][curr_w]:
            selected_stations.append(cand)
            curr_w -= w_i
        else:
            if curr_w < w_i:
                reason = f"Installation cost (₹{real_cost:,}) exceeds remaining budget (₹{curr_w * k:,})"
            else:
                reason = "Alternative candidate combination provides strictly higher public benefit"
            rejected_stations.append({
                "station": cand.model_dump(),
                "reason": reason
            })

    selected_stations.reverse()
    rejected_stations.reverse()

    total_real_cost = sum(c.installation_cost + c.feeder_connection_cost for c in selected_stations)
    total_value = sum(c.expected_value for c in selected_stations)

    # Provable budget safety assertion
    assert total_real_cost <= budget, (
        f"Knapsack budget violation: Real cost {total_real_cost} > Budget {budget}"
    )

    utilization = round((total_real_cost / budget) * 100.0, 1) if budget > 0 else 0.0

    return KnapsackResponse(
        selected_stations=selected_stations,
        rejected_stations=rejected_stations,
        total_installation_cost=total_real_cost,
        total_value_benefit=total_value,
        remaining_budget=budget - total_real_cost,
        budget_utilization_pct=utilization,
        algorithm_info={
            "algorithm": "0/1 Knapsack Dynamic Programming (Hand-written Python)",
            "table_dimensions": f"{n + 1} items × {scaled_budget + 1} scaled capacity",
            "scale_factor_inr": k,
            "pseudo_polynomial_bound": "O(n * B')",
            "space_complexity": "O(n * B')",
            "viva_stretch": "Provably optimal integer allocation under budget constraint"
        }
    )

