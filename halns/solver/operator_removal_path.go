package solver

type PathRemovalOperator struct {}

func (op PathRemovalOperator) Apply(solution *Solution, removeCount int) *Solution {

	rndPlanIndex, randomPlan := solution.RandomNotEmptyPlan()
	request := randomPlan.RandomAction().Request

	var pickupIdx int
	if request.IsPartial {
		pickupIdx = 0
	} else {
		pickupIdx = randomPlan.FindPickup(request)
	}
	dropIdx := randomPlan.FindDrop(request)

	unplannedRequests := make(RequestSet)

	for i := pickupIdx; i < dropIdx; i++ {
		if unplannedRequests.Size() < removeCount {
			unplannedRequests.Add(randomPlan.Actions[i].Request)
		}
	}

	newSolution := solution.Copy()
	newPlan := newSolution.Plans[rndPlanIndex].CopyWithoutRequests(&unplannedRequests)
	newSolution.Plans[rndPlanIndex] = &newPlan
	newSolution.Plans[rndPlanIndex].ComputeMetrics()
	newSolution.UnplannedRequests.AddAll(&unplannedRequests)
	newSolution.ComputeCost()

	return &newSolution
}
