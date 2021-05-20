package solver


type DistanceRemovalOperator struct {}

func (op DistanceRemovalOperator) Apply(solution *Solution, removeCount int) *Solution {
	_, rndPlan := solution.RandomNotEmptyPlan()
	request := rndPlan.RandomAction().Request

	var requestCosts []requestCost

	for _, p := range solution.Plans {
		for _, a := range p.Actions {
			if a.Type == Pickup {

				var pickupNode int
				if request.IsPartial {
					pickupNode = globalInstance.Starts[request.Courier]
				} else {
					pickupNode = request.Pickup.Node
				}
				startCost := globalInstance.CarDistanceMatrix[pickupNode][a.Node]
				endCost := globalInstance.CarDistanceMatrix[request.Drop.Node][a.Request.Drop.Node]

				cost := startCost + endCost

				requestCosts = append(requestCosts, requestCost{
					request: a.Request,
					cost:    float64(cost),
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
