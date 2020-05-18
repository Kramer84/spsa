import openturns 
import numpy 


'''Here we are going to generate samples for the Monte-Carlo experiement,
knowing that the variables that we are generating are a mix of random-variables
representing Physical variables and random-variables used to reconstruct stochastic
field. 
This has little implication of the Latin Hypercube sampling itself, but will change the
way we shuffle to retrieve the conditional variances.

To know which variable belongs to which type of physical quantity, this class works will
work exclusively with the NdGaussianProcessSensitivity.OpenturnsPythonFunctionWrapper
, from which we need the KLComposedDistribution attribute, as well as the inputVarNames
and inputVarNamesKL. Later, this can later be modified to work with other inputs as well.
'''


class NdGaussianProcessExperiment(object):
    '''Class to generate experiments for the sensitivity analysis.

    This uses the fact that we have fields decomposed in a series of
    random variables (with karhunen loeve), but that only the conditional
    variance knowing all of those variables is needed, and that there is no
    physical meaning to the conditional variance knowing only one of those
    decomposed variables.

    This generation begins similarly to other experiments, generating a big
    sample of size 2*N that we decompose in two samples A and B of size N.
    This generation can be done entirely randomely, or using specific sampling methods,
    as LHS, LowDiscrepancySequence or SimulatedAnnealingLHS.

    The difference lies in the way we 'shuffle' our two samples. For a classical RV
    representing a mono-dimensional physical quantitiy, we take the column representing this
    quantity in the matrix B and replace the correspoding values in A, thus creating a new matrix,
    that we append to our samples. But in the case of a gaussian field represented by a series
    of random variables, we take all those variables in B and put them in A, but we do not take them
    individually, as in a classical experiment.

    Generation options :
    1 : Random
    2 : LHS
    3 : LowDiscrepancySequence
    4 : SimulatedAnnealingLHS
    '''

    def __init__(self, sampleSize = None, OTPyFunctionWrapper = None, generationType = 1):
        self.OTPyFunctionWrapper  = None
        self.composedDistribution = None
        self.inputVarNames        = list()
        self.inputVarNamesKL      = list()
        self.N                    = None
        self._genType             = 1
        print('Generation types:\n1 : Random (default)\n2 : LHS\n3 : LowDiscrepancySequence\n4 : SimulatedAnnealingLHS')
        if sampleSize is not None:          self.setSampleSize(sampleSize)
        if OTPyFunctionWrapper is not None: self.setOTPyFunctionWrapper(OTPyFunctionWrapper)
        if generationType is not None:      self.setGenType(generationType)
        # here we come to the samples
        self.sample_A             = None
        self.sample_B             = None
        self.dataMixSamples       = list()
        self.experimentSample     = None

    def generate(self, **kwargs):
        assert (self.OTPyFunctionWrapper is not None) and \
               (self.N is not None) , "Please intialise sample size and PythonFunction wrapper"
        self.generateSample(**kwargs)
        self.getDataFieldAndRV()
        self.getExperiment()
        return self.experimentSample

    def setSampleSize(self, N):
        assert type(N) is int, "Sample size can only be positive integer"
        if self.N is None :
            self.N = N 
        else :
            self.N        = N 
            self.sample_A = self.sample_B = self.experimentSample = None

    def setOTPyFunctionWrapper(self, OTPyFunctionWrapper):
        self.OTPyFunctionWrapper  = OTPyFunctionWrapper
        self.inputVarNames        = self.OTPyFunctionWrapper.inputVarNames
        self.inputVarNamesKL      = self.OTPyFunctionWrapper.inputVarNamesKL
        self.composedDistribution = self.OTPyFunctionWrapper.KLComposedDistribution
        self.getDataFieldAndRV()

    def setGenType(self, arg):
        arg = int(arg)
        if arg not in [1,2,3,4]:
            print('Generation types:\n1 : Random (default)\n2 : LHS\n3 : LowDiscrepancySequence\n4 : SimulatedAnnealingLHS')
            raise TypeError
        self._genType = arg

    def getDataFieldAndRV(self):
        '''Here we analyse the names of the variables, to know which columns
        belong to RVs or Fields
        '''
        n_vars              = len(self.inputVarNames)
        n_vars_KL           = len(self.inputVarNamesKL)
        self.dataMixSamples =  list()
        for i in range(n_vars):
            k           = 0
            timesInList = 0
            jump        = self.ramp(sum(self.dataMixSamples)-i)
            while self.inputVarNamesKL[i+k+jump].startswith(self.inputVarNames[i]):
                timesInList += 1
                k           += 1
                if i+k+jump == n_vars_KL: break   
            self.dataMixSamples.append(timesInList)

    def getExperiment(self):
        n_vars = len(self.inputVarNames)
        N = self.N
        self.experimentSample            = numpy.tile(self.sample_A,[2+n_vars,1])
        self.experimentSample[N:2*N,...] = self.sample_B
        jump    = 2*N
        jumpDim = 0
        for i in range(n_vars):
            self.experimentSample[jump+N*i:jump+N*(i+1), jumpDim:jumpDim+self.dataMixSamples[i]] = \
                    self.sample_B[...,                   jumpDim:jumpDim+self.dataMixSamples[i]]
            jumpDim += self.dataMixSamples[i]

    def ramp(self,X):
        if X >= 0: return X
        else:      return 0

    def generateSample(self, **kwargs):
        distribution = self.composedDistribution
        method       = self._genType
        methodDict   = {1:'Random (default)', 2:'LHS', 3:'LowDiscrepancySequence', 4:'SimulatedAnnealingLHS'}
        print('Choosen generation method is',methodDict[method])
        N2           = 2*self.N 
        if   method is 1 :
            sample = distribution.getSample(N2)
        elif (method is 2) or (method is 4) :
            lhsExp = openturns.LHSExperiment(distribution, 
                                             N2, 
                                             False, #alwaysShuffle
                                             True) #randomShift
            if method is 2 :
                sample = lhsExp.generate()
            if method is 4 :
                lhsExp.setAlwaysShuffle(True)
                if 'SpaceFilling' in kwargs :
                    if kwargs['SpaceFilling'] is 'SpaceFillingC2':      spaceFill = openturns.SpaceFillingC2
                    if kwargs['SpaceFilling'] is 'SpaceFillingMinDist': spaceFill = openturns.SpaceFillingMinDist
                    if kwargs['SpaceFilling'] is 'SpaceFillingPhiP':    
                        spaceFill = openturns.SpaceFillingPhiP
                        if 'p' in kwargs : 
                            if (type(kwargs['p']) is int) or (type(kwargs['p']) is float) : p = int(kwargs['p'])
                            else : 
                                print('Wrong type for p parameter in SpaceFillingPhiP algorithm, setting to default p = 50')
                                p = 50
                        else : 
                            print('undefined parameter p in SpaceFillingPhiP algorithm, setting to default p = 50')
                            p = 50
                else : 
                    print("undefined parameter 'SpaceFilling', setting to default 'SpaceFillingC2'")
                    spaceFill = openturns.SpaceFillingC2
                if 'TemperatureProfile' in kwargs : 
                    if kwargs['TemperatureProfile'] is 'GeometricProfile': geomProfile = openturns.GeometricProfile(10.0, 0.95, 2000) #Default value
                    if kwargs['TemperatureProfile'] is 'LinearProfile':    geomProfile = openturns.LinearProfile(10.0, 100)
                else :
                    print("undefined parameter 'TemperatureProfile', setting default GeometricProfile")
                    geomProfile = openturns.GeometricProfile(10.0, 0.95, 2000)
                optimalLHSAlgorithm = openturns.SimulatedAnnealingLHS(lhsExp, geomProfile, spaceFill())
                sample = optimalLHSAlgorithm.generate()
        elif method is 3 : 
            restart = True 
            if 'sequence' in kwargs :
                if kwargs['sequence'] == 'Faure':         seq = openturns.FaureSequenc 
                if kwargs['sequence'] == 'Halton':        seq = openturns.HaltonSequence
                if kwargs['sequence'] == 'ReverseHalton': seq = openturns.ReverseHaltonSequence
                if kwargs['sequence'] == 'Haselgrove':    seq = openturns.HaselgroveSequence
                if kwargs['sequence'] == 'Sobol':         seq = openturns.SobolSequence
            else :
                print('sequence undefined for low discrepancy experiment, setting default to SobolSequence')
                print("possible vals for 'sequence' argument:\n    ['Faure','Halton','ReverseHalton','Haselgrove','Sobol']")
                seq = openturns.SobolSequence
            LDExperiment = openturns.LowDiscrepancyExperiment(seq(), 
                                                              distribution,
                                                              N2,
                                                              True)
            sample = LDExperiment.generate()
        sample = numpy.array(sample)
        self.sample_A = sample[:self.N,:]
        self.sample_B = sample[self.N:,:]