package solver

import (
	"math/rand"
)

type InterRouteInsertionOperator struct{}

func (o InterRouteInsertionOperator) Apply(solution *Solution) *Solution {
	newSolution := EmptySolution(globalInstance.NumPlansToCreate)
	newSolution.Plans = solution.CopyPlans()

	requests := solution.UnplannedRequests.ToList()
	rand.Shuffle(len(requests), func(i, j int) { requests[i], requests[j] = requests[j], requests[i] })

	for _, r := range requests {
		position := findBestInsertInSolution(newSolution, r)
		insertIntoPlan(newSolution.Plans[position.planIndex], r, position.planPosition)
	}

	newSolution.ComputeCost()
	return newSolution
}
