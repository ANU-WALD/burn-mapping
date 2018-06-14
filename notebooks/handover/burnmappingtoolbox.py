"""
This script included all the modules used in the burn-severity mapping. All the included modules are listed below:

geometric_median(X,tol,MaxInter): to calculate the geometric median over the given period for the given point

spectral_angle(ref,obs): to calculate the spectral angle to the reference

medoid(X): to calculate the medoid over the given period for the given point

cosdistance(ref,obs): to calculate the cosine distance from the observation to the reference for the given point

nbr_eucdistance(ref,obs): to calculate the euclidean distance between NBR and NBRmed (NBR calculated from geometric median)
"""

import numpy as np
import math

def geometric_median(X,tol,MaxInter):
    """
    This is a script to calculate the Geomatric Median 
    The required variables are:
    "X" is a p x N matric, wehre p = number of bands and N = the number of dates in the period of interest
    "MaxNIter" is the maximum number of iteration
    "tol" is tolerance
    The procedure stop when EITHER error tolerance in solution 'tol' or the maximum number of iteration 'MaxNIter' is reached. 
    Returns a p-dimensional vector   'geoMedian' 
    """
    NDATES = len(X[0])
    l = 0
    y0 = np.nanmean(X,axis=1)
    if len(y0[np.isnan(y0)])>0:
        geoMedian = y0
    else:
        eps = 10**2
        while ( np.sqrt(np.sum(eps**2))> tol and l< MaxInter):

            EucDist = np.transpose(np.transpose(X) - y0)
            EucNorm = np.sqrt(np.sum(EucDist**2,axis=0))
            NotNaN = np.where(~np.isnan(EucNorm))[0]
            y1=np.sum(X[:,NotNaN]/EucNorm[NotNaN],axis=1)/(np.sum(1/EucNorm[NotNaN]))
            if len(y1[np.isnan(y1)])>0:
                eps = 0
            else:
                eps = y1 - y0
                y0 = y1
                l = l+1
        geoMedian = y0
        
    return geoMedian


def spectral_angle(ref,obs):
    """
    'ref' is the reference spectrum, p-dimentional
    'obs' is an arbitary observed spectrum, o-dimensional
    returns the Spetral Angle (in degrees); return NAN if obs have any NAN.
    """
    numer = np.sum(ref*obs)
    denom = np.sqrt(sum(ref**2)*sum(obs**2))
    if ~np.isnan(numer) and ~np.isnan(denom):
        alpha = np.arccos(numer/denom)*180./math.pi
    else:
        alpha = np.nan
    return alpha


def medoid(X):
    """
    "X" is a p x N matric, wehre p = number of bands and N = the number of dates in the period of interest
    Returns a p-dimensional vector Medoid
    """
    NDATES = len(X[0])
    TrackSum = np.empty((NDATES));
    TrackSum.fill(np.nan)
    y0 = np.nanmean(X,axis=1)
    EucDist = np.transpose(np.transpose(X)-y0)
    EucNorm = np.sqrt(np.sum(EucDist**2,axis=0))
    NotNaN = np.where(~np.isnan(EucNorm))[0]
    if len(NotNaN)>0:
        for counter,ll in enumerate(NotNaN):
            y0 = X[:,ll]
            EucDist = np.transpose(np.transpose(X) - y0)
            EucNorm = np.sqrt(np.sum(EucDist**2,axis=0))
            TrackSum[ll] = np.nansum(EucNorm)
        indmin = np.where(TrackSum==np.nanmin(TrackSum))[0]
        Med = X[:,indmin[0]]
       
    else:
        Med = y0
        
    return Med

def cosdistance(ref,obs):
    """
    This module calculates the cosine distance between observation (2-D array with multiple days) and reference (with multiple bands, e.g. 6). The calculation is point based, easily adaptable to any dimension. 
    Required inputs:
    ref: reference e.g. geomatric median [Nbands]
    obs: observation e.g. monthly geomatric median or reflectance [Nbands,ndays]
    return the cosine distance at each time step in [ndays]
    """
    cosdist = np.empty((obs.shape[1],))
    cosdist.fill(np.nan)
    index = np.where(~np.isnan(obs[0,:]))[0]
    tmp = [1 - np.sum(ref*obs[:,t])/(np.sqrt(np.sum(ref**2))*np.sqrt(np.sum(obs[:,t]**2))) for t in index]
    cosdist[index] = np.transpose(tmp)
    return cosdist

def nbr_eucdistance(ref,obs):
    """
    This module calculated the euclidean distance between the NBR at each time step with the NBR calculated from the geometric medians and also the direction of change to the NBR from the geometric medians.
    Required inputs:
    ref: NBR calculated from geometric median, one value
    obs: NBR time series, 1-D time series array with ndays 
    return the euclidean distance and change direction (1: decrease; 0: increase) at each time step in [ndays]
    """
    NBRdist = np.empty((obs.shape[0],))
    Sign = np.zeros((obs.shape[0],))
    NBRdist.fill(np.nan)
    index = np.where(~np.isnan(obs[:]))[0]
    EucDist = (obs[index]-ref)
    EucNorm = np.sqrt((EucDist**2))    
    NBRdist[index] = EucNorm
    Sign[index[EucDist<0]] = 1
    return NBRdist, Sign

def severity(CDist,CDistoutlier,Time,NBR,NBRDist,NBRoutlier,Sign,Method=3):  
    """
    This module calculated the severity and stored the duration and start date of the change.
    Required inputs:
    CDist: cosine distance in 1D list with ndays
    CDistoutlier: outlier for cosine distance, 1 for each point
    Time: dates
    NBR: NBR time series in 1D list with ndays
    NBRDist: Euclidean distance from NBR to NBRmed in a 1D list with ndays
    NBRoutlier: outlier for NBRdist
    Sign: change direction for NBR, if Sign==1, NBR decrease from the median
    Method: 1,2,3 to choose
        Method 1: only use cosine distance as an indicator for change
        Method 2: use cosine distance together with NBR<0
        Method 3: use both cosine distance, NBR euclidean distance, and NBR change direction for change detection
        
    outputs include the severity, start date and duration
    """
    sevindex=0
    startdate=0
    duration=0
    notnanind = np.where(~np.isnan(CDist))[0] #remove the nan values for each pixel
    cosdist = CDist[notnanind]
    if Method==1:#only include change where cosine distance above the line
        outlierind = np.where((cosdist>CDistoutlier))[0] 
    if Method==2:#cosdist above the line and NBR<0
        outlierind = np.where((cosdist>CDistoutlier) & (NBR[notnanind]<0))[0] 
    if Method==3:#both cosdist and NBR dist above the line and it is negative change
        outlierind = np.where((cosdist>CDistoutlier) & (NBRDist[notnanind]>NBRoutlier) & (Sign[notnanind]==1))[0] 
    
    time = Time[notnanind]
    outlierdates = time[outlierind]
    Nout = len(outlierind)
    AreaAboveD0 = 0
    if Nout>=2:
        tt = []            
        for ii in range(0,Nout):
            if outlierind[ii]+1<len(time):
                u = np.where(time[outlierind[ii]+1]==outlierdates)[0] #next day have to be outlier to be included
                #print(u)

                if len(u)>0:
                    t1_t0 = (time[outlierind[ii]+1]-time[outlierind[ii]])/np.timedelta64(1, 's')/(60*60*24)
                    y1_y0 = (cosdist[outlierind[ii]+1] +cosdist[outlierind[ii]] )-2*CDistoutlier
                    AreaAboveD0 = AreaAboveD0 + 0.5*y1_y0*t1_t0 # calculate the area under the curve
                    duration = duration + t1_t0
                    tt.append(ii) # record the index where it is detected as a change

        if len(tt)>0:                
            startdate = time[outlierind[tt[0]]] #record the date of the first change 
            sevindex = AreaAboveD0
   
    return sevindex, startdate, duration