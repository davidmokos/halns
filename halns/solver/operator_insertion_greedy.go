package solver

import "math"

type GreedyInsertionOperator struct{}

func (o GreedyInsertionOperator) Apply(solution *Solution) *Solution {
	newSolution := EmptySolution(globalInstance.NumPlansToCreate)
	newSolution.Plans = solution.CopyPlans()

	requests := solution.UnplannedRequests.Copy()

	for requests.Size() > 0 {
		var bestPosition solutionPosition
		var bestCost int64 = math.MaxInt64
		var bestRequest *Request
		for r := range requests {
			position := findBestInsertInSolution(newSolution, r)
			if position.cost < bestCost && (position.isFeasible || !bestPosition.isFeasible) {
				bestCost = position.cost
				bestPosition = position
				bestRequest = r
			}
		}
		insertIntoPlan(newSolution.Plans[bestPosition.planIndex], bestRequest, bestPosition.planPosition)
		requests.Delete(bestRequest)
	}

	newSolution.ComputeCost()
	return newSolution
}
