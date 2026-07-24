"""Online Newton Step optimizer for CTM betting parameters."""

import numpy as np


class ONS:
    """Maintain and update a bounded one-dimensional betting parameter.

    The optimizer stores the history of eta values and applies an Online Newton
    Step-style update using confidence-interval uncertainty around each observed
    empirical CDF value.
    """

    def __init__(self, ci_eps, D=0.5):
        self.D = D
        self.ci_eps = ci_eps
        self.etas = [0]
        self.a = 1

    def step(self, u_t, smooth_param=0.):
        """Update eta from one empirical CDF value and return the new eta.

        Parameters
        ----------
        u_t : float
            Current empirical CDF value, typically in ``[0, 1]``.
        smooth_param : float, default=0.
            Positive values use the differentiable smoothed absolute-value
            surrogate ``sqrt(eta_t**2 + smooth_param**2)`` in the gradient.

        Returns
        -------
        float
            The updated eta value, clipped to ``[-D, D]``.
        """
        eta_t = self.etas[-1]
        if smooth_param > 0:
            v_t_dot_eta_t = (1/(0.5+(1+smooth_param)*self.ci_eps))*\
                (eta_t*(u_t - 0.5) - np.sqrt(eta_t**2 + smooth_param**2)*self.ci_eps)
            dv_t = (1/(0.5+(1+smooth_param)*self.ci_eps))*\
                (u_t - 0.5 - eta_t*self.ci_eps/np.sqrt(eta_t**2 + smooth_param**2))
            z_t = dv_t / (1 + v_t_dot_eta_t)
        else:
            v_t = (1/(0.5+self.ci_eps))*(u_t - 0.5 - np.sign(eta_t) * self.ci_eps)
            z_t = v_t / (1 + eta_t * v_t)
        self.a = self.a + z_t**2
        eta_new = eta_t + (2/(2-np.log(3))) * z_t / self.a
        if abs(eta_new) > self.D:
            eta_new = self.D * np.sign(eta_new)
        self.etas.append(eta_new)
        return eta_new
