from math import exp

import numpy as np


def peResponse(t, delay, nphotons, speAmplitude, riseTime, fallTime):
    if t < delay:
        return 0
    else:
        return -nphotons * speAmplitude * exp(-(t - delay) / fallTime) * (1 - exp(-(t - delay) / riseTime))


def waveGen(t, speAmplitude, riseTime, fallTime):
    response = np.array([0 for ti in t])
    true_response = np.array([0 for ti in t])

    while True:
        nhits = 0
        nhits = np.random.poisson(2)
        if nhits > 0:
            break

    while True:
        checkSumHits = 0
        for aHit in range(0, nhits):
            delay = np.random.uniform(t[0], t[-1])
            nphotons = np.random.poisson(3)
            checkSumHits = checkSumHits + nphotons
            temp =  np.array([peResponse(ti, delay, nphotons, speAmplitude, riseTime, fallTime) for ti in t])
            noiseResponse = np.array([np.random.normal(0, speAmplitude / 15) for ti in t])
            response = response + noiseResponse + temp
            true_response = true_response + temp
        if checkSumHits > 0:
            break

    return [response, true_response]


def getRawADC(p, res):
    return round(p / res)


def getADC(p, nBits, res, voltMin):
    guessADC = round((p - voltMin) / res)
    if guessADC < 0:
        return 0
    if guessADC > (2 ** nBits - 1):
        return 2 ** nBits - 1
    return guessADC

def digitizeWave(p, nBits, voltMin, dynamicRange, offset):
    resolution = dynamicRange / (2**nBits - 1)
    return np.array([(getADC(pi, nBits=nBits, res=resolution, voltMin=voltMin) + offset) for pi in p])

def aTrigger(dt, nsamples, speAmplitude, riseTime, fallTime):
    t = np.arange(0, nsamples*dt, dt)
    [p, true_p] = waveGen(t, speAmplitude=speAmplitude, riseTime=riseTime, fallTime=fallTime)

    return [t, p, true_p]

def aDigitizedTrigger(dt, nsamples, speAmplitude, riseTime, fallTime, nBits, voltMin, dynamicRange, offset):
    t = np.arange(0, nsamples*dt, dt)
    [p, true_p] = waveGen(t, speAmplitude=speAmplitude, riseTime=riseTime, fallTime=fallTime)
    digital_p = digitizeWave(p, nBits=nBits, voltMin=voltMin, dynamicRange=dynamicRange, offset=offset)
    digital_true_p = digitizeWave(true_p, nBits=nBits, voltMin=voltMin, dynamicRange=dynamicRange, offset=offset)

    return [t, digital_p, digital_true_p]