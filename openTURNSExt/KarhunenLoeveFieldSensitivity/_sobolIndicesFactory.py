import openturns as ot 
from collections import Iterable, UserList, Sequence
from copy import copy, deepcopy
from numbers import Complex, Integral, Real, Rational, Number

__all__ = ['SobolKarhunenLoeveFieldSensitivityAlgorithm']


def all_same(items=None):
    #Checks if all items of a list are the same
    return all(x == items[0] for x in items)

def atLeastList(elem=None):
    if isinstance(elem, (Iterable, Sequence, list)) and not isinstance(elem,(str,bytes)):
        return list(elem)
    else : 
        return [elem]

def list_(*args): return list(args)

def zip_(*args): return map(list_, *args)


class SobolKarhunenLoeveFieldSensitivityAlgorithm(ot.SaltelliSensitivityAlgorithm):
    '''Pure opentTURNS implementation of the sobol indices algorithm
    in the case where the design of the experiment was generated 
    using a field function that has been wrapped using the 
    KarhunenLoeveGeneralizedWrapper. 

    Note
    ----
    There should be no difference at all with the real 
    SaltelliSensitivityAlgorithm implementation, only that the orihinal 
    implementation checks the input and output desgin's dimension and 
    raises an error if the dimensions don't match. 
    '''
    def __init__(self, inputDesign=None, outputDesign=None, N=0, 
            estimator = ot.SaltelliSensitivityAlgorithm(), computeSecondOrder=False):
        self.inputDesign = inputDesign
        self.outputDesign = atLeastList(outputDesign)
        if len(self.outputDesign) > 0 and outputDesign is not None:
            assert all_same([len(
                self.outputDesign[i]) for i in range(len(self.outputDesign))])
        self.N = int(N)
        self.size = None
        self.__nOutputs__ = 0
        self.__computeSecondOrder__ = computeSecondOrder
        self.__visibility__ = True
        self.__shadowedId__ = 0
        self.__name__ = 'Unnamed'
        self.inputDescription = None
        self.__nSobolIndices__ = None
        self.__Meshes__ = list()
        self.__Classes__ = list()
        self.__BootstrapSize__ = None
        self.flatOutputDesign = list()
        self.__centeredOutputDesign__ = list()
        self.__preProcessedOutputDesign__ = list()
        self.__setDefaultState__()
        self.estimator = estimator
        self.__results__ = list()

    def DrawCorrelationCoefficients(self, *args):
        self.__fastResultCheck__()
        print('Drawing is not yet implemented')
        raise NotImplementedError


    def DrawImportanceFactors(self, *args):
        self.__fastResultCheck__()
        print('Drawing is not yet implemented')
        raise NotImplementedError


    def DrawSobolIndices(self, *args):
        self.__fastResultCheck__()
        print('Drawing is not yet implemented')
        raise NotImplementedError


    def draw(self, *args):
        self.__fastResultCheck__()
        print('Drawing is not yet implemented')
        raise NotImplementedError

    def getAggregatedFirstOrderIndices(self):
        self.__fastResultCheck__()
        aggFO_indices = list()
        for i in range(self.__nOutputs__):
            aggFO_indices.append(ot.PointWithDescription(self.__results__[i].getAggregatedFirstOrderIndices()))
            aggFO_indices[i].setName('Sobol_'+self.outputDesign[i].getName())
            aggFO_indices[i].setDescription([self.outputDesign[i].getName()+'_'+self.inputDescription[j] for j in range(self.__nSobolIndices__)])
        return aggFO_indices 

    def getAggregatedTotalOrderIndices(self):
        self.__fastResultCheck__()
        aggTO_indices = list()
        for i in range(self.__nOutputs__):
            aggTO_indices.append(ot.PointWithDescription(self.__results__[i].getAggregatedTotalOrderIndices()))
            aggTO_indices[i].setName('Sobol_'+self.outputDesign[i].getName())
            aggTO_indices[i].setDescription([self.outputDesign[i].getName()+'_'+self.inputDescription[j] for j in range(self.__nSobolIndices__)])
        return aggTO_indices 

    def getBootstrapSize(self):
        return self.__BootstrapSize__

    def getClassName(self):
        return self.__class__.__name__

    def getConfidenceLevel(self):
        return self.ConfidenceLevel 

    def getFirstOrderIndices(self):
        self.__fastResultCheck__()
        FO_indices = list()
        nMarginals = [self.__centeredOutputDesign__[i].getDimension() for i in range(self.__nOutputs__)]
        for i in range(self.__nOutputs__):
            FO_point_list = list()
            for j in range(nMarginals[i]):
                FO_point_list.append(self.__results__[i].getFirstOrderIndices(j))
            FO_point_list = list(zip_(*FO_point_list))
            FO_indices.append([self.__toBaseDataFormat__(ot.Point(FO_point_list[k]), i) for k in range(self.__nSobolIndices__)])
            [FO_indices[i][k].setName('Sobol_'+self.outputDesign[i].getName()+'_'+self.inputDescription[k]) for k in range(self.__nSobolIndices__)]
        return FO_indices 

    def getFirstOrderIndicesDistribution(self):
        self.__fastResultCheck__()
        FO_indices_distribution = list()
        for i in range(self.__nOutputs__):
            FO_indices_distribution.append(self.__results__[i].getFirstOrderIndicesDistribution())
            FO_indices_distribution[i] = self.__toBaseDataFormat__(FO_indices_distribution[i], i)
            FO_indices_distribution[i].setName(self.outputDesign[i].getName())
            FO_indices_distribution[i].setDescription([self.outputDesign[i].getName()+'_'+self.inputDescription[j] for j in range(self.__nSobolIndices__)])
        return FO_indices_distribution 

    def getFirstOrderIndicesInterval(self):
        self.__fastResultCheck__()
        FO_indices_interval = list()
        for i in range(self.__nOutputs__):
            FO_indices_interval.append(self.__results__[i].getFirstOrderIndicesInterval())
        [FO_indices_interval[i].setName('Bounds_Sobol_'+self.outputDesign[i].getName()) for i in range(self.__nOutputs__)]  
        return FO_indices_interval

    def getId(self):
        return id(self)

    def getName(self):
        return self.__name__

    def getSecondOrderIndices(self):
        if self.__computeSecondOrder__ == True : 
            self.__fastResultCheck__()
            SO_indices = list()
            nMarginals = [self.__centeredOutputDesign__[i].getDimension() for i in range(self.__nOutputs__)]
            for i in range(self.__nOutputs__):
                SO_point_list = list()
                for j in range(nMarginals[i]):
                    SO_point_list.append(self.__results__[i].getSecondOrderIndices(j))
                SO_point_list = list(zip_(*SO_point_list))
                SO_indices.append([self.__toBaseDataFormat__(ot.Point(SO_point_list[k]), i) for k in range(self.__nSobolIndices__)])
                [SO_indices[i][k].setName('SecondOrderSobol_'+self.outputDesign[i].getName()+'_'+self.inputDescription[k]) for k in range(self.__nSobolIndices__)]
            return SO_indices
        else : 
            print('The second order indices flag is not set to true.')
            print('Have you passed the right sample to make this calculus?')
            return None

    def getShadowedId(self):
        return self.__shadowedId__

    def getTotalOrderIndices(self):
        self.__fastResultCheck__()
        TO_indices = list()
        nMarginals = [self.__centeredOutputDesign__[i].getDimension() for i in range(self.__nOutputs__)]
        for i in range(self.__nOutputs__):
            TO_point_list = list()
            for j in range(nMarginals[i]):
                TO_point_list.append(self.__results__[i].getTotalOrderIndices(j))
            TO_point_list = list(zip_(*TO_point_list))
            TO_indices.append([self.__toBaseDataFormat__(ot.Point(TO_point_list[k]), i) for k in range(self.__nSobolIndices__)])
            [TO_indices[i][k].setName('TotalOrderSobol_'+self.outputDesign[i].getName()+'_'+self.inputDescription[k]) for k in range(self.__nSobolIndices__)]
        return TO_indices

    def getTotalOrderIndicesDistribution(self):
        self.__fastResultCheck__()
        TO_indices_distribution = list()
        for i in range(self.__nOutputs__):
            TO_indices_distribution.append(self.__results__[i].getTotalOrderIndicesDistribution())
            TO_indices_distribution[i] = self.__toBaseDataFormat__(TO_indices_distribution[i], i)
            TO_indices_distribution[i].setName(self.outputDesign[i].getName())
            TO_indices_distribution[i].setDescription([self.outputDesign[i].getName()+'_'+self.inputDescription[j] for j in range(self.__nSobolIndices__)])
        return TO_indices_distribution 

    def getTotalOrderIndicesInterval(self):
        self.__fastResultCheck__()
        TO_indices_interval = list()
        for i in range(self.__nOutputs__):
            TO_indices_interval.append(self.__results__[i].getTotalOrderIndicesInterval())
        [TO_indices_interval[i].setName('BoundsTotalOrderSobol_'+self.outputDesign[i].getName()) for i in range(self.__nOutputs__)]  
        return TO_indices_interval

    def getUseAsymptoticDistribution(self):
        self.__fastResultCheck__()
        useAsymptotic = list()
        for i in range(self.__nOutputs__):
            useAsymptotic.append(self.__results__[i].getUseAsymptoticDistribution())
            useAsymptotic[i] = self.__toBaseDataFormat__(useAsymptotic[i], i)
        return useAsymptotic 

    def getVisibility(self):
        return self.__visibility__

    def hasName(self):
        if self.__name__ != 'Unnamed' and len(self.__name__)>0:
            return True 
        else :
            return False

    def setBootstrapSize(self, bootstrapSize):
        self.__BootstrapSize__ = bootstrapSize

    def setConfidenceLevel(self, confidenceLevel):
        self.ConfidenceLevel = confidenceLevel

    def setDesign(self, inputDesign=None, outputDesign=None, N=0):
        outputDesign = atLeastList(outputDesign)
        assert all_same([len(outputDesign[i]) for i in range(len(outputDesign))])
        assert (isinstance(N,(int, Integral)) and N>=0)
        self.inputDesign = inputDesign
        self.outputDesign = atLeastList(outputDesign)
        self.N = int(N)
        if self.outputDesign is not None and self.N > 0:
            self.__setDefaultState__()

    def setEstimator(self, estimator):
        self.estimator = estimator 

    def setName(self, name):
        self.__name__ = name

    def setShadowedId(self, shadowedId):
        self.__shadowedId__ = shadowedId

    def setUseAsymptoticDistribution(self,useAsymptoticList=False):
        if isinstance(useAsymptoticList, bool):
            asymptoticList = [useAsymptoticList]*self.__nOutputs__
        elif isinstance(useAsymptoticList, (Sequence,Iterable)):
            assert len(useAsymptoticList)==self.__nOutputs__
            asymptoticList = useAsymptoticList
        else : 
            raise NotImplementedError
        self.__fastResultCheck__()
        try:
            for i in range(self.__nOutputs__):
                self.__results__[i].setUseAsymptoticDistribution(asymptoticList[i])
        except TypeError :
            print('Check the function arguments. Must be of type Bool or list of Bools')
            raise TypeError

    def setVisibility(self, visible):
        self.__visibility__ = visible

    def __setDefaultState__(self):
        try : 
            if self.outputDesign is not None and self.N > 0 :
                self.size = len(self.outputDesign[0])
                self.__nOutputs__ = len(self.outputDesign)
                if self.__computeSecondOrder__== True : 
                    self.__nSobolIndices__ = (int(self.size / self.N) - 2)/2
                    try : 
                        assert (int(self.size / self.N) - 2) % 2 == 0
                    except : 
                        print('The outputDesign you have passed does not satisfy')
                        print('The minimum requirements to do the sensitivity analysis')
                        print('The total sample size should be : tot = N * (2 + d) = 2*N + 2*d*N') 
                        print('In this case : tot-2*N = 2*d*N MUST be divisible by two')
                else :
                    self.__nSobolIndices__ = int(self.size / self.N) - 2
                    print('Warning : Always pass the computeSecondOrder argument')
                    print('if you also pass the data to compute it')
                    print('Otherwise, the behavior will be unreliable')
                self.__getDataOutputDesign__()
                self.__flattenOutputDesign__()
                self.__centerOutputDesign__()
                self.__preProcessOutputDesign__()                
                self.__confirmationMessage__()
                self.__setDefaultName__()
            else : 
                pass
        except Exception as e :
            print('Something unexpected happened')
            raise e

    def __getDataOutputDesign__(self):
        self.__Meshes__.clear()
        self.__Classes__.clear()
        for output in self.outputDesign :
            try :
                self.__Classes__.append(output.__class__)
                self.__Meshes__.append(output.getMesh())
            except AttributeError :
                self.__Meshes__.append(None)

    def __flattenOutputDesign__(self):
        self.flatOutputDesign.clear()
        for outputDes in self.outputDesign : 
            if isinstance(outputDes, (ot.Point, ot.Sample)):
                self.flatOutputDesign.append(outputDes)
            if isinstance(outputDes, ot.ProcessSample):
                sample, mesh = self.__splitProcessSample__(outputDes)
                self.flatOutputDesign.append(sample)

    def __splitProcessSample__(self, processSample):
        mesh = processSample.getMesh()
        n_vertices = mesh.getVerticesNumber()
        sample = ot.Sample(self.size, n_vertices)
        for i in range(self.size):
            field = processSample.getField(i)
            vals = field.getValues()
            vals = list([vals[i][0] for i in range(n_vertices)])
            sample[i] = vals
        return sample, mesh

    def __centerOutputDesign__(self):
        design_cpy = [self.flatOutputDesign[i][:] for i in range(self.__nOutputs__)]
        self.__centeredOutputDesign__.clear()
        for design_elem in design_cpy :
            if isinstance(design_elem, ot.Point):
                mean = sum(design_elem) / design_elem.getDimension()
                design_elem -= [mean] * design_elem.getDimension()
                self.__centeredOutputDesign__.append(deepcopy(design_elem))
            elif isinstance(design_elem, ot.Sample):
                mean = design_elem.computeMean()
                design_elem -= mean
                self.__centeredOutputDesign__.append(deepcopy(design_elem))
            else : 
                raise NotImplementedError

############################################################################################################################
    def __preProcessOutputDesign__(self):                                                                                 ##
        flatSampleA = [self.__centeredOutputDesign__[i][:self.N] for i in range(self.__nOutputs__)]                       ##
        flatSampleB = [self.__centeredOutputDesign__[i][self.N:2*self.N] for i in range(self.__nOutputs__)]               ##
        psi_fo, psi_to = self.__symbollicSaltelliFormula__(1)                                                             ##
        self.__preProcessedOutputDesign__.clear()                                                                         ##
        for i_output in range(self.__nOutputs__):                                                                         ##
            inputOneOutput = []                                                                                           ##
            for sobolIdx in range(self.__nSobolIndices__):                                                                ##
                inputOneIndice = []                                                                                       ##
                inputOneIndice.append(flatSampleA[i_output])                                                              ##
                inputOneIndice.append(flatSampleB[i_output])                                                              ##
                inputOneIndice.append(self.__centeredOutputDesign__[i_output][(2+sobolIdx)*self.N : (3+sobolIdx)*self.N]) ##
                inputOneIndice.append(psi_fo)                                                                             ##
                inputOneIndice.append(psi_to)                                                                             ##
                inputOneOutput.append(tuple(inputOneIndice))                                                              ##
            self.__preProcessedOutputDesign__.append(inputOneOutput)                                                      ##
############################################################################################################################

    def __confirmationMessage__(self):
        def getDim(pointOrSample):
            if isinstance(pointOrSample, ot.Point):
                return 1
            elif isinstance(pointOrSample, ot.Sample):
                return pointOrSample.getDimension()
            else :
                return pointOrSample.getDimension()
        dims = ', '.join([str(getDim(self.flatOutputDesign[i])) for i in range(self.__nOutputs__)])
        print(
'There are {} indices to get for {} outputs with dimensions {} each.'.format(
            self.__nSobolIndices__, self.__nOutputs__, dims))

    def __setDefaultName__(self):
        if self.inputDesign is None :
            desc = ot.Description.BuildDefault(self.__nSobolIndices__, 'X')
            self.inputDescription = desc
        elif all_same(self.inputDesign.getDescription()) == True:
            desc = ot.Description.BuildDefault(self.__nSobolIndices__, 'X')
            self.inputDescription = desc
        elif all_same(self.inputDesign.getDescription()) == False:
            inputDescription = self.inputDesign.getDescription()
            SobolIndicesName = []
            inputWOutLastChar = [inputDescription[i][:-1] for i in range(len(inputDescription))]
            SobolIndicesName = []
            for x in inputWOutLastChar:
                if x not in SobolIndicesName:
                    SobolIndicesName.append(x)
            print('SobolIndicesName',SobolIndicesName)
            self.inputDescription = SobolIndicesName

    def __fastResultCheck__(self):
        if not len(self.__results__)>0 : 
            try : 
                self.__solve__()
            except AssertionError :
                print('You need samples to work on. Check doc')
                raise AssertionError

    def __solve__(self):
        assert self.estimator is not None, "First initialize the estimator (Jansen, Saltelli, etc.)"
        assert len(self.outputDesign) > 0, "You have to pass a Sample to work on"
        assert self.outputDesign[0] is not None, "You have to pass a Sample to work on"
        dummyInputSample = ot.Sample(self.size, self.__nSobolIndices__)
        dummyInputSample.setDescription(self.inputDescription)
        self.__results__.clear()
        outputDesigns = self.__centeredOutputDesign__
        for i in range(len(outputDesigns)):
            estimator = self.estimator.__class__()
            _input = dummyInputSample[:]
            self.__results__.append(estimator)
            self.__results__[i].setDesign(_input, outputDesigns[i], self.N)
            self.__results__[i].setName(self.inputDescription[i])

    def __toBaseDataFormat__(self, data, idx):
        mesh = self.__Meshes__[idx]
        if isinstance(data, ot.Point) :
            if mesh is not None :
                dataBaseFormat = ot.Field(mesh, [[dat] for dat in data])
                return dataBaseFormat
            else : 
                return data 
        elif isinstance(data, ot.Interval) :
            lowBounds = data.getLowerBound()
            upperBounds = data.getUpperBound()
            if mesh is not None :
                lowBoundsBaseFormat = ot.Field(mesh, [[bnd] for bnd in lowBounds])
                upperBoundsBaseFormat = ot.Field(mesh, [[bnd] for bnd in upperBounds])
                return lowBoundsBaseFormat, upperBoundsBaseFormat
            else : 
                return data
        elif isinstance(data, ot.Distribution):
            print('Cannot convert distribution to field, dimensional correlation lost.')
            return data 
        elif isinstance(data, (bool, int, float)):
            return data 
        else : 
            raise NotImplementedError
 
#######################################################################################
    def __symbollicSaltelliFormula__(self, N : int) :                                ##
        '''Method to create the symbolic python saltelli function                    ##
                                                                                     ##
         Note                                                                        ##
        ----                                                                         ##
        N > 1 only in the case of aggregated indices                                 ##
                                                                                     ##
         Arguments                                                                   ##
        ---------                                                                    ##
        N : int                                                                      ##
            number of nominators and denominators                                    ##
                                                                                     ##
         Returns                                                                     ##
        -------                                                                      ##
        psi_fo : ot.SymbolicFunction                                                 ##
            first order symbolic function                                            ##
        psi_to : ot.SymbolicFunction                                                 ##
            total order symbolic function                                            ##
        '''                                                                          ##
        x, y = (ot.Description.BuildDefault(N, 'X'),                                 ##
                ot.Description.BuildDefault(N, 'Y'))                                 ##
        # in order X0, Y0, X1, Y1                                                    ##
        xy = list(x)                                                                 ##
        for i, yy in enumerate(y):                                                   ##
            xy.insert(2 * i + 1, yy)                                                 ##
        symbolic_num, symbolic_denom = '', ''                                        ##
        symbolic_num = [item for sublist in zip(x, ['+'] * N) for item in sublist]   ##
        symbolic_denom = [item for sublist in zip(y, ['+'] * N) for item in sublist] ##
        (symbolic_num.pop(), symbolic_denom.pop())                                   ##
        symbolic_num = ''.join(symbolic_num)                                         ##
        # psi  = (x1 + x2 + ...) / (y1 + y2 + ...).                                  ##
        symbolic_denom = ''.join(symbolic_denom)                                     ##
        psi_fo = ot.SymbolicFunction(xy,\                                            ##
                             ['(' + symbolic_num + ')/(' + symbolic_denom + ')'])    ##
        psi_to = ot.SymbolicFunction(xy,\                                            ##
                    ['1 - ' + '(' + symbolic_num + ')/(' + symbolic_denom + ')'])    ##
        return psi_fo, psi_to                                                        ##
#######################################################################################