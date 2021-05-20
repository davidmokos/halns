package solver

type LocalSearchIntraExchangeOperator struct{}

func (op LocalSearchIntraExchangeOperator) Apply(solution *Solution) *Solution {
	newSolution := solution.Copy()
	_, randomPlan := newSolution.RandomNotEmptyPlan()

	requests := NewRequestSet()
	for _, a := range randomPlan.Actions {
		requests.Add(a.Request)
	}
	for r := range requests {
		randomPlan.Remove(r)
		position := findBestInsertInPlan(randomPlan, r)
		insertIntoPlan(randomPlan, r, position)
	}
	newSolution.ComputeCost()
	return &newSolution
}
