"""Window Indicator Routes
Computational endpoints for analyzing time-series windows
"""
from fastapi import APIRouter, HTTPException
from bson.objectid import ObjectId
import simplejson as json
import pandas as pd
import numpy as np
from typing import Dict, Any
from scipy.signal import welch, hilbert

from database import get_db, get_data_folder_path
from models import WindowFeaturesRequest

router = APIRouter(prefix="/window-indicator", tags=["window-indicator"])


def compute_frequency_features(window_df: pd.DataFrame, fs: float) -> Dict[str, Any]:
    """
    Compute generic frequency-domain features for a time series window.
    Returns slow/fast band power and band ratios.
    
    Args:
        window_df: DataFrame containing the time series window
        fs: Sampling frequency
        
    Returns:
        Dictionary with frequency features for each channel
    """
    results = {}
    for col in window_df.columns:
        f, Pxx = welch(window_df[col].values, fs=fs, nperseg=min(1024, len(window_df[col])))

        def bandpower(f, Pxx, fmin, fmax):
            mask = (f >= fmin) & (f <= fmax)
            return np.trapz(Pxx[mask], f[mask]) if np.any(mask) else 0.0

        bp_delta = bandpower(f, Pxx, 0.5, 4)
        bp_theta = bandpower(f, Pxx, 4, 7)
        bp_alpha = bandpower(f, Pxx, 8, 13)
        bp_beta = bandpower(f, Pxx, 13, 30)

        slow = bp_delta + bp_theta
        fast = bp_alpha + bp_beta
        total = slow + fast + 1e-12

        results[col] = {
            "bp_delta": float(bp_delta),
            "bp_theta": float(bp_theta),
            "bp_alpha": float(bp_alpha),
            "bp_beta": float(bp_beta),
            "slow_ratio": float(slow / total),
            "fast_ratio": float(fast / total)
        }

    return results


def compute_energy_features(window_df: pd.DataFrame, fs: float) -> Dict[str, Any]:
    """
    Compute instantaneous and segment-level energy features for a time series window.
    
    Args:
        window_df: DataFrame containing the time series window
        fs: Sampling frequency
        
    Returns:
        Dictionary with energy features for each channel
    """
    results = {}
    for col in window_df.columns:
        sig = window_df[col].values
        analytic = hilbert(sig)
        envelope = np.abs(analytic)

        rms = float(np.sqrt(np.mean(sig**2)))
        env_mean = float(np.mean(envelope))
        env_std = float(np.std(envelope) + 1e-12)

        results[col] = {
            "rms": rms,
            "mean_envelope": env_mean,
            "std_envelope": env_std,
            "max_envelope": float(np.max(envelope))
        }

    return results


def compute_morphology_features(window_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute waveform morphology features (peak-to-peak amplitude, duration, slope, etc.)
    
    Args:
        window_df: DataFrame containing the time series window
        
    Returns:
        Dictionary with morphology features for each channel
    """
    results = {}
    for col in window_df.columns:
        sig = window_df[col].values

        peak_to_peak = float(np.max(sig) - np.min(sig))

        zero_crossings = np.where(np.diff(np.sign(sig)))[0]
        zcr = float(len(zero_crossings) / max(1, len(sig)))

        deriv = np.gradient(sig)
        max_slope = float(np.max(np.abs(deriv)))

        symmetry = float(np.mean(sig[: len(sig)//2]) - np.mean(sig[len(sig)//2 :]))

        results[col] = {
            "peak_to_peak": peak_to_peak,
            "zero_crossing_rate": zcr,
            "max_slope": max_slope,
            "symmetry_estimate": symmetry
        }

    return results


@router.post("/features")
async def compute_window_features(request: WindowFeaturesRequest):
    """
    Compute frequency, energy, and morphology features for a time-series window.
    
    Args:
        request: WindowFeaturesRequest with file_id, start, and end indices
        
    Returns:
        Dictionary containing frequency, energy, and morphology features
    """
    try:
        db = get_db()
        data_folder_path = get_data_folder_path()
        
        # Get file info from database
        file_doc = db['files'].find_one({'_id': ObjectId(request.file_id)})
        if not file_doc:
            raise HTTPException(status_code=404, detail=f"File not found: {request.file_id}")
        
        # Load the time series data from JSON file
        json_path = file_doc['jsonPath']
        file_path = f'{data_folder_path}/{json_path}'
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Convert JSON data to pandas DataFrame
        # Data structure: list of channel objects, each with 'name' and 'data' arrays
        df_dict = {}
        for channel in data:
            if not channel.get('x', False):  # Skip x-axis channel
                channel_name = channel['name']
                channel_data = channel['data']
                df_dict[channel_name] = channel_data
        
        df = pd.DataFrame(df_dict)
        
        # Validate window indices
        if request.start < 0 or request.end > len(df):
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid window indices: start={request.start}, end={request.end}, data_length={len(df)}"
            )
        
        if request.start >= request.end:
            raise HTTPException(
                status_code=400,
                detail=f"Start index must be less than end index: start={request.start}, end={request.end}"
            )
        
        # Extract the window from the dataframe
        window_df = df.iloc[request.start:request.end]
        
        # Compute features with fs=1.0 (hardcoded as requested)
        fs = 256.0
        
        frequency_features = compute_frequency_features(window_df, fs)
        energy_features = compute_energy_features(window_df, fs)
        morphology_features = compute_morphology_features(window_df)
        
        # Return the features
        return {
            'frequency': frequency_features,
            'energy': energy_features,
            'morphology': morphology_features,
            'window': {
                'start': request.start,
                'end': request.end,
                'length': request.end - request.start
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error computing window features: {str(e)}")

