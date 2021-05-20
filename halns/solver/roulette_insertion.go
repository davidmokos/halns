package solver

type InsertionOperator interface {
	Apply(solution *Solution) *Solution
}

type InsertionRoulette struct {
	operators []InsertionOperator
	probabilities []float64
	scores        []float64
	usedCounts    []int
	used          []int
}

func CreateInsertionRoulette() *InsertionRoulette {
	operators := []InsertionOperator{
		IntraRouteInsertionOperator{},
		InterRouteInsertionOperator{},
		SortingTimeInsertionOperator{},
		GreedyInsertionOperator{},
	}
	probabilities := make([]float64, len(operators))
	for i := 0; i < len(operators); i++ {
		probabilities[i] = insertionOperatorInitialProbability
	}
	scores := make([]float64, len(operators))
	usedCounts := make([]int, len(operators))
	insertionRoulette := InsertionRoulette{
		operators:     operators,
		probabilities: probabilities,
		scores:        scores,
		usedCounts:    usedCounts,
		used:          nil,
	}
	return &insertionRoulette
}

func (insertionRoulette *InsertionRoulette) selectOperator() (int, *InsertionOperator) {
	var maxProb float64
	probabilities := make([]float64, 0, len(insertionRoulette.operators))
	for i := range insertionRoulette.operators {
		prob := insertionRoulette.probabilities[i]
		maxProb += prob
		probabilities = append(probabilities, maxProb)
	}
	rouletteOutcome := RandomFloatRange(0, maxProb)
	var operatorIndex int
	for i, p := range probabilities {
		if rouletteOutcome <= p {
			operatorIndex = i
			break
		}
	}
	return operatorIndex, &insertionRoulette.operators[operatorIndex]
}

func (insertionRoulette *InsertionRoulette) PerformInsertion(solution *Solution) *Solution {
	index, op := insertionRoulette.selectOperator()
	newSolution := (*op).Apply(solution)
	insertionRoulette.usedCounts[index] += 1
	insertionRoulette.used = append(insertionRoulette.used, index)
	return newSolution
}

func (insertionRoulette *InsertionRoulette) updateScores(current bool, best bool, feasible bool) {
	var scoreIncrease float64 = 0
	if current {
		scoreIncrease += pi3
	}
	if best {
		scoreIncrease += pi1
	}
	if feasible {
		scoreIncrease += pi2
	}
	for _, index := range insertionRoulette.used {
		insertionRoulette.scores[index] += scoreIncrease
	}
	insertionRoulette.used = nil
}

func (insertionRoulette *InsertionRoulette) updateProbabilities() {
	for i := 0; i < len(insertionRoulette.operators); i++ {
		if insertionRoulette.usedCounts[i] > 0 {
			insertionRoulette.probabilities[i] = insertionRoulette.probabilities[i]*(1-rouletteWheelParameter) +
				rouletteWheelParameter*insertionRoulette.scores[i]/float64(insertionRoulette.usedCounts[i])
			insertionRoulette.usedCounts[i] = 0
			insertionRoulette.scores[i] = 0
		}
	}
}