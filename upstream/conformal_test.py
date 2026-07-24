"""Sequential conformal martingale tests for exchangeability."""

import numpy as np
from pairwise import simulate_ARm_process, simulate_exchangeable_sequence
from optimization import ONS


class ConformalTest:
    """Run online conformal p-value tests with martingale betting.

    The default conformity score is the sample value itself. Subclasses can
    override ``calculate_conformity_score`` to test exchangeability with a
    problem-specific score while reusing the p-value and martingale logic.
    """

    def __init__(self, alpha: float = 0.05, D: float = 1.0):
        """Initialize the conformal exchangeability test.

        Parameters
        ----------
        alpha : float, default=0.05
            Significance level. The martingale rejection threshold is
            ``1 / alpha``.
        D : float, default=1.0
            Bound for the ONS betting parameter. If ``D > 0``, the test uses
            ONS-optimized betting; otherwise, it uses a simple jumper
            martingale.
        """
        if not 0 < alpha < 1:
            raise ValueError("alpha must be between 0 and 1")

        self.alpha = alpha
        self.threshold = 1 / alpha
        self.D = D  # Parameter for the ONS optimization
        self.scores = None  # Will be pre-allocated numpy array
        self.n_scores = 0  # Number of scores currently stored
        self.p_values = []  # Store p-values for analysis

    def calculate_conformity_score(self, sample) -> float:
        """Return the conformity score for one sample.

        The base implementation uses the sample value directly. Override this
        method in subclasses when a different score is needed.
        """
        return sample

    def calculate_p_values(self, test_set) -> np.ndarray:
        """Calculate online randomized conformal p-values for a sequence."""
        # Convert test set to numpy array if not already
        test_set = np.array(test_set)

        # Calculate conformity scores for all samples
        scores = np.array([self.calculate_conformity_score(x) for x in test_set])
        p_values = np.zeros_like(scores, dtype=np.float64)

        # Calculate p-values using rank statistics
        for i in range(len(scores)):
            smaller, equal = self._count_smaller_and_equal(scores, i)
            p_value = (np.random.uniform(0, 1) * equal + smaller) / (i + 1)
            p_values[i] = p_value

        self.p_values = p_values
        return p_values

    def _count_smaller_and_equal(self, arr: np.ndarray, index: int) -> tuple[int, int]:
        """Count preceding-or-current scores smaller than or equal to one score.

        Parameters
        ----------
        arr : np.ndarray
            Array of conformity scores.
        index : int
            Index of the score being tested.

        Returns
        -------
        tuple[int, int]
            Counts of scores smaller than, and equal to, ``arr[index]`` among
            observations seen so far, including ``arr[index]`` itself.
        """
        target_element = arr[index]
        # In an online setting, we only consider elements seen so far (from index 0 to i+1)
        subset = arr[:index+1]

        smaller_count = np.sum(subset < target_element)
        equal_count = np.sum(subset == target_element)

        return smaller_count, equal_count

    def _calculate_p_value(self, new_score: float) -> float:
        """Calculate the randomized conformal p-value for a new score.

        The method compares ``new_score`` with previously stored scores and
        includes the new score as one additional tie.

        Parameters
        ----------
        new_score : float
            Conformity score for the new sample.

        Returns
        -------
        float
            Randomized online conformal p-value.
        """
        if self.n_scores > 0:
            scores_view = self.scores[:self.n_scores]
            smaller_count = np.sum(scores_view < new_score)
            equal_count = np.sum(scores_view == new_score)
        else:
            smaller_count = 0
            equal_count = 0

        equal_count += 1
        n = self.n_scores + 1
        return (np.random.uniform(0, 1) * equal_count + smaller_count) / n

    def test_exchangeability(self, test_set, cal_set_size=0, J=0.01, early_stop: bool = False,
                              C=0., warmup_samples=0, calibration_size: int = None,
                              warmup: int = None) -> tuple[int, np.ndarray]:
        """Run the sequential conformal martingale test.

        Parameters
        ----------
        test_set : array-like
            Sequence of samples processed online.
        cal_set_size : int, default=0
            Number of initial samples used only to seed the rank history.
        J : float, default=0.01
            Mixing parameter for the simple jumper martingale branch.
        early_stop : bool, default=False
            Stop processing after the martingale first crosses ``1 / alpha``.
        C : float, default=0.
            Threshold below which the ONS eta is treated as 0.
        warmup_samples : int, default=0
            Number of post-calibration samples used to update ONS without
            changing the martingale from 1.
        calibration_size : int, optional
            Alias for ``cal_set_size``.
        warmup : int, optional
            Alias for ``warmup_samples``.

        Returns
        -------
        tuple[int, np.ndarray]
            The first index where the martingale crosses the threshold, or -1 if
            it never does, and the martingale values over time.
        """
        if calibration_size is not None:
            cal_set_size = calibration_size
        if warmup is not None:
            warmup_samples = warmup

        test_set = np.array(test_set)
        cal_set_size = 0 if cal_set_size is None else int(cal_set_size)
        warmup_samples = 0 if warmup_samples is None else int(warmup_samples)
        if cal_set_size < 0:
            raise ValueError("cal_set_size must be non-negative")
        if warmup_samples < 0:
            raise ValueError("warmup_samples must be non-negative")
        if cal_set_size > len(test_set):
            raise ValueError("cal_set_size cannot exceed the number of samples")
        if not 0 <= J <= 1:
            raise ValueError("J must be between 0 and 1")

        learnable = self.D > 0

        self.scores = np.zeros(len(test_set), dtype=np.float64)
        self.n_scores = 0
        self.p_values = []

        for sample in test_set[:cal_set_size]:
            new_score = self.calculate_conformity_score(sample)
            p_value = self._calculate_p_value(new_score)
            self.p_values.append(p_value)
            self.scores[self.n_scores] = new_score
            self.n_scores += 1

        actual_test_set = test_set[cal_set_size:]
        first_exceeding_index = -1

        if learnable:
            optim = ONS(ci_eps=0, D=self.D) # without CI consideration
        else:
            jumper_capitals = {-1: 1/3., 0: 1/3., 1: 1/3.}

        current_martingale = 1.0
        martingale_values = [current_martingale] * cal_set_size

        # Process each test sample one at a time
        for idx, test_sample in enumerate(actual_test_set):
            new_score = self.calculate_conformity_score(test_sample)
            p_value = self._calculate_p_value(new_score)
            self.p_values.append(p_value)
            self.scores[self.n_scores] = new_score
            self.n_scores += 1

            if idx < warmup_samples:
                if learnable:
                    optim.step(p_value)
                martingale_values.append(1.)
                continue

            if learnable:
                eta_t = optim.etas[-1]
                if abs(eta_t) < C:
                    eta_t = 0
                current_martingale *= (1 + eta_t * (p_value - 0.5))
                current_martingale = min(current_martingale, 1e250)
                optim.step(p_value)
            else:
                previous_martingale = current_martingale
                for epsilon in jumper_capitals.keys():
                    jumper_capitals[epsilon] = (
                        (1 - J) * jumper_capitals[epsilon]
                        + (J / 3.) * previous_martingale
                    )
                    jumper_capitals[epsilon] *= 1 + epsilon * (p_value - 0.5)
                current_martingale = np.sum(list(jumper_capitals.values()))

            martingale_values.append(current_martingale)
            if current_martingale >= self.threshold:
                if first_exceeding_index == -1:
                    first_exceeding_index = len(martingale_values) - 1
                if early_stop:
                    break

        return first_exceeding_index, np.array(martingale_values)



# Example usage and demonstration
if __name__ == "__main__":
    np.random.seed(42)

    # Test parameters
    N_OBS = 300
    ALPHA_DEMO = 0.05

    print("Pairwise Betting Test for Exchangeability - Continuous Case")
    print("=" * 60)

    # Test 1: AR(1) process (should reject exchangeability)
    a_true, sigma_true = 0.2, 1.0
    print(f"\nTest 1: AR(1) Process (a={a_true}, σ={sigma_true})")
    print("-" * 40)
    ar1_data = simulate_ARm_process(N_OBS, a_true, sigma_true)

    test = ConformalTest(alpha=ALPHA_DEMO)

    # Oracle test (knowing true parameters)
    oracle_results = test.test_exchangeability(ar1_data)[1]

    print("Oracle Test:")
    print(f"  Max wealth: {max(oracle_results):.4f}, argmax: {np.argmax(oracle_results)}")

    # Estimated test
    estimated_result = test.test_exchangeability(ar1_data)[1]

    print("\nEstimated Test:")
    print(f"  Max wealth: {max(estimated_result):.4f}, argmax: {np.argmax(estimated_result)}")


    # Test 2: Exchangeable sequence (should not reject)
    print("\n\nTest 2: I.I.D. Normal Sequence (Exchangeable)")
    print("-" * 40)

    iid_data = simulate_exchangeable_sequence(N_OBS, 'normal')

    iid_result = test.test_exchangeability(iid_data)[1]

    print("\nEstimated Test:")
    print(f"  Max wealth: {max(iid_result):.4f}, argmax: {np.argmax(iid_result)}")

