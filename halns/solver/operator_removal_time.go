package solver

import (
	"math"
)

type TimeRemovalOperator struct {}

func (op TimeRemovalOperator) Apply(solution *Solution, removeCount int) *Solution {

	_, randomPlan := solution.RandomNotEmptyPlan()
	request := randomPlan.RandomAction().Request

	var rndPickupIdx int
	if request.IsPartial {
		rndPickupIdx = 0
	} else {
		rndPickupIdx = randomPlan.FindPickup(request)
	}
	rndDropIdx := randomPlan.FindDrop(request)

	var requestCosts []requestCost

	for _, p := range solution.Plans {
		for pickupIdx, a := range p.Actions {
			if a.Type == Pickup {
				dropIdx := p.FindDrop(a.Request)

				cost := math.Abs(float64(randomPlan.Etas[rndPickupIdx]-p.Etas[pickupIdx])) +
					math.Abs(float64(randomPlan.Etas[rndDropIdx]-p.Etas[dropIdx]))

				requestCosts = append(requestCosts, requestCost{
					request: a.Request,
					cost:    cost,
				})
			}
		}
	}

	requestsToRemove := selectRequestsToDrop(requestCosts, removeCount)

	newSolution := EmptySolution(globalInstance.NumPlansToCreate)

	for i, p := range solution.Plans {
		for _, a := range p.Actions {
			if !requestsToRemove.Contains(a.Request) {
				newSolution.Plans[i].Append(a)
			}
		}
		newSolution.Plans[i].ComputeMetrics()
	}

	newSolution.UnplannedRequests = solution.UnplannedRequests.Copy()
	newSolution.UnplannedRequests.AddAll(requestsToRemove)
	newSolution.ComputeCost()

	return newSolution
}
