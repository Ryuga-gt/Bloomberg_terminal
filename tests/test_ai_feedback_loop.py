"""
RED tests for ai.feedback_loop.StrategyResearchLoop contract.

Contract:
  - Class StrategyResearchLoop
  - Method run(prompt: str, candles: list[dict], iterations: int) -> dict
  - Returns:
        best_strategy_class  — class with highest fitness_score
        best_metrics         — metrics dict for best strategy
        best_prompt          — prompt that generated the best strategy
        history              — list of per-iteration records
"""

from ai.feedback_loop import StrategyResearchLoop

# ---------------------------------------------------------------------------
# Candle fixtures
# ---------------------------------------------------------------------------

CANDLES_RISING = [
    {"timestamp": "2024-01-01", "open": 99.0,  "high": 101.0, "low": 98.0,  "close": 100.0, "volume": 1_000_000},
    {"timestamp": "2024-01-02", "open": 100.5, "high": 111.0, "low": 100.0, "close": 110.0, "volume": 1_200_000},
    {"timestamp": "2024-01-03", "open": 105.0, "high": 121.0, "low": 104.5, "close": 120.0, "volume": 1_300_000},
    {"timestamp": "2024-01-04", "open": 115.0, "high": 131.0, "low": 114.5, "close": 130.0, "volume": 1_400_000},
]

CANDLES_FLAT = [
    {"timestamp": "2024-01-01", "open": 99.0, "high": 101.0, "low": 98.0, "close": 100.0, "volume": 1_000_000},
    {"timestamp": "2024-01-02", "open": 99.0, "high": 101.0, "low": 98.0, "close": 100.0, "volume": 1_000_000},
    {"timestamp": "2024-01-03", "open": 99.0, "high": 101.0, "low": 98.0, "close": 100.0, "volume": 1_000_000},
]


# ---------------------------------------------------------------------------
# Instantiation
# ---------------------------------------------------------------------------

def test_strategy_research_loop_is_instantiable():
    loop = StrategyResearchLoop()
    assert loop is not None


# ---------------------------------------------------------------------------
# run() returns a dict
# ---------------------------------------------------------------------------

def test_run_returns_dict():
    loop = StrategyResearchLoop()
    result = loop.run("momentum", CANDLES_RISING, iterations=1)
    assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# Required keys in the returned dict
# ---------------------------------------------------------------------------

def test_run_result_has_best_strategy_class():
    loop = StrategyResearchLoop()
    result = loop.run("momentum", CANDLES_RISING, iterations=1)
    assert "best_strategy_class" in result


def test_run_result_has_best_metrics():
    loop = StrategyResearchLoop()
    result = loop.run("momentum", CANDLES_RISING, iterations=1)
    assert "best_metrics" in result


def test_run_result_has_best_prompt():
    loop = StrategyResearchLoop()
    result = loop.run("momentum", CANDLES_RISING, iterations=1)
    assert "best_prompt" in result


def test_run_result_has_history():
    loop = StrategyResearchLoop()
    result = loop.run("momentum", CANDLES_RISING, iterations=1)
    assert "history" in result


# ---------------------------------------------------------------------------
# best_strategy_class must be a type
# ---------------------------------------------------------------------------

def test_best_strategy_class_is_a_type():
    loop = StrategyResearchLoop()
    result = loop.run("aggressive", CANDLES_RISING, iterations=1)
    assert isinstance(result["best_strategy_class"], type)


# ---------------------------------------------------------------------------
# best_metrics must contain required keys
# ---------------------------------------------------------------------------

def test_best_metrics_has_required_keys():
    loop = StrategyResearchLoop()
    result = loop.run("trend", CANDLES_RISING, iterations=1)
    metrics = result["best_metrics"]
    for key in ("final_equity", "sharpe_ratio", "calmar_ratio", "fitness_score"):
        assert key in metrics, f"best_metrics missing key '{key}'"


# ---------------------------------------------------------------------------
# history length equals iterations
# ---------------------------------------------------------------------------

def test_history_length_equals_iterations_1():
    loop = StrategyResearchLoop()
    result = loop.run("momentum", CANDLES_RISING, iterations=1)
    assert len(result["history"]) == 1


def test_history_length_equals_iterations_3():
    loop = StrategyResearchLoop()
    result = loop.run("momentum", CANDLES_RISING, iterations=3)
    assert len(result["history"]) == 3


def test_history_length_equals_iterations_5():
    loop = StrategyResearchLoop()
    result = loop.run("any prompt", CANDLES_RISING, iterations=5)
    assert len(result["history"]) == 5


# ---------------------------------------------------------------------------
# Each history record has the required fields
# ---------------------------------------------------------------------------

def test_history_records_have_required_fields():
    loop = StrategyResearchLoop()
    result = loop.run("trend", CANDLES_RISING, iterations=3)
    for record in result["history"]:
        assert "iteration" in record
        assert "prompt" in record
        assert "strategy_class" in record
        assert "metrics" in record


def test_history_iteration_indices_are_sequential():
    loop = StrategyResearchLoop()
    result = loop.run("momentum", CANDLES_RISING, iterations=4)
    indices = [r["iteration"] for r in result["history"]]
    assert indices == list(range(4))


def test_history_each_strategy_class_is_a_type():
    loop = StrategyResearchLoop()
    result = loop.run("trend", CANDLES_RISING, iterations=3)
    for record in result["history"]:
        assert isinstance(record["strategy_class"], type)


def test_history_each_metrics_has_fitness_score():
    loop = StrategyResearchLoop()
    result = loop.run("momentum", CANDLES_RISING, iterations=3)
    for record in result["history"]:
        assert "fitness_score" in record["metrics"]


# ---------------------------------------------------------------------------
# best_strategy_class is the one with the highest fitness_score in history
# ---------------------------------------------------------------------------

def test_best_strategy_class_has_highest_fitness():
    loop = StrategyResearchLoop()
    result = loop.run("aggressive momentum", CANDLES_RISING, iterations=4)
    best_fitness = result["best_metrics"]["fitness_score"]
    for record in result["history"]:
        assert record["metrics"]["fitness_score"] <= best_fitness + 1e-12, (
            f"A history record has fitness {record['metrics']['fitness_score']} "
            f"which exceeds best_fitness {best_fitness}"
        )


# ---------------------------------------------------------------------------
# best_prompt must correspond to a history entry's prompt
# ---------------------------------------------------------------------------

def test_best_prompt_is_in_history():
    loop = StrategyResearchLoop()
    result = loop.run("conservative", CANDLES_RISING, iterations=3)
    history_prompts = [r["prompt"] for r in result["history"]]
    assert result["best_prompt"] in history_prompts


# ---------------------------------------------------------------------------
# Input candles are not mutated
# ---------------------------------------------------------------------------

def test_run_does_not_mutate_candles():
    candles_copy = [dict(c) for c in CANDLES_RISING]
    original_closes = [c["close"] for c in candles_copy]

    loop = StrategyResearchLoop()
    loop.run("momentum", candles_copy, iterations=3)

    for i, c in enumerate(candles_copy):
        assert c["close"] == original_closes[i], (
            f"Candle {i} close was mutated"
        )


# ---------------------------------------------------------------------------
# iterations < 1 must raise ValueError
# ---------------------------------------------------------------------------

def test_run_raises_for_zero_iterations():
    loop = StrategyResearchLoop()
    try:
        loop.run("momentum", CANDLES_RISING, iterations=0)
        assert False, "Expected ValueError for iterations=0"
    except ValueError:
        pass


def test_run_raises_for_negative_iterations():
    loop = StrategyResearchLoop()
    try:
        loop.run("trend", CANDLES_RISING, iterations=-1)
        assert False, "Expected ValueError for iterations=-1"
    except ValueError:
        pass


# ---------------------------------------------------------------------------
# Determinism — same inputs produce same best result
# ---------------------------------------------------------------------------

def test_run_is_deterministic():
    loop1 = StrategyResearchLoop()
    loop2 = StrategyResearchLoop()
    result1 = loop1.run("momentum trend", CANDLES_RISING, iterations=3)
    result2 = loop2.run("momentum trend", CANDLES_RISING, iterations=3)

    assert result1["best_metrics"]["fitness_score"] == result2["best_metrics"]["fitness_score"]
    assert result1["best_strategy_class"] is result2["best_strategy_class"]


# ---------------------------------------------------------------------------
# Prompt adjustment — prompt must change across iterations
# (heuristic must actually modify the prompt at least once in 3 iterations)
# ---------------------------------------------------------------------------

def test_prompt_changes_across_iterations():
    loop = StrategyResearchLoop()
    result = loop.run("initial prompt", CANDLES_RISING, iterations=3)
    prompts = [r["prompt"] for r in result["history"]]
    # At minimum the second iteration should have a different prompt
    # (since the first iteration produces a fitness > -inf, adjustment fires)
    assert len(set(prompts)) > 1, (
        "All prompts are identical — prompt adjustment heuristic is not working"
    )


# ---------------------------------------------------------------------------
# Single iteration — first prompt is preserved in history
# ---------------------------------------------------------------------------

def test_single_iteration_history_prompt_matches_input():
    loop = StrategyResearchLoop()
    result = loop.run("my specific prompt", CANDLES_RISING, iterations=1)
    assert result["history"][0]["prompt"] == "my specific prompt"
    assert result["best_prompt"] == "my specific prompt"
