import numpy as np
import scipy.signal as scisig

import SiPMWaveGen as swg


def FindPedestal(p, m):
    noOutlier = RejectOutliers(p, m=m)
    return np.mean(noOutlier)


def FindDigitizedPedestal(p, m, nBits, dynamicRange, noiseSigma):
    noOutlier = FindPedestal(p=p, m=m)
    res = dynamicRange / (2 ** nBits - 1)
    noiseInADC = swg.getRawADC(noiseSigma, res)

    return [np.mean(noOutlier), noiseInADC]


def RejectOutliers(data, m=2.):
    d = np.abs(data - np.median(data))
    mdev = np.median(d)
    s = d / mdev if mdev else 0.
    return data[s < m]


def WaveformDiscriminator(p,
                          noiseSigma,
                          nNoiseSigmaThreshold=1,
                          sgFilter=True,
                          sgWindow=15,
                          sgPolyOrder=3):
    [baselineVal, noiseInADC] = FindDigitizedPedestal(p=p, m=3, nBits=12, dynamicRange=1, noiseSigma=noiseSigma)
    if sgFilter:
        filter_p = scisig.savgol_filter(x=p, window_length=sgWindow, polyorder=sgPolyOrder)
        hitLogic = np.array(
            [(True if pi < baselineVal - nNoiseSigmaThreshold * noiseInADC else False) for pi in filter_p])
    else:
        hitLogic = np.array([(True if pi < baselineVal - nNoiseSigmaThreshold * noiseInADC else False) for pi in p])
    return [hitLogic, baselineVal, noiseInADC]


def DiscriminatorConditioning(p,
                              noiseSigmaInVolt,
                              durationTheshold=5,
                              adjDurationThreshold=5,
                              nNoiseSigmaThreshold=1,
                              sgFilter=True,
                              sgWindow=15,
                              sgPolyOrder=3):
    [hitLogic, baseline, noiseSigma] = WaveformDiscriminator(p=p,
                                                             noiseSigma=noiseSigmaInVolt,
                                                             nNoiseSigmaThreshold=nNoiseSigmaThreshold,
                                                             sgFilter=sgFilter,
                                                             sgWindow=sgWindow,
                                                             sgPolyOrder=sgPolyOrder)

    for i in range(1, np.size(hitLogic)):
        if ((not hitLogic[i - 1]) and hitLogic[i]) and hitLogic[i]:
            countDuration = 0
            for j in range(i, np.size(hitLogic) - 1):
                if hitLogic[j]:
                    countDuration = countDuration + 1
                if not hitLogic[j + 1]:
                    break

            if countDuration < durationTheshold:
                for j in range(i, i + countDuration):
                    hitLogic[j] = False

    for i in range(1, np.size(hitLogic)):
        if (hitLogic[i - 1] and (not hitLogic[i])) and (not hitLogic[i]):
            countDuration = 0
            for j in range(i, np.size(hitLogic) - 1):
                if (not hitLogic[j]):
                    countDuration = countDuration + 1
                if hitLogic[j + 1]:
                    break

            if countDuration < adjDurationThreshold:
                for j in range(i, i + countDuration):
                    hitLogic[j] = True

    return [hitLogic, baseline, noiseSigma]


def HitFinder(p,
              noiseSigmaInVolt,
              cfdThreshold=0.2,
              durationTheshold=10,
              adjDurationThreshold=10,
              nNoiseSigmaThreshold=2,
              sgFilter=True,
              sgWindow=15,
              sgPolyOrder=3):
    [hitLogic, baseline, noiseSigma] = DiscriminatorConditioning(p=p,
                                                                 noiseSigmaInVolt=noiseSigmaInVolt,
                                                                 durationTheshold=durationTheshold,
                                                                 adjDurationThreshold=adjDurationThreshold,
                                                                 nNoiseSigmaThreshold=nNoiseSigmaThreshold,
                                                                 sgFilter=sgFilter,
                                                                 sgWindow=sgWindow,
                                                                 sgPolyOrder=sgPolyOrder)

    hitStartIndexList = np.zeros(0)
    for i in range(1, np.size(hitLogic)):
        if ((not hitLogic[i - 1]) and hitLogic[i]) and hitLogic[i]:
            hitAmplitude = 1E100
            hitPeakIndex = i
            for j in range(i, np.size(hitLogic) - 1):
                if p[j] < hitAmplitude:
                    hitAmplitude = p[j]
                    hitPeakIndex = j
                if not hitLogic[j + 1]:
                    break
            ThresholdADC = baseline - (cfdThreshold * (baseline - hitAmplitude))

            hitStartIndex = i
            exactStartIndex = False
            for j in range(hitPeakIndex, 0, -1):
                if p[j] == ThresholdADC:
                    hitStartIndex = j
                    exactStartIndex = True
                    break
                if (p[j] < ThresholdADC and p[j - 1] > ThresholdADC):
                    hitStartIndex = j
                    break

            if exactStartIndex:
                hitStartIndexList = np.append(hitStartIndexList, hitStartIndex)
            else:
                if hitStartIndex >= 3:
                    V2 = p[hitStartIndex]
                    t2 = hitStartIndex
                    V1 = p[hitStartIndex - 1]
                    t1 = hitStartIndex - 1
                    m = (V2 - V1) / (t2 - t1)
                    extrapolatedHitStartIndex = ((ThresholdADC - V1) / m) + t1
                    hitStartIndexList = np.append(hitStartIndexList, extrapolatedHitStartIndex)

    return [hitStartIndexList, hitLogic, baseline, noiseSigma]
