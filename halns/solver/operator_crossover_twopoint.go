package solver

type TwoPointCrossoverOperator struct{}

func (o TwoPointCrossoverOperator) Apply(best *Solution, random *Solution) *Solution {
	maxCrossover := best.MaxPlanLength() - 1

	firstCrossoverPoint := RandomRange(0, maxCrossover - 1)
	secondCrossoverPoint := RandomRange(firstCrossoverPoint, maxCrossover)
	emplacedRequests := NewRequestSet()

	// Prepare center parts
	centerParts := make([][]*Action, len(best.Plans))
	for pi, p := range best.Plans {
		for ai, a := range p.Actions {
			if ai >= firstCrossoverPoint && ai < secondCrossoverPoint {
				emplacedRequests.Add(a.Request)
			}
		}
		for _, a := range p.Actions {
			if emplacedRequests.Contains(a.Request){
				centerParts[pi] = append(centerParts[pi], a)
			}
		}
	}

	// Prepare left parts
	leftRequests := NewRequestSet()
	leftParts := make([][]*Action, len(best.Plans))
	for pi, p := range random.Plans {
		for ai, a := range p.Actions {
			if ai >= secondCrossoverPoint && !emplacedRequests.Contains(a.Request) {
				leftRequests.Add(a.Request)
				emplacedRequests.Add(a.Request)
			}
		}
		for _, a := range p.Actions {
			if leftRequests.Contains(a.Request){
				leftParts[pi] = append(leftParts[pi], a)
			}
		}
	}

	// Prepare right parts
	rightParts := make([][]*Action, len(best.Plans))
	for pi, p := range random.Plans {
		for _, a := range p.Actions {
			if !emplacedRequests.Contains(a.Request) {
				rightParts[pi] = append(rightParts[pi], a)
			}
		}
	}


	newSolution := EmptySolution(globalInstance.NumPlansToCreate)
	for pi, plan := range newSolution.Plans {
		for _, leftAction := range leftParts[pi] {
			plan.Append(leftAction)
		}
		for _, cenAction := range centerParts[pi] {
			plan.Append(cenAction)
		}
		for _, rightAction := range rightParts[pi] {
			plan.Append(rightAction)
		}
	}

	newSolution.ComputeCost()
	newSolution.UnplannedRequests = best.UnplannedRequests.Intersection(&random.UnplannedRequests)
	return newSolution
}
