package solver

import (
	"math"
	"sort"
)

type requestCost struct {
	request *Request
	cost float64
}

type RelatedRemovalOperator struct {}

func (op RelatedRemovalOperator) Apply(solution *Solution, removeCount int) *Solution {

	_, randomPlan := solution.RandomNotEmptyPlan()
	request := randomPlan.RandomAction().Request

	var rndPickupIdx int
	if request.IsPartial {
		rndPickupIdx = 0
	} else {
		rndPickupIdx = randomPlan.FindPickup(request)
	}
	rndDropIdx := randomPlan.FindDrop(request)

	var normalizeValue int64 = 1
	for _, p := range solution.Plans {
		normalizeValue = Max(normalizeValue, p.LastEta())
	}

	var requestCosts []requestCost

	for _, p := range solution.Plans {
		for pickupIdx, a := range p.Actions {
			if a.Type == Pickup {
				dropIdx := p.FindDrop(a.Request)

				var pickupNode int
				if request.IsPartial {
					pickupNode = globalInstance.Starts[request.Courier]
				} else {
					pickupNode = request.Pickup.Node
				}
				startCost := float64(globalInstance.CarDurationMatrix[pickupNode][a.Node])
				endCost := float64(globalInstance.CarDurationMatrix[request.Drop.Node][a.Request.Drop.Node])

				cost := startCost - endCost +
					3*(math.Abs(float64(randomPlan.Etas[rndPickupIdx]-p.Etas[pickupIdx])/float64(normalizeValue))+
						math.Abs(float64(randomPlan.Etas[rndDropIdx]-p.Etas[dropIdx])/float64(normalizeValue)))

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

func selectRequestsToDrop(requestCosts []requestCost, removeCount int) *RequestSet {
	sort.Slice(requestCosts, func(i, j int) bool {
		return requestCosts[i].cost < requestCosts[j].cost
	})

	unplannedRequests := make(RequestSet)
	for i := 0; i < removeCount; i++ {
		unplannedRequests.Add(requestCosts[i].request)
	}
	return &unplannedRequests
}
