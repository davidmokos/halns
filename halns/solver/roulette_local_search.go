package solver

import "math/rand"

type LocalSearchOperator interface {
	Apply(solution *Solution) *Solution
}

type LocalSearchRoulette struct {
	operators []LocalSearchOperator
}

func CreateLocalSearchRoulette() *LocalSearchRoulette {
	operators := []LocalSearchOperator{
		LocalSearchIntraExchangeOperator{},
		LocalSearchInterExchangeOperator{},
		LocalSearch2OptOperator{},
	}
	localSearchRoulette := LocalSearchRoulette{
		operators: operators,
	}
	return &localSearchRoulette
}

func (localSearchRoulette *LocalSearchRoulette) selectOperator() (int, *LocalSearchOperator) {
	operatorIndex := RandomRange(0, len(localSearchRoulette.operators))
	return operatorIndex, &localSearchRoulette.operators[operatorIndex]
}

func (localSearchRoulette *LocalSearchRoulette) PerformLocalSearch(solution *Solution) *Solution {
	operatorIndexes := make([]int, 0, len(localSearchRoulette.operators))
	for i := range localSearchRoulette.operators {
		operatorIndexes = append(operatorIndexes, i)
	}
	rand.Shuffle(len(operatorIndexes), func(i, j int) { operatorIndexes[i], operatorIndexes[j] = operatorIndexes[j], operatorIndexes[i] })
	var newSolution = solution
	for _, operatorIndex := range operatorIndexes {
		op := localSearchRoulette.operators[operatorIndex]
		newSolution = op.Apply(newSolution)
		if newSolution.Cost < solution.Cost {
			break
		}
	}
	return newSolution
}
