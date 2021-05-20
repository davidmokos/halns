package solver

type LinearCrossoverOperator struct{}

func (o LinearCrossoverOperator) Apply(best *Solution, random *Solution) *Solution {
	maxCrossover := best.MaxPlanLength() - 1

	firstCrossoverPoint := RandomRange(0, maxCrossover - 1)
	secondCrossoverPoint := RandomRange(firstCrossoverPoint, maxCrossover)
	emplacedRequests := NewRequestSet()

	for _, p := range best.Plans {
		for ai, a := range p.Actions {
			if ai >= firstCrossoverPoint && ai < secondCrossoverPoint {
				emplacedRequests.Add(a.Request)
			}
		}
	}

	centerParts := make([][]*Action, len(best.Plans))
	for pi, p := range best.Plans {
		for _, a := range p.Actions {
			if emplacedRequests.Contains(a.Request){
				centerParts[pi] = append(centerParts[pi], a)
			}
		}
	}

	randomParts := make([][]*Action, len(best.Plans))
	for pi, p := range random.Plans {
		for _, a := range p.Actions {
			if !emplacedRequests.Contains(a.Request){
				randomParts[pi] = append(randomParts[pi], a)
			}
		}
	}

	newSolution := EmptySolution(globalInstance.NumPlansToCreate)
	for pi, plan := range newSolution.Plans {
		for ai, rndAction := range randomParts[pi] {
			if ai < firstCrossoverPoint {
				plan.Append(rndAction)
				emplacedRequests.Add(rndAction.Request)
			} else if emplacedRequests.Contains(rndAction.Request) {
				plan.Append(rndAction)
			}
		}
		for _, cenAction := range centerParts[pi] {
			plan.Append(cenAction)
		}
		for _, rndAction := range randomParts[pi] {
			if !emplacedRequests.Contains(rndAction.Request) {
				plan.Append(rndAction)
			}
		}
	}

	newSolution.ComputeCost()
	newSolution.UnplannedRequests = best.UnplannedRequests.Intersection(&random.UnplannedRequests)
	return newSolution
}
