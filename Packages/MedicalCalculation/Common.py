import operator

def GetMaxAISP(probDict):
    if probDict is None:
        return 0, 0
    # get the maximum ais probability by sorting values
    decendProb = dict(sorted(probDict.items(), key=operator.itemgetter(1), reverse=True))
    return next(iter(decendProb.items()))

def GetMaxAISByProbFilter(probDict, filter):
    if probDict is None:
        return 0, 0
    if filter is None:
        raise Exception("filter is not defined.")

    filteredDict = {key: val for key, val in probDict.items() if val >= filter}
    if len(filteredDict) == 0:  # if no item found then return ais 0 and original probDict
        return 0, probDict

    # get the maximum ais by sorting keys
    decendProb = dict(sorted(filteredDict.items(), key=operator.itemgetter(0), reverse=True))
    return next(iter(decendProb.items()))

def CalcMaxAISWithLimit(formula, filter, updatedProb):
    if formula is None:
        # if formula is missing, do nothing
        return None
    if filter is None:
        raise Exception("filter is not defined.")
    if updatedProb is None:
        raise Exception("updatedProb is not defined.")

    # step1: calc the max ais with prob(ais) >= filter
    ais, ais_prob = GetMaxAISByProbFilter(formula["P(AIS)"], filter)

    # step2: consider limit for updating the ais
    limit = formula["Limit"]
    if limit > ais:
        ais = limit
        formula["P(AIS)"][ais] = updatedProb

    # step3: update the final ais in formula
    formula["AIS"] = ais

def CalcMaxAISByLimitWithFlag(formula, flag, updatedProb):
    if formula is None:
        # if formula is missing, do nothing
        return None
    if filter is None:
        raise Exception("flag is not defined.")
    if updatedProb is None:
        raise Exception("updatedProb is not defined.")

    ais = 0
    limit = formula["Limit"]
    if limit > flag:
        ais = limit
        formula["P(AIS)"][ais] = updatedProb

    formula["AIS"] = ais

def InitFormula():
    result = FormulaResult()
    result["AIS"] = 0
    return result

def CombineFormulas(originalFormulas):
    if originalFormulas is None or len(originalFormulas) == 0:
        return None, None

    formulasToCombine = []
    for of in originalFormulas:
        if of is None:
            # if formula is missing - initialize it to zeros only for this calculation
            formulasToCombine.append(InitFormula())
        else:
            formulasToCombine.append(of)

    # step1: foreach ais build prob list out of all formulas and calc max probability
    maxAisProbDict = {}
    for i in range(6):  # index is the ais key
        plist = []
        for ftc in formulasToCombine:
            plist.append(ftc["P(AIS)"][i+1])
        maxAisProbDict[i+1] = max(plist)

    # steps2: calculate the max ais from all formulas
    aisList = []
    for formula in formulasToCombine:
        aisList.append(formula["AIS"])

    return max(aisList), maxAisProbDict

def FormulaResult(value=0, ais1p=0, ais2p=0, ais3p=0, ais4p=0, ais5p=0, ais6p=0, limit=0):
    aisProb = {1: ais1p, 2: ais2p, 3: ais3p, 4: ais4p, 5: ais5p, 6: ais6p}
    return {"Value": value, "P(AIS)": aisProb, "Limit": limit}

