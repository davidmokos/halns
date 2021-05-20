package solver

type OnePointCrossoverOperator struct{}

func (o OnePointCrossoverOperator) Apply(best *Solution, random *Solution) *Solution {
	newSolution := EmptySolution(globalInstance.NumPlansToCreate)

	maxCrossover := best.MaxPlanLength() - 1

	crossoverPoint := RandomRange(0, maxCrossover)
	emplacedRequests := NewRequestSet()

	for pi, bp := range best.Plans {
		for ai, ba := range bp.Actions {
			if ai <= crossoverPoint {
				newSolution.Plans[pi].Append(ba)
				emplacedRequests.Add(ba.Request)
			} else if emplacedRequests.Contains(ba.Request) {
				newSolution.Plans[pi].Append(ba)
			}
		}
	}

	for pi, rp := range random.Plans {
		for _, ra := range rp.Actions {
			if !emplacedRequests.Contains(ra.Request) {
				newSolution.Plans[pi].Append(ra)
			}
		}
	}

	newSolution.ComputeCost()
	newSolution.UnplannedRequests = best.UnplannedRequests.Intersection(&random.UnplannedRequests)
	return newSolution
}
