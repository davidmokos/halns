package solver

type LocalSearchInterExchangeOperator struct{}

func (op LocalSearchInterExchangeOperator) Apply(solution *Solution) *Solution {
	newSolution := solution.Copy()
	_, randomPlan := newSolution.RandomNotEmptyPlan()

	requests := NewRequestSet()
	for _, a := range randomPlan.Actions {
		requests.Add(a.Request)
	}
	for r := range requests {
		randomPlan.Remove(r)
		position := findBestInsertInSolution(&newSolution, r)
		insertIntoPlan(newSolution.Plans[position.planIndex], r, position.planPosition)
	}
	newSolution.ComputeCost()
	return &newSolution
}
