"""Regularised deconvolution with an explicit stopping criterion.

Deblurring is the well-posed sibling of the occlusion problem. A blur kernel
attenuates high frequencies rather than annihilating a subspace, so inversion is
legitimate — but only down to the noise floor. Below that floor the inverse
filter amplifies noise faster than signal, and every additional "improvement" is
structured noise that looks like detail.

This module therefore estimates the noise floor first and reports the frequency
beyond which nothing was recovered. A deblur result without that number is not
a measurement.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

__all__ = ["DeblurResult", "estimate_noise_sigma", "gaussian_psf", "wiener_deblur"]


def estimate_noise_sigma(image: np.ndarray) -> float:
    """Robust noise estimate via the median absolute deviation of a Laplacian.

    Immerkaer's method: convolving with a kernel that annihilates linear ramps
    leaves mostly noise. Taking the MAD rather than the standard deviation keeps
    genuine edges — which are sparse and large — from inflating the estimate.
    The 1.4826 factor makes MAD a consistent estimator of sigma for Gaussians.
    """
    k = np.array([[1.0, -2.0, 1.0], [-2.0, 4.0, -2.0], [1.0, -2.0, 1.0]])
    from scipy.signal import convolve2d

    response = convolve2d(image, k, mode="valid")
    mad = float(np.median(np.abs(response - np.median(response))))
    sigma = 1.4826 * mad
    # Normalise by the kernel's L2 norm, which is 6 for the mask above.
    return sigma / 6.0


def gaussian_psf(shape: tuple[int, int], sigma: float) -> np.ndarray:
    """Unit-sum Gaussian point spread function, centred for FFT use."""
    if sigma <= 0:
        raise ValueError("sigma must be positive")
    h, w = shape
    y = np.arange(h) - h // 2
    x = np.arange(w) - w // 2
    yy, xx = np.meshgrid(y, x, indexing="ij")
    psf = np.exp(-(yy**2 + xx**2) / (2.0 * sigma**2))
    return psf / psf.sum()


@dataclass
class DeblurResult:
    """A deblurred image plus the honest limit of what it recovered."""

    image: np.ndarray
    noise_sigma: float
    cutoff_cycles_px: float  # beyond this frequency, nothing was recovered
    effective_gain_limit: float

    def summary(self) -> dict[str, float]:
        return {
            "noise_sigma": self.noise_sigma,
            "cutoff_cycles_px": self.cutoff_cycles_px,
            "effective_gain_limit": self.effective_gain_limit,
        }


def wiener_deblur(
    image: np.ndarray,
    psf: np.ndarray,
    noise_sigma: float | None = None,
) -> DeblurResult:
    """Wiener deconvolution with a measured, not guessed, noise-to-signal ratio.

    The Wiener filter H*/(|H|^2 + NSR) is the minimum-mean-squared-error linear
    inverse. Its virtue here is the NSR term, which automatically stops
    amplifying each frequency once the blur has pushed it under the noise — this
    is the mathematical statement of "detail below the noise floor is gone".

    ``cutoff_cycles_px`` reports where |H|^2 falls to the NSR, i.e. the highest
    frequency at which any real recovery occurred. Claims about structure finer
    than 1 / cutoff pixels are not supported by the output.
    """
    if image.shape != psf.shape:
        raise ValueError(
            f"psf shape {psf.shape} must match image shape {image.shape}; "
            "pad the psf rather than cropping the image"
        )

    if noise_sigma is None:
        noise_sigma = estimate_noise_sigma(image)

    signal_power = float(np.var(image))
    if signal_power <= 0:
        raise ValueError("image has zero variance; nothing to deconvolve")

    nsr = (noise_sigma**2) / signal_power

    h = np.fft.fft2(np.fft.ifftshift(psf))
    g = np.fft.fft2(image)

    h2 = np.abs(h) ** 2
    filt = np.conj(h) / (h2 + nsr)
    restored = np.real(np.fft.ifft2(g * filt))

    # Locate the frequency at which the blur transfer function drops to the NSR.
    hh, ww = image.shape
    fy = np.fft.fftfreq(hh)[:, None]
    fx = np.fft.fftfreq(ww)[None, :]
    freq = np.sqrt(fy**2 + fx**2)
    recovered = h2 > nsr
    cutoff = float(freq[recovered].max()) if recovered.any() else 0.0

    return DeblurResult(
        image=np.clip(restored, 0.0, 1.0),
        noise_sigma=float(noise_sigma),
        cutoff_cycles_px=cutoff,
        effective_gain_limit=float(1.0 / np.sqrt(nsr)) if nsr > 0 else float("inf"),
    )
