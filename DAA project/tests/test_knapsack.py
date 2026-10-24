import pytest
import random
from models.station import Station, KnapsackItem
from algorithms.knapsack import knapsack_01_optimize
from algorithms.baselines import brute_force_knapsack, greedy_knapsack

def _make_dummy_item(id_num: int, weight: int, value: int) -> KnapsackItem:
    st = Station(
        id=f"CS-{id_num:02d}",
        name=f"Station {id_num}",
        location_id=f"LOC-{id_num:02d}",
        installation_cost=weight,
        expected_coverage=value // 10,
        capacity_kw=100,
        priority=2,
        demand_score=5.0
    )
    return KnapsackItem(station=st, weight=weight, value=value, feeder_km=0.0, feeder_cost=0)

def test_knapsack_budget_zero_and_negative():
    items = [_make_dummy_item(1, 10000, 50)]
    res_zero = knapsack_01_optimize(items, budget=0)
    assert len(res_zero.selected_items) == 0
    assert res_zero.total_weight == 0
    assert res_zero.total_value == 0
    assert res_zero.remaining_budget == 0

    res_neg = knapsack_01_optimize(items, budget=-500)
    assert len(res_neg.selected_items) == 0

def test_knapsack_budget_below_every_item():
    items = [
        _make_dummy_item(1, 50000, 30),
        _make_dummy_item(2, 80000, 60),
    ]
    res = knapsack_01_optimize(items, budget=20000)
    assert len(res.selected_items) == 0
    assert res.remaining_budget == 20000
    assert len(res.unselected_items) == 2
    for _, reason in res.unselected_items:
        assert "Insufficient remaining budget" in reason

def test_knapsack_budget_exactly_equal_to_one_item():
    items = [
        _make_dummy_item(1, 50000, 30),
        _make_dummy_item(2, 100000, 70),
    ]
    res = knapsack_01_optimize(items, budget=50000)
    assert len(res.selected_items) == 1
    assert res.selected_items[0].station.id == "CS-01"
    assert res.total_weight == 50000
    assert res.remaining_budget == 0
    assert res.total_value == 30

def test_knapsack_strict_tie_breaking():
    # Two items: same value, but Item 2 has zero benefit over Item 1
    # Items: (weight=10, val=20), (weight=10, val=0)
    # If budget=20, it should not pick the zero-value item if strictly greater rule applies
    items = [
        _make_dummy_item(1, 10, 50),
        _make_dummy_item(2, 10, 0),
    ]
    res = knapsack_01_optimize(items, budget=20)
    # Item 1 taken, Item 2 provides no extra value -> skipped
    assert len(res.selected_items) == 1
    assert res.selected_items[0].station.id == "CS-01"
    assert res.total_weight == 10

def test_knapsack_rupee_budget_safety_under_coarse_scaling():
    # High rupee budget triggering adaptive scaling: B = 10,000,000 with max_cells = 1000
    items = [
        _make_dummy_item(1, 1_234_567, 100),
        _make_dummy_item(2, 2_345_678, 210),
        _make_dummy_item(3, 3_456_789, 320),
        _make_dummy_item(4, 4_567_890, 430),
        _make_dummy_item(5, 5_678_901, 540),
    ]
    budget = 10_000_000
    res = knapsack_01_optimize(items, budget=budget, max_cells=1000)
    
    # Real weight must NEVER exceed real budget
    assert res.total_weight <= budget
    assert res.remaining_budget == budget - res.total_weight
    assert res.scale_factor > 1

def test_knapsack_vs_brute_force_cross_check():
    """Ground truth cross check comparing DP vs 2^n exhaustive power set search."""
    rng = random.Random(999)
    for _ in range(5):
        n = rng.randint(6, 10)
        items = []
        for i in range(1, n + 1):
            wt = rng.randint(10, 100) * 1000
            val = rng.randint(15, 80)
            items.append(_make_dummy_item(i, wt, val))
        
        budget = rng.randint(150, 400) * 1000
        
        dp_res = knapsack_01_optimize(items, budget=budget)
        bf_val, bf_subset = brute_force_knapsack(items, budget=budget)

        assert dp_res.total_value == bf_val
        assert dp_res.total_weight <= budget

def test_knapsack_dp_beats_or_equals_greedy():
    """
    Classic DAA demonstration: 0/1 Knapsack DP is mathematically optimal,
    whereas Greedy heuristic can fail to find the global optimum.
    Example: Budget = 100.
      Item 1: Weight 60, Value 60 (ratio 1.0)
      Item 2: Weight 50, Value 45 (ratio 0.9)
      Item 3: Weight 50, Value 45 (ratio 0.9)
    Greedy takes Item 1 (60), remaining capacity 40 cannot fit either Item 2 or 3 -> Total Value = 60.
    DP takes Item 2 + Item 3 (Weight 100) -> Total Value = 90.
    """
    items = [
        _make_dummy_item(1, 60, 60),
        _make_dummy_item(2, 50, 45),
        _make_dummy_item(3, 50, 45),
    ]
    budget = 100
    dp_res = knapsack_01_optimize(items, budget=budget)
    greedy_val, greedy_w, greedy_sel = greedy_knapsack(items, budget=budget)

    assert dp_res.total_value == 90
    assert greedy_val == 60
    assert dp_res.total_value > greedy_val

