"""Unit tests for TerminationCriteria — convergence detection."""

from agentforge.evoforge.engine.termination import TerminationCriteria


class TestTerminationCriteriaUnit:
    def test_max_generations(self):
        tc = TerminationCriteria(max_generations=10)
        assert tc.should_terminate(9, 0.0) == (False, "")
        assert tc.should_terminate(10, 0.0) == (True, "MAX_GENERATIONS")

    def test_fitness_threshold(self):
        tc = TerminationCriteria(fitness_threshold=0.95)
        assert tc.should_terminate(1, 0.9) == (False, "")
        assert tc.should_terminate(1, 0.95) == (True, "FITNESS_THRESHOLD")
        assert tc.should_terminate(1, 1.0) == (True, "FITNESS_THRESHOLD")

    def test_fitness_threshold_none_fitness(self):
        tc = TerminationCriteria(fitness_threshold=0.95)
        assert tc.should_terminate(1, None) == (False, "")

    def test_convergence_detects_stagnation(self):
        tc = TerminationCriteria(convergence_generations=3, convergence_threshold=0.01)
        fitness = 1.0
        # First call sets _prev_best, no stagnation count yet
        assert tc.should_terminate(0, fitness) == (False, "")
        # Next 3 stagnant calls accumulate count to 3
        assert tc.should_terminate(0, fitness) == (False, "")  # count=1
        assert tc.should_terminate(0, fitness) == (False, "")  # count=2
        assert tc.should_terminate(0, fitness) == (True, "CONVERGENCE")  # count=3

    def test_convergence_resets_on_improvement(self):
        tc = TerminationCriteria(convergence_generations=3, convergence_threshold=0.01)
        assert tc.should_terminate(0, 1.0) == (False, "")
        assert tc.should_terminate(0, 1.0) == (False, "")
        # Improvement resets counter
        assert tc.should_terminate(0, 2.0) == (False, "")
        # Counter back to 0
        assert tc.should_terminate(0, 2.0) == (False, "")

    def test_no_criteria_never_terminates(self):
        tc = TerminationCriteria()
        assert tc.should_terminate(1000, 0.99) == (False, "")

    def test_none_fitness_no_convergence(self):
        tc = TerminationCriteria(convergence_generations=3)
        assert tc.should_terminate(0, None) == (False, "")
