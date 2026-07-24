import numpy as np

def compute_dkw_band(n, alpha):
    """Compute the DKW confidence band width."""
    epsilon = np.sqrt(np.log(2 / alpha) / (2 * n))
    return epsilon


def empirical_cdf(data):
    """Estimates the empirical CDF given data and returns the CDF as a function."""
    data_sorted = np.sort(data)
    n = len(data_sorted)

    def cdf_function(x):
        """Returns the empirical CDF value for a given point x."""
        return np.sum(data_sorted <= x) / n

    return cdf_function

def empirical_cdf_rand(data):
    """Estimates the empirical CDF given data and returns the CDF as a function."""
    data_sorted = np.sort(data)
    n = len(data_sorted)

    def cdf_function(x):
        """Returns the empirical CDF value for a given point x."""
        return (np.sum(data_sorted < x) + np.random.rand()*(1+np.sum(data_sorted == x))) / (n + 1)

    return cdf_function

def betting_function(u_t, betting_param = 1.0, interval_eps = 0., smooth_param = 0.):
    
    if smooth_param > 0:
        bet_res = 1 + (1/(0.5+(1+smooth_param)*interval_eps))*(betting_param*(u_t - 0.5) - np.sqrt(betting_param**2 + smooth_param**2)*interval_eps)
    else:
        bet_res = 1 + (1/(0.5+interval_eps))*betting_param*(u_t - 0.5 - np.sign(betting_param)*interval_eps)
        
    return bet_res
