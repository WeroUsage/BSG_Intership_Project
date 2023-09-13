import numpy as np
import scipy


def get_p_value(mean, sd, two_sided=False):
    """Calculate the p value (I.e. the probability of a false positive error.)

    Args:
        mean (flaot): the mean of the normal distribution representing the alternative hypothesis.
          0 is by default the mean of the null hypothesis
        sd (float): standard deviation of both alternative and null hypothesis
        two_sided (bool, optional): Whether you want to calculate a one sided or two sided p value.
            Defaults to False.

    Returns:
        float: the p value of our experiment
    """
    # calculate z_score: how many standard deviations d_hat is from 0
    z_score = mean / sd

    # calculate p value
    p_val = scipy.stats.norm.sf(abs(z_score))

    # if distribution is two sided, multiply p value by 2
    if two_sided:
        p_val *= 2
    return p_val


def get_power(p_A, p_B, se1, se2, two_sided=False, significance=0.05):
    """Calculate the power (i.e. the probability that if the alternative hypothesis is correct,
      we will be able to detect it with statistical significance)

    Args:
        p_A (float): redemption probability for group A
        p_B (float): redemption probabiloty for group B
        se1 (float): standard error for group A
        se2 (float): standard error for group B
        two_sided (bool, optional): whether we want to run a one sided or two sided test.
          Default to False.
        significance (float, optional): a value from 0 to 1 representing the threshold of
            statistical significance. Default to 0.05.

    Returns:
        float: A value between 0 and 1 representig the power of our experiment
    """
    positive = p_B > p_A
    null_hyp_z_score = scipy.stats.norm.isf(significance, loc=0, scale=1)
    if positive or not two_sided:
        power = scipy.stats.norm.sf(
            (p_A + se1 * null_hyp_z_score - p_B) / se2,
            loc=0,
            scale=1,
        )
    else:
        power = scipy.stats.norm.sf(
            (p_B + se2 * null_hyp_z_score - p_A) / se1,
            loc=0,
            scale=1,
        )
    return power


def get_p_val_and_power(
    nobs_A,
    p_A,
    min_detect_effect,
    nobs_B=None,
    two_sided=False,
    statistical_significance=0.05,
    min_power=0.8,
):
    """Calculate the P value and power for an A/B test with the given caracteristics

    Args:
        nobs_A (int): number of customers in the control group A
        p_A (float): default target proportion for control group A
        min_detect_effect (float): minimum difference you want to be able to detect between group A
          and group B
        nobs_B (float, optional): number of customers in the control group A, if None,
            the group B is assumed to be the same size as group A. Defaults to None.
        two_sided (bool, optional): whether the test will be two sided or one sided.
            Defaults to False.
        statistical_significance (float, optional): Thresholds of the p-value to consider
            a result statistically significant. Defaults to 0.05.
        min_power (float, optional): minimum power required for the experiment. Defaults to 0.8.

    Returns:
        tuple(float, float, bool): a tuple containing (p-value, power, whether the experiment
         is statistically significant)
    """
    if nobs_B is None:
        nobs_B = nobs_A

    p_B = p_A + min_detect_effect

    significance = (
        statistical_significance / 2 if two_sided else statistical_significance
    )

    # standard error (standard deviation of normal distribution)
    se1 = (p_A * (1 - p_A) / nobs_A) ** (1 / 2)
    se2 = (p_B * (1 - p_B) / nobs_B) ** (1 / 2)

    # calculate standard deviation of the sum of the A and B group
    # Knowing that the variance of the sum is sum of variance
    # This will be the sd of both the null and the alternative hypothesis
    sd_of_sum = (se1**2 + se2**2) ** (1 / 2)

    # calculate d_hat, as the mean of the alternative hypothesis
    # assuming the mean of the null hypothesis is 0, and the sd of both is sd_of_sum
    d_hat = p_B - p_A

    p_value = get_p_value(mean=d_hat, sd=sd_of_sum, two_sided=two_sided)

    power = get_power(p_A, p_B, se1, se2, two_sided, significance)

    if power >= min_power and p_value <= statistical_significance:
        result_is_significant = True
    else:
        result_is_significant = False
    return p_value, power, result_is_significant


def calculate_min_sample_size(
    p_A,
    min_detect_effect,
    step_size=100,
    max_feasible_observations=1_000_000,
    two_sided=False,
    statistical_significance=0.05,
    min_power=0.8,
):
    """Function that calculates the minimum sample size of each gropu to make an A/B
        test statistically significant

    Args:
        p_A (float): Baseline target proportion for control group A
        min_detect_effect (float): minimum effect we need to be able to detect between success
          probability of control group A and test group B
        step_size (int, optional): Step size used to search the sample size. Defaults to 100.
        max_feasible_observations (int, optional): maximum number of observations that are feasible
          for the experiment. If at this number the experiment is still not statistically significant,
          the output will be None. Defaults to 1_000_000.
        two_sided (bool, optional): whether the test will be one sided or two-sided. Defaults to False.
        statistical_significance (float, optional): threshold of the p-value to determine statistical
          significante. Defaults to 0.05.
        min_power (float, optional): threshold for the minimum power needed for this experiment.
          Defaults to 0.8.

    Returns:
        int: Minimum sample size needed in each group to make the A/B test statistically significant.
    """
    for nobs in range(step_size, max_feasible_observations, step_size):
        res = get_p_val_and_power(
            nobs_A=nobs,
            p_A=p_A,
            min_detect_effect=min_detect_effect,
            two_sided=two_sided,
            statistical_significance=statistical_significance,
            min_power=min_power,
        )
        if res[2]:
            return nobs
    return None


def calculate_min_detect_effect(
    p_A,
    nobs_A,
    nobs_B=None,
    step_size=0.0001,
    max_effect_tested=1,
    two_sided=False,
    statistical_significance=0.05,
    min_power=0.8,
):
    """Function that calculates the highest "minimum detectable effect" that would make the
        A/B test statistically significant

    Args:
        p_A (_type_): Baseline target proportion for the control group A
        nobs_A (int): Number of observations in the control group A
        nobs_B (int, optional): number of observations in the control group B, if None,
            it will be set equal to nobs_A. Defaults to None.
        step_size (float, optional): step size for the search. the minimum detectable
            effect will be searched in increments based on this number. Defaults to 0.0001.
        max_effect_tested (int, optional): maximum value for the minimum detectable effect tested.
            if the experiment is not statistical significant at this value, the function will return None.
              Defaults to 1.
        two_sided (bool, optional): whether the test is two sided or one sided. Defaults to False.
        statistical_significance (float, optional): threshold of the p-value to be considered
            statistically significant. Defaults to 0.05.
        min_power (float, optional): threshold for the minimum power required by the experiment.
            Defaults to 0.8.

    Returns:
        float: the highest "minimum detectable effect" that would make this experiment statistically
            significant.
    """
    for min_detect_effect in np.arange(
        step_size,
        max_effect_tested + step_size,
        step_size,
    ):
        res = get_p_val_and_power(
            nobs_A=nobs_A,
            nobs_B=nobs_B,
            p_A=p_A,
            min_detect_effect=min_detect_effect,
            two_sided=two_sided,
            statistical_significance=statistical_significance,
            min_power=min_power,
        )
        if res[2]:
            return min_detect_effect
    return None


if __name__ == "__main__":
    p_A = 0.02
    mde = 0.005
    print(f"assumptions:\nbaseline target proportion of controll group: {p_A*100:.2f}%")
    print(f"minimum detectable effect: {mde*100:.2f}pp")
    print()
    min_sample_size = calculate_min_sample_size(
        p_A=p_A,
        min_detect_effect=mde,
        two_sided=False,
    )
    print(f"Min sample size: {min_sample_size}")
