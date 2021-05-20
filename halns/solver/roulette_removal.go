package solver

import (
	"math"
)

type RemovalOperator interface {
	Apply(solution *Solution, removeCount int) *Solution
}

type RemovalRoulette struct {
	operators     []RemovalOperator
	probabilities []float64
	scores        []float64
	usedCounts    []int
	used          []int
}

func CreateRemovalRoulette() *RemovalRoulette {
	operators := []RemovalOperator{
		RandomRemovalOperator{},
		PathRemovalOperator{},
		RelatedRemovalOperator{},
		TimeRemovalOperator{},
		DistanceRemovalOperator{},
	}
	probabilities := make([]float64, len(operators))
	for i := 0; i < len(operators); i++ {
		probabilities[i] = removalOperatorInitialProbability
	}
	scores := make([]float64, len(operators))
	usedCounts := make([]int, len(operators))
	removalRoulette := RemovalRoulette{
		operators:     operators,
		probabilities: probabilities,
		scores:        scores,
		usedCounts:    usedCounts,
		used:          nil,
	}
	return &removalRoulette
}

func (removalRoulette *RemovalRoulette) updateScores(current bool, best bool, feasible bool) {
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
	for _, index := range removalRoulette.used {
		removalRoulette.scores[index] += scoreIncrease
	}
	removalRoulette.used = nil
}

func (removalRoulette *RemovalRoulette) updateProbabilities() {
	for i := 0; i < len(removalRoulette.operators); i++ {
		if removalRoulette.usedCounts[i] > 0 {
			removalRoulette.probabilities[i] = removalRoulette.probabilities[i]*(1-rouletteWheelParameter) +
				rouletteWheelParameter*removalRoulette.scores[i]/float64(removalRoulette.usedCounts[i])
			removalRoulette.usedCounts[i] = 0
			removalRoulette.scores[i] = 0
		}
	}
}

func (removalRoulette *RemovalRoulette) selectOperator() (int, *RemovalOperator) {
	var maxProb float64
	probabilities := make([]float64, 0, len(removalRoulette.operators))
	for i := range removalRoulette.operators {
		prob := removalRoulette.probabilities[i]
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
	return operatorIndex, &removalRoulette.operators[operatorIndex]
}

func (removalRoulette *RemovalRoulette) PerformRemoval(solution *Solution, applyCount int) *Solution {
	newSolution := solution
	for i := 0; i < applyCount; i++ {
		index, op := removalRoulette.selectOperator()
		min := float64(len(globalInstance.Requests)) * removeMin
		max := float64(len(globalInstance.Requests)) * removeMax
		removeCount := int(math.Round(RandomFloatRange(min, max)))
		newSolution = (*op).Apply(newSolution, removeCount)
		removalRoulette.usedCounts[index] += 1
		removalRoulette.used = append(removalRoulette.used, index)
	}
	return newSolution
}
