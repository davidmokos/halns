package solver

import (
	"math/rand"
)

type RandomRemovalOperator struct {}

func (op RandomRemovalOperator) Apply(solution *Solution, removeCount int) *Solution {

	requests := append([]*Request{}, globalInstance.Requests...)
	rand.Shuffle(len(requests), func(i, j int) { requests[i], requests[j] = requests[j], requests[i] })

	requestsToRemove := make(RequestSet)

	for _, r := range requests {
		if requestsToRemove.Size() >= removeCount {
			break
		}
		if !solution.UnplannedRequests.Contains(r) {
			requestsToRemove.Add(r)
		}
	}

	newSolution := EmptySolution(globalInstance.NumPlansToCreate)

	for i, p := range solution.Plans {
		newPlan := p.CopyWithoutRequests(&requestsToRemove)
		newSolution.Plans[i] = &newPlan
		newSolution.Plans[i].ComputeMetrics()
	}

	newSolution.UnplannedRequests = solution.UnplannedRequests.Copy()
	newSolution.UnplannedRequests.AddAll(&requestsToRemove)
	newSolution.ComputeCost()

	return newSolution
}
