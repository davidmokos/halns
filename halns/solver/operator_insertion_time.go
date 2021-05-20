package solver

import (
	"math/rand"
	"sort"
)

type SortingTimeInsertionOperator struct {}

func (o SortingTimeInsertionOperator) Apply(solution *Solution) *Solution {
	newSolution := EmptySolution(globalInstance.NumPlansToCreate)
	newSolution.Plans = solution.CopyPlans()

	requests := solution.UnplannedRequests.ToList()
	sort.Slice(requests, func(i, j int) bool {
		return requests[i].Drop.TimeWindowList.MaxFromTime < requests[j].Drop.TimeWindowList.MaxFromTime
	})

	planIndexes := make([]int, 0, len(newSolution.Plans))
	for i := range newSolution.Plans {
		planIndexes = append(planIndexes, i)
	}

	for _, r := range requests {
		if r.IsPartial {
			position := findBestInsertInPlan(newSolution.Plans[r.Courier], r)
			insertIntoPlan(newSolution.Plans[r.Courier], r, position)
		} else {
			rand.Shuffle(len(planIndexes), func(i, j int) { planIndexes[i], planIndexes[j] = planIndexes[j], planIndexes[i] })
			for i, planIndex := range planIndexes {
				position := findBestInsertInPlan(newSolution.Plans[planIndex], r)
				if position.isFeasible || i == len(planIndexes) - 1 {
					insertIntoPlan(newSolution.Plans[planIndex], r, position)
					break
				}
			}
		}
	}
	newSolution.ComputeCost()
	return newSolution
}