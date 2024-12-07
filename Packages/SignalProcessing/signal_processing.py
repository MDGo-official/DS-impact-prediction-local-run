import pandas as pd
import numpy as np
if __debug__:
    import matplotlib.pyplot as plt
from scipy import signal
from scipy.fftpack import fft, fftfreq, fftshift, ifft
import sys

#2Do
class SignalProcessing:
    @classmethod
    def check_if_only_one_Fs(cls, df, timeCol=0):
        """
        Check that there is only one frequency in df
        :return: bool output
        """
        time = df.iloc[:, timeCol].to_numpy().astype('float32')
        unique_fs = np.unique(1 / np.round(np.diff(time[time > 0]), 5))
        return unique_fs.shape[0] == 1

    @classmethod
    def calc_fs(cls, df, timeCol=0):
        # first data-frame column is time [sec]

        # return np.round(np.mean(1 / ((df.diff(axis=0)).iloc[1:, timeCol])))
        if isinstance(df, pd.DataFrame):
            time = df.iloc[:, timeCol].to_numpy().astype('float32')
        elif isinstance(df, np.ndarray):
            time = df[:, timeCol].astype('float32')
        else:
            raise TypeError("input array should be either pd.DataFrame or np.ndarray")
        return np.unique(1 / np.round(np.diff(time[time > 0]), 5))[0]

    @classmethod
    def quantize(cls, df, dq=0.5, method='floor'):
        # dq - resolution , in [G]
        # method='floor'/'round'

        if method == 'floor':
            df.iloc[:, 1:] = (np.floor(df.iloc[:, 1:] / dq)) * dq
        elif method == 'round':
            df.iloc[:, 1:] = (np.round(df.iloc[:, 1:] / dq)) * dq
        return df

    @classmethod
    def insert_time_column(cls, df, sigFs=50, shiftTimeIndex=0):
        # Input: df with columns 'X','Y','Z'
        # this function adds time column in 'insertColInd' position. Time in [sec] calc. according to sample index

        df.insert(loc=0, column='Time_axis', value=((df.index - shiftTimeIndex) / sigFs))
        return df

    @classmethod
    def create_hpf(cls, fs, cutoffFreq, nCoeff=1023, debugPltFlag=0):
        # creates high-pass FIR with cutoff at cutoffFreq [Hz]
        # fs - sampling rate of the filter (equal to fs of the signal that will be filtered) [Hz]
        # cutoffFreq - in [Hz]
        ### HP FILTER
        if nCoeff % 2 == 0:
            print("Error,number of coeff. should be odd ")
            sys.exit(0)
        cutoff = cutoffFreq / (fs / 2)
        hpf = signal.firwin(nCoeff, cutoff, width=None, pass_zero=False)

        if debugPltFlag and __debug__:
            freqsVec = np.linspace(-fs / 2, fs / 2, hpf.shape[0])
            plt.figure(2)
            plt.plot(freqsVec, fftshift(np.abs(fft(hpf))))
            plt.xlabel('freq [Hz]')
            plt.title('HPF')
            plt.show()

        return hpf

    @classmethod
    def create_lpf(cls, fs, cutoffFreq, nCoeff=1024, debugPltFlag=0):
        # creates low-pass FIR with cutoff at cutoffFreq [Hz]
        # fs - sampling rate of the filter (equal to the signal that will be filtered)
        ### LP FILTER
        cutoff = cutoffFreq / (fs / 2)
        lpf = signal.firwin(nCoeff, cutoff, width=None)

        if debugPltFlag and __debug__:
            freqsVec = np.linspace(-fs / 2, fs / 2, lpf.shape[0])
            plt.figure(2)
            plt.plot(freqsVec, fftshift(np.abs(fft(lpf))))
            plt.xlabel('freq [Hz]')
            plt.title('LPF')
            plt.show()
        return lpf

    @classmethod
    def create_bpf(cls, fs, fStart, fStop, nCoeff=1023, debugPltFlag=0):

        if nCoeff % 2 == 0:
            print("Error,number of coeff. should be odd ")
            sys.exit(0)
        if fStart <= 0 or fStop >= fs / 2:
            print("Error, fStart must be grater than 0 , and fStop smaller than fs/2")
            sys.exit(0)
        else:
            cutoff = [fStart / (fs / 2), fStop / (fs / 2)]
            bpf = signal.firwin(nCoeff, cutoff, width=None, pass_zero=False)
            return bpf

    @classmethod
    def filter(cls, df, filter, mode='same'):
        # filtering the input signal (data frame columns) with filter (given in time, same fs as df]
        # first column of data frame is always time or sample number
        nColumns = df.shape[-1]
        if isinstance(df, pd.DataFrame):
            outSig = df.copy(deep=True)
            for iAxis in range(1, nColumns):
                outSig.iloc[:, iAxis] = np.convolve(df.iloc[:, iAxis], filter, mode)
        elif isinstance(df, np.ndarray):
            outSig = np.apply_along_axis(lambda x: np.convolve(x, filter, mode), 0, df)
            # for iAxis in range(1, nColumns):
            #     outSig[:, iAxis] = np.convolve(df[:, iAxis], filter, mode)
        else:
            raise TypeError("input data can be only pd.DataFrame or np.ndarray")
        return outSig

    @classmethod
    def plot_sig_vs_time_and_freq(cls, sig, sampFreq=None, newFigFlag=True, pltLabel=None, pltColor=None, pltLine='-',
                                  pltMarker='', pltSuptitle=None, pltIndex=None, name=None, pltShow=False,
                                  pltTimeXlim=None, xlimFreqPlt=None, pltTitle=''):

        # Signal is a data-frame. It's columns assumed to be [timeAxis or sampleIndex, carAcc-xAxis, carAcc-yAxis, carAcc-zAxis]
        if __debug__:
            if newFigFlag:
                if pltIndex is not None:
                    plt.figure(pltIndex)
                else:
                    plt.figure()
            nSamp = sig.shape[0]
            if sampFreq is None:
                sampFreq = cls.calc_fs(sig)
                xLabel = 'time[sec]'
            else:
                xLabel = '#sample'
            if pltColor is None:
                pltColor = np.random.uniform(0, 1, 3)

            sigFreqDomain = np.fft.fftshift(np.abs(np.fft.fft(sig.iloc[:, 1::], axis=0)), axes=0) / np.sqrt(nSamp)

            vFreqs = np.fft.fftshift(np.fft.fftfreq(nSamp)) * sampFreq

            for iAxis in range(1, 4):

                plt.subplot(2, 3, iAxis)
                plt.plot(sig.iloc[:, 0], sig.iloc[:, iAxis], color=pltColor, linestyle=pltLine, marker=pltMarker,
                        label=pltLabel)
                plt.xlabel(xLabel)

                if len(pltTitle) == 3:
                    plt.title(pltTitle[iAxis - 1])
                if pltTimeXlim is not None:
                    plt.xlim([pltTimeXlim[0], pltTimeXlim[1]])
                plt.subplot(2, 3, iAxis + 3)
                plt.plot(vFreqs, sigFreqDomain[:, iAxis - 1], color=pltColor, linestyle=pltLine, label=pltLabel)
                if xlimFreqPlt is not None:
                    plt.xlim((xlimFreqPlt[0], xlimFreqPlt[1]))

                plt.xlabel('freq. [Hz]')

                # if iAxis == 2:
                # plt.title('signal - freq. domain')
                # if xlimFreqPlt is not None:
                #     pltSuptitle = pltSuptitle + '  (fs=' + str(sampFreq) + 'Hz)'
            if pltLabel is not None:
                plt.legend()
            if pltSuptitle is not None:
                plt.suptitle(pltSuptitle)
            if pltShow:
                plt.show()

            if name is not None:
                plt.savefig(name)

    @classmethod
    def plot_sig_vs_time(cls, sig, sampFreq=None, newFigFlag=True, pltLabel=['X', 'Y', 'Z'], pltColor=['b', 'r', 'k'],
                         pltLine='-',
                         pltMarker='', pltSuptitle=None, pltIndex=None, name=None, pltShow=False,
                         pltTimeXlim=None, pltTitle='', pltSepAxis=False, pltYLabel='[G]'):
        ylim = [np.min((sig.values)[:, 1:]) - 1, np.max((sig.values)[:, 1:]) + 1]
        # Signal is a data-frame. It's columns assumed to be [timeAxis or sampleIndex, carAcc-xAxis, carAcc-yAxis, carAcc-zAxis]
        if __debug__:    
            if newFigFlag:
                if pltIndex is not None:
                    plt.figure(pltIndex)
                else:
                    plt.figure()
            nSamp = sig.shape[0]
            if sampFreq is None:
                sampFreq = cls.calc_fs(sig)
                xLabel = 'time[sec]'
            else:
                xLabel = '#sample'

            for iAxis in range(1, 4):
                # if pltSepAxis:
                #     plt.figure(iAxis)
                # else:
                #     plt.subplot(1, 3, iAxis)
                plt.plot(sig.iloc[:, 0], sig.iloc[:, iAxis], color=pltColor[iAxis - 1], linestyle=pltLine, marker=pltMarker,
                        label=pltLabel[iAxis - 1])
                plt.ylim([ylim[0], ylim[1]])
                plt.ylabel(pltYLabel)
                # if len(pltTitle) == 3:
                #     plt.title(pltTitle)
                plt.title(pltTitle)
                if pltTimeXlim is not None:
                    plt.xlim([pltTimeXlim[0], pltTimeXlim[1]])
                plt.xlabel(xLabel)
                if pltLabel is not None:
                    plt.legend()
            if pltSuptitle is not None:
                plt.suptitle(pltSuptitle)
            if pltShow:
                plt.show()

            if name is not None:
                plt.savefig(name)

    @classmethod
    def downsample(cls, dfSig, downsampFactor, initialSample):

        downsampSig = dfSig.iloc[initialSample::downsampFactor, ]
        downsampSig = downsampSig.set_index(np.arange(downsampSig.shape[0]))
        return downsampSig

    @classmethod
    def upsample(cls, dfSig, upsampFactor, inFs):
        # # df columns assumed to be [timeAxis or sampleIndex, carAcc-xAxis, carAcc-yAxis, carAcc-zAxis]
        maxLpfCoeff = 1024
        nSamp = dfSig.shape[0]
        upsampSig = pd.DataFrame(data=np.zeros([nSamp * upsampFactor, dfSig.shape[1]]), columns=dfSig.columns)
        upsampSig.iloc[0::upsampFactor, :] = dfSig.values
        upsampSig.iloc[:, 0] = np.real(upsampSig.iloc[:, 0])

        outFs = inFs * upsampFactor
        lpf = cls.create_lpf(outFs, 0.5 * outFs / upsampFactor, nCoeff=min(upsampSig.shape[0], maxLpfCoeff),
                              debugPltFlag=0)
        upsampFilt = cls.filter(upsampSig, lpf, mode='same')

        upsampFilt.iloc[:, 1::] = upsampFilt.iloc[:, 1::] * upsampFactor

        upsampFilt.iloc[:, 0] = np.arange(upsampFilt.shape[0]) * (1 / outFs) + upsampFilt.iloc[0, 0]

        return upsampFilt

    @classmethod
    def change_sampling_rate(cls, dfSig, inFs=None, outFs=None, sampRatioN=1, sampRatioD=2, initialSample=0):

        #  Converts the sampling rate of the dfSig to outFs if given. Else the sampling rate of the output signal
        #  = inFs*(sampRatioN/sampRatioD)

        # inSig is a data-frame. Its columns assumed to be [timeAxis or sampleIndex, carAcc-xAxis, carAcc-yAxis, carAcc-zAxis]
        # first column is time if inFs=None, otherwise assumed to be #sample

        # 2Do:
        # checking that df type is data frame

        if inFs is None:  # first axis is timeAxis
            inFs = int(np.round(1 / (dfSig.iat[1, 0] - dfSig.iat[0, 0])))
        assert type(inFs) == int, 'Input Frequency is not an integer'

        if outFs is not None:
            assert type(outFs) == int, 'Outputput Frequency is not an integer'
            gcdFactor = np.gcd(inFs, outFs)
            if gcdFactor == 1:
                print('outFreq has changed')
                if inFs > outFs:
                    sampRatioD = int(np.round(inFs / outFs))
                    sampRatioN = 1
                else:
                    sampRatioN = int(np.round(outFs / inFs))
                    sampRatioD = 1

            else:
                sampRatioD = int(inFs / gcdFactor)
                sampRatioN = int(outFs / gcdFactor)
        else:
            gcdFactor = np.gcd(sampRatioD, sampRatioN)
            sampRatioD = int(sampRatioD / gcdFactor)
            sampRatioN = int(sampRatioN / gcdFactor)

        if sampRatioN > 1:
            assert ((inFs % sampRatioD) == 0)
            dfSigUS = cls.upsample(dfSig, sampRatioN, int(inFs))
        else:
            dfSigUS = dfSig
            dfSigUS = dfSigUS.set_index(np.arange(dfSigUS.shape[0]))
        if sampRatioD > 1:
            dfSigDS = cls.downsample(dfSigUS, sampRatioD, initialSample)
            dfSigDS = dfSigDS.set_index(np.arange(dfSigDS.shape[0]))

        else:
            dfSigDS = dfSigUS

        outFs = inFs * sampRatioN / sampRatioD

        return dfSigDS, outFs

    @classmethod
    def clipping(cls, dfSig, clipTh, sensorsColInd=[1, 2, 3]):
        dfSigClipped = dfSig.copy()
        dfSigClipped.iloc[:, sensorsColInd] = dfSig.iloc[:, sensorsColInd].clip(-np.abs(clipTh), np.abs(clipTh))
        return dfSigClipped

    @classmethod
    def smooth_dataset_filter(cls, df, cutoffFreq, nCoeff =None):
        inFs = cls.calc_fs(df)
        if nCoeff is None:
            nCoeff = min(512, df.shape[0] // 2 * 2)
        lpf = cls.create_lpf(inFs, cutoffFreq, nCoeff)
        return cls.filter(df, lpf, mode='same')

    @classmethod
    def _find_max_energy_index(cls, df):
        if isinstance(df, pd.DataFrame):
            return np.argmax(np.linalg.norm(df.to_numpy()[:, 1:], axis=1))
        elif isinstance(df, np.ndarray):
            return np.argmax(np.linalg.norm(df[:, 1:], axis=1))

    @classmethod
    def alignment_signal(cls, df, size=240):
        if isinstance(df, pd.DataFrame):
            df_new = np.pad(df.to_numpy(), ((size, size), (0, 0)), mode='constant', constant_values=0)
            idx = cls._find_max_energy_index(df_new)
            df_new = df_new[idx - int(size / 2):idx + int(size / 2), :]
            df_new = pd.DataFrame(df_new, columns=df.columns)
        elif isinstance(df, np.ndarray):
            df_new = np.pad(df, ((size, size), (0, 0)), mode='constant', constant_values=0)
            idx = cls._find_max_energy_index(df_new)
            df_new = df_new[idx - int(size / 2):idx + int(size / 2), :]
        else:
            raise TypeError("input data can be only pd.DataFrame or np.ndarray")
        return df_new

    @classmethod
    def align_axes(cls, data, input_orientation, output_orientation='FRD', sensors=['X', 'Y', 'Z']):
        # orientation is represented as a 3 char (uppercase) string
        # first char represents X Axis and takes either (F)ront or (R)ear
        # second char represents X Axis and takes either (R)ight or (L)eft
        # third char represents X Axis and takes either (U)p or (D)own

        if len(input_orientation) != 3 or len(output_orientation) != 3:
            print("orientation must be exactly 3 chars long")
            sys.exit(1)
        if input_orientation[0] not in ['F', 'R']:
            print("Error, X axis orientation must take F or R, got %s" % input_orientation[0])
            sys.exit(1)
        if input_orientation[1] not in ['R', 'L']:
            print("Error, X axis orientation must take R or L, got %s" % input_orientation[1])
            sys.exit(1)
        if input_orientation[2] not in ['U', 'D']:
            print("Error, X axis orientation must take U or D, got %s" % input_orientation[2])
            sys.exit(1)

        if input_orientation[0] != output_orientation[0]:
            data[sensors[0]] = data[sensors[0]] * -1
        if input_orientation[1] != output_orientation[1]:
            data[sensors[1]] = data[sensors[1]] * -1
        if input_orientation[2] != output_orientation[2]:
            data[sensors[2]] = data[sensors[2]] * -1

        return data

    @classmethod
    def scale(cls, df, ratio, columns):
        df[columns] = df[columns] * ratio
        return df

    @classmethod
    def shift(cls, df, vShift, columns):
        if type(vShift) is list:
            vShift = np.array(vShift)
        if vShift.shape[0] == 1:
            df[columns] = df[columns] + vShift
        else:
            if vShift.shape[0] == df[columns].shape[-1]:
                for iCol in range(df[columns].shape[1]):
                    df[columns[iCol]] += vShift[iCol]
            else:
                print("Error in shift vector length")
                sys.exit(1)
        return df

    @classmethod
    def multiple_case_recognition(cls, df, height=4, distance=50):
        """
        distance - in [samples]
        height - same units as the df data
        """
        from scipy.signal import hilbert, find_peaks

        min_idx = [0, ]
        S = np.linalg.norm(df.iloc[:, 1:3].values, axis=1)
        analytic_signal = hilbert(S)
        env = np.abs(analytic_signal)

        peaks, _ = find_peaks(env, height=height, distance=distance)

        if len(peaks) > 1:
            df_list = []
            for i in range(len(peaks) - 1):
                idx_min = peaks[i] + np.argmin(env[peaks[i]:peaks[i + 1]])
                min_idx.append(idx_min)
            min_idx.append(df.shape[0])
            for i in range(len(min_idx) - 1):
                df_list.append(df.iloc[min_idx[i]:min_idx[i + 1], :])

            return df_list
        else:
            return [df]

    @staticmethod
    def offset_to_bit(offset,step=1/256):
        bit_offset = [] 
        for v in offset:
            bit_offset.append(int(v/step))
        return bit_offset
    
    @staticmethod
    def bit_to_offset(bit_offset, step = 1/256):
        offset = [] 
        for v in bit_offset:
            offset.append(v*step)
        return offset

    @classmethod
    def rotate_signal(cls, df, operational_mat, output_orientation, input_orientation='FLU',
                      sensors=['Acc_X', 'Acc_Y', 'Acc_Z'], offset=[0, 0, 0]):
        """
        :param df: Sense dataframe containing all sensors
        :param operational_mat:
        :param output_orientation: [string] FRD,...
        :param input_orientation: [string] FLU,...
        :param sensors: [array] column names of the acceleration sensors to be rotated
        :param offset: [array] x, y, z vertical offset
        :return: df with just the rotated acc sensors
        """
        if type(operational_mat) is list:
            operational_mat = np.array(operational_mat)
        offset = SignalProcessing.bit_to_offset(offset)
        if isinstance(df, pd.DataFrame):
            df = df.loc[:, sensors]
            df = SignalProcessing.shift(df, -np.array(offset), sensors)
            df.loc[:, sensors] = df.to_numpy() @ operational_mat.T
            df = cls.align_axes(df, input_orientation, output_orientation, sensors=sensors)
        else:
            raise TypeError("input data can only be pd.DataFrame")
        return df


class Pipeline():
    def __init__(self, target_freq, smooth_freq=None, multCaseHeight=5, multCaseDist=50):
        self.target_freq = target_freq
        self.smooth_freq = smooth_freq
        self.multCaseHeight = multCaseHeight
        self.multCaseDist = multCaseDist
        self.sp = SignalProcessing()

    def run(self, df, orig_axes, sensor_columns):

        sensors = list(sensor_columns.split(','))

        df = self.sp.align_axes(df, orig_axes)
        # self.sp.plot_sig_vs_time_and_freq(aligned_df, name='axis-aligned.png')

        if self.smooth_freq is None:
            self.smooth_freq = self.target_freq / 2
        df = self.sp.smooth_dataset_filter(df, self.smooth_freq)

        df = self.sp.shift(df, [1], sensors[-1])

        df, _ = self.sp.change_sampling_rate(df, outFs=self.target_freq)

        df_list = self.multiple_case_recognition(df, self.multCaseHeight, self.multCaseDist)

        signal_list = []
        for i, df1 in enumerate(df_list):
            df1 = self.alignment_signal(df1)
            signal_list.append(df1)

        return signal_list










