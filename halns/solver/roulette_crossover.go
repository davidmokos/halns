package solver

type CrossoverOperator interface {
	Apply(best *Solution, random *Solution) *Solution
}

type CrossoverRoulette struct {
	operators []CrossoverOperator
}

func CreateCrossoverRoulette() *CrossoverRoulette {
	operators := []CrossoverOperator{
		OnePointCrossoverOperator{},
		TwoPointCrossoverOperator{},
		LinearCrossoverOperator{},
	}
	roulette := CrossoverRoulette{
		operators: operators,
	}
	return &roulette
}

func (roulette *CrossoverRoulette) selectOperator() (int, *CrossoverOperator) {
	operatorIndex := RandomRange(0, len(roulette.operators))
	return operatorIndex, &roulette.operators[operatorIndex]
}

func (roulette *CrossoverRoulette) PerformCrossover(best *Solution, random *Solution) *Solution {
	_, op := roulette.selectOperator()
	newSolution := (*op).Apply(best, random)
	return newSolution
}
