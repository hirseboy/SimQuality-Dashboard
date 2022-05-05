#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# STATISTICS FUNCTIONS
#
# Helper functions to calculate statistical parameters in order to compare datasets 
# with simulated data with reference data sets and generate an conformity score


import pandas as pd  # Data manipulation and analysis
import numpy as np
import math          # used for mathematical calculations

import warnings      # used to catch warnings inside the functions e.g. when some division by zero errors occur
warnings.filterwarnings("error") 


class StatisticsFunctions:
    
    NEAR_ZERO = 1e-5
    
    ###############################################################################
    ###                      CVRMSE from diff case - ref                        ###
    ###############################################################################
    
    def Calculate_CVRMSE_from_diff_case_ref(diff_case_ref, reference_vector):
        """Calculate the Coefficient of Variation of Root Mean Squared Error (CVRMSE)
        of a case compared to a reference: CVRMSE with all data points [%].
        """
    
        nbr_samples = len(diff_case_ref)        # Number of samples
        avrg_ref = (reference_vector.mean())    # Average value of the reference = number samples ref * mean average ref
        square_diff = diff_case_ref ** 2        
        sum_squares = square_diff.sum()
        CVRMSE = ((math.sqrt(sum_squares / nbr_samples)) / avrg_ref) * 100
        
        return CVRMSE
    
    
    ###############################################################################
    ###                             Daily amplitude                             ###
    ###############################################################################
    
    def Calculate_daily_amplitude(input_vector):
        """Caculate the amplitude (max - min) over 24 hours (daily) from midnight
        to midnight on data df with date and time stamp in 1st column.
        """
    
        vector_min = input_vector.resample("1440min", on="Date and Time").min()  # Daily min (24h resampling)
        vector_max = input_vector.resample("1440min", on="Date and Time").max()  # Daily max (24h resampling)
    
        """With resample .min() or .max(), the date and time stamp column does not 
        replace the index column, so need to select data column if only 1 data 
        column for further calculation"""
        vector_min = vector_min.iloc[:, 1]
        vector_max = vector_max.iloc[:, 1]
    
        daily_amplitude_vector = vector_max - vector_min  # Daily resampled amplitude
    
        return daily_amplitude_vector
    

    "#############################################################################"
    "##                   KPIs / Comparison Metrics functions                   ##"
    "#############################################################################"
    
    ###############################################################################
    ###                                MBE [-]                                  ###
    ###############################################################################
    
    def function_MBE(reference_vector, test_case_vector, date_and_time_stamp_vect):
        """Calculate the Mean Bias Error (MBE) of a case compared to reference.
        MBE with all data points.
        """
    
        "Difference point by point for test case compared to reference profile"
        diff_case_ref = test_case_vector - reference_vector  # Case - Reference
    
        MBE = (diff_case_ref.sum()) / (len(reference_vector))
    
        return round(MBE, 2)
    
    
    ###############################################################################
    ###                                NMBE [%]                                 ###
    ###############################################################################
    
    def function_NMBE(reference_vector, test_case_vector, date_and_time_stamp_vect):
        """Calculate the Normalized Mean Bias Error (NMBE) of a case compared to
        reference [%]. NMBE with all data points.
        """
    
        "Difference point by point for test case compared to reference profile"
        diff_case_ref = test_case_vector - reference_vector  # Case - Reference
    
        NMBE = (diff_case_ref.sum()) * 100 / (reference_vector.sum())
    
        return round(NMBE, 2)
    
    
    ###############################################################################
    ###                           Hourly CVRMSE [%]                             ###
    ###############################################################################
    
    def function_Hourly_CVRMSE(reference_vector, test_case_vector, date_and_time_stamp_vect):
        """Calculate the Coefficient of Variation of Root Mean Squared Error (CVRMSE)
        on Hourly running average data: Need resampling at 60 min freq.
        """
    
        "Difference point by point for test case compared to reference profile"
        diff_case_ref = test_case_vector - reference_vector  # Case - Reference
    
        "Resampling"
        frames = [date_and_time_stamp_vect, diff_case_ref]  # The 2 df to concat
        diff_case_ref = pd.concat(frames, axis=1, join="outer")  # date and time followed by data on the right
        """With resample .mean(), the date and time stamp column replaces the index
        column, so no need to select data column if only 1 data column for further
        calculation"""
        diff_case_ref = diff_case_ref.resample("60min", on="Date and Time").mean()  # Resample as hourly mean average: the time stamp column becomes index column
    
        hourly_CVRMSE = StatisticsFunctions.Calculate_CVRMSE_from_diff_case_ref(diff_case_ref, reference_vector)
    
        return round(hourly_CVRMSE, 2)
    
    
    ###############################################################################
    ###                      Daily Amplitude CVRMSE [%]                         ###
    ###############################################################################
    
    def function_Daily_Amplitude_CVRMSE(
            reference_vector,
            test_case_vector,
            date_and_time_stamp_vect):
        """CVRMSE of the daily amplitude from midnight to midnight: Need resampling
        at 1440 min.
        """
    
        "Daily amplitude test case"
        frames = [date_and_time_stamp_vect, test_case_vector]  # The 2 df to concat
        input_vector = pd.concat(frames, axis=1, join="outer")  # date and time followed by data on the right
        Daily_amplitude_case = StatisticsFunctions.Calculate_daily_amplitude(input_vector)  # Get daily amplitude user test data
    
        "Daily amplitude reference profile"
        frames = [date_and_time_stamp_vect, reference_vector]  # The 2 df to concat
        input_vector = pd.concat(frames, axis=1, join="outer")  # date and time followed by data on the right
        Daily_amplitude_reference = StatisticsFunctions.Calculate_daily_amplitude(input_vector)  # Get daily amplitude user test data
    
        "Difference daily amplitude between test case and reference"
        Diff_daily_aimplitude_case_ref = Daily_amplitude_case - Daily_amplitude_reference
    
        "CVRMSE"
        daily_amp_CVRMSE = StatisticsFunctions.Calculate_CVRMSE_from_diff_case_ref(
            Diff_daily_aimplitude_case_ref, Daily_amplitude_reference)
    
        return round(daily_amp_CVRMSE, 2)
    
    
    ###############################################################################
    ###             R squared (coefficient of determination) [-]                ###
    ###############################################################################
    
    def function_R_squared_coeff_determination(
            reference_vector,
            test_case_vector,
            date_and_time_stamp_vect):
        """R squared (R2) is defined here as the coefficient of determination: it 
        is the proportion of the variance in the dependant variable (model output 
        or model prediction) that is predictable from the independent variable(s) 
        (model input).
        In other words: how good a linear regression fits the data in comparison 
        to a model that is only the average of the dependant variable.
        
        ref: https://en.wikipedia.org/wiki/Coefficient_of_determination#Definitions
        """
    
        "y: observations / reality / measured data / reference data"
        "f: prediction / fitted data / modeled data / test data"
    
        y = reference_vector
        f = test_case_vector
    
        "e: residuals"
        e = y - f
    
        "e2: squares of residuals"
        e2 = e ** 2
    
        "SSres: sum of squares of residuals, or residual sum of squares."
        SSres = e2.sum()
    
        "y_mean: mean of the observed /refeence data"
        y_mean = y.mean()
    
        "squares of difference to the mean for the observed / reference data"
        squares_diff_to_mean = (y - y_mean) ** 2
    
        "SStot: total sum of squares (proportional to the variance of the data)"
        SStot = squares_diff_to_mean.sum()
    
        R_squared = 1 - (SSres / SStot)
    
        return round(R_squared*100, 2)
    
    
    ###############################################################################
    ###                                 MSE [-]                                 ###
    ###############################################################################
    
    def function_MSE(reference_vector, test_case_vector, date_and_time_stamp_vect):
        """Calculate the Mean Squared Error (MSE) of a case compared to a
        reference [-]: MSE with all data points.
        """
    
        "y: observations / reality / measured data / reference data"
        "f: prediction / fitted data / modeled data / test data"
    
        y = reference_vector
        f = test_case_vector
    
        squares_diff = (y - f) ** 2
    
        sum_squares_diff = squares_diff.sum()
    
        nbr_samples = len(test_case_vector)
    
        MSE = sum_squares_diff / nbr_samples # Average the squared differences (residuals)
    
        return round(MSE, 2)
    
    
    ###############################################################################
    ###                                 RMSE [-]                                ###
    ###############################################################################
    
    def function_RMSE(reference_vector, test_case_vector, date_and_time_stamp_vect):
        """Calculate the Root Mean Squared Error (RMSE) of a case 
        compared to a reference [-]: RMSE with all data points.
        """
    
        "y: observations / reality / measured data / reference data"
        "f: prediction / fitted data / modeled data / test data"
    
        y = reference_vector
        f = test_case_vector
    
        squares_diff = (y - f) ** 2
    
        sum_squares_diff = squares_diff.sum()
    
        nbr_samples = len(test_case_vector)
    
        average_squares_diff = sum_squares_diff / nbr_samples
    
        RMSE = np.sqrt(average_squares_diff)
    
        return round(RMSE, 2)
    
    
    ###############################################################################
    ###                                RMSLE [-]                                ###
    ###############################################################################
    
    def function_RMSLE(reference_vector, test_case_vector, date_and_time_stamp_vect):
        """Calculate the Root Mean Squared Logarithmic Error (RMSLE) of a case 
        compared to a reference [-]: RMSLE with all data points.
        """
    
        "y: observations / reality / measured data / reference data"
        "f: prediction / fitted data / modeled data / test data"
            
        y = reference_vector
        f = test_case_vector
    
        log_f = np.log(f + 1)
        log_y = np.log(y + 1)
    
        squares_diff_logs = (log_f - log_y) ** 2
    
        sum_squares_diff = squares_diff_logs.sum()
    
        nbr_samples = len(test_case_vector)
    
        average_squares_diff = sum_squares_diff / nbr_samples
    
        RMSLE = np.sqrt(average_squares_diff)
    
        return round(RMSLE, 5)
    
    
    ###############################################################################
    ###                               CVRMSE [%]                                ###
    ###############################################################################
    
    def function_CVRMSE(reference_vector, test_case_vector, date_and_time_stamp_vect):
        """Calculate the Coefficient of Variation of Root Mean Squared Error (CVRMSE)
        of a case compared to a reference: CVRMSE with all data points [%].
        """
    
        "y: observations / reality / measured data / reference data"
        "f: prediction / fitted data / modeled data / test data"
    
        y = reference_vector
        f = test_case_vector
        
        squares_diff = (y - f) ** 2
    
        nbr_samples = len(reference_vector)  # Number of samples
    
        avrg_ref = reference_vector.mean()  # Average value of the reference = number samples ref * mean average ref
    
        sum_squares = squares_diff.sum()
        
        # division through zero handling
        if math.isclose(avrg_ref, 0 ):
            avrg_ref = StatisticsFunctions.NEAR_ZERO
    
        CVRMSE = ((np.sqrt(sum_squares / nbr_samples)) / avrg_ref) * 100
    
        return round(CVRMSE, 2)
    
    
    ###############################################################################
    ###                                 NRMSE [%]                               ###
    ###############################################################################
    
    def function_NRMSE(reference_vector, test_case_vector, date_and_time_stamp_vect):
        """Calculate the Normalized Root Mean Squared Error (NRMSE) of a case 
        compared to a reference [%]: NRMSE with all data points.
        The RMSE is normalized by the range (amplitude = max - min) of the
        reference data.
        """
    
        "y: observations / reality / measured data / reference data"
        "f: prediction / fitted data / modeled data / test data"
    
        y = reference_vector
        f = test_case_vector
        
        amplitude = max(reference_vector) - min(reference_vector)
    
        squares_diff = (y - f) ** 2
    
        sum_squares_diff = squares_diff.sum()
    
        nbr_samples = len(test_case_vector)
    
        average_squares_diff = sum_squares_diff / nbr_samples
    
        RMSE = np.sqrt(average_squares_diff)
        
        NRMSE = (RMSE / amplitude) * 100
    
        return round(NRMSE, 2)
    
    
    ###############################################################################
    ###                                RMSEIQR [%]                              ###
    ###############################################################################
    
    def function_RMSEIQR(reference_vector, test_case_vector, date_and_time_stamp_vect):
        """Calculate the IQR-Normalized Root Mean Squared Error (RMSEIQR) of a case 
        compared to a reference [%]: RMSEIQR with all data points.
        The RMSE is normalized by the interquartile range (IQR) of the reference
        data.
        """
    
        "y: observations / reality / measured data / reference data"
        "f: prediction / fitted data / modeled data / test data"
           
        y = reference_vector
        f = test_case_vector
        
        "IQR calculation"
        q75, q25 = np.percentile(y, [75 ,25]) # 75th and 25th percentiles of ref data
        IQR = q75 - q25
        
        squares_diff = (y - f) ** 2
    
        sum_squares_diff = squares_diff.sum()
    
        nbr_samples = len(test_case_vector)
    
        average_squares_diff = sum_squares_diff / nbr_samples
    
        RMSE = np.sqrt(average_squares_diff)
        
        RMSEIQR = (RMSE / IQR) * 100
    
        return round(RMSEIQR, 2)
    
    
    ###############################################################################
    ###                                Minimum                                  ###
    ###############################################################################
    
    def function_Minimum(reference_vector, test_case_vector, date_and_time_stamp_vect):
        result = test_case_vector.min()
        
        return round(result, 2)
    
    
    ###############################################################################
    ###                                Maximum                                  ###
    ###############################################################################
    
    def function_Maximum(reference_vector, test_case_vector, date_and_time_stamp_vect):
        result = test_case_vector.max()
        
        return round(result, 2)
    
    
    ###############################################################################
    ###                                Average                                  ###
    ###############################################################################
    
    def function_Average(reference_vector, test_case_vector, date_and_time_stamp_vect):
        result = test_case_vector.mean()
        
        return round(result, 2)
    
    
    ###############################################################################
    ###                           Standard Deviation                            ###
    ###############################################################################
    
    def function_std_dev(reference_vector, test_case_vector, date_and_time_stamp_vect):
        result = np.std(test_case_vector)
        
        return round(result, 2)
    
