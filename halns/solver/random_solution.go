package solver

import (
	"math"
	"math/rand"
)

type planPosition struct {
	pick       int
	drop       int
	isFeasible bool
	cost       int64
}

type solutionPosition struct {
	planPosition
	planIndex int
}

func findBestInsertInSolution(solution *Solution, request *Request) solutionPosition {
	var bestPosition planPosition
	var bestPlanIndex int
	var bestCost int64 = math.MaxInt64

	if request.IsPartial {
		bestPlanIndex = request.Courier
		bestPosition = findBestInsertInPlan(solution.Plans[bestPlanIndex], request)
	} else {
		for i, plan := range solution.Plans {
			position := findBestInsertInPlan(plan, request)
			if position.cost < bestCost && (position.isFeasible || !bestPosition.isFeasible) {
				bestPosition = position
				bestPlanIndex = i
				bestCost = position.cost
			}
		}
	}
	return solutionPosition{
		planPosition: bestPosition,
		planIndex:    bestPlanIndex,
	}
}

func findBestInsertInPlan(plan *Plan, request *Request) planPosition {
	var bestInsertionCost int64 = math.MaxInt64
	var bestPosition planPosition

	if cached := plan.cachedBestPosition(request); cached != nil {
		return *cached
	}


	var metricsFun getMetricsFun

	if globalInstance.CapacityEnabled {
		metricsFun = plan.getMetricsWithCapacity
	} else {
		metricsFun = plan.getMetrics
	}

	insertion := PlanInsertion{
		request: request,
		dropIdx: 0,
		pickIdx: 0,
	}

	if request.IsPartial {
		if plan.Courier != request.Courier {
			panic("courier id from partial request does not match plan")
		}
		for i := 0; i <= plan.Length(); i++ {
			insertion.dropIdx = i
			insertionCost, feasible, finished := plan.InsertionCost(
				&insertion,
				bestInsertionCost,
				metricsFun)
			if finished && insertionCost < bestInsertionCost {
				if feasible {
					bestInsertionCost = insertionCost
					bestPosition = planPosition{drop: i, isFeasible: true, cost: insertionCost}
				} else if !bestPosition.isFeasible {
					bestInsertionCost = insertionCost
					bestPosition = planPosition{drop: i, isFeasible: false, cost: insertionCost}
				}
			}
		}
	} else {
		for i := 0; i <= plan.Length(); i++ {
			insertion.pickIdx = i
			for j := i + 1; j <= plan.Length()+1; j++ {
				insertion.dropIdx = j
				insertionCost, feasible, finished := plan.InsertionCost(
					&insertion, bestInsertionCost, metricsFun)

				if finished && insertionCost < bestInsertionCost {
					if feasible {
						bestInsertionCost = insertionCost
						bestPosition = planPosition{pick: i, drop: j, isFeasible: true, cost: insertionCost}
					} else if !bestPosition.isFeasible {
						bestInsertionCost = insertionCost
						bestPosition = planPosition{pick: i, drop: j, isFeasible: false, cost: insertionCost}
					}
				}
			}
		}
	}

	if bestInsertionCost < math.MaxInt64 {
		plan.cacheBestPosition(request, bestPosition)
		return bestPosition
	} else {
		panic("could not find an insertion position")
	}
}

func insertIntoPlan(plan *Plan, request *Request, position planPosition) {
	if !request.IsPartial {
		plan.Insert(request.Pickup, position.pick)
	}
	plan.Insert(request.Drop, position.drop)
	plan.ComputeMetrics()
}

func InsertionHeuristicsSolution() *Solution {
	op := InterRouteInsertionOperator{}
	init := EmptySolution(globalInstance.NumPlansToCreate)
	init.UnplannedRequests = RequestSetFromList(globalInstance.Requests)
	solution := op.Apply(init)
	return solution
}

func RandomSolution() *Solution {
	solution := EmptySolution(globalInstance.NumPlansToCreate)
	plans := solution.Plans

	requests := append([]*Request{}, globalInstance.Requests...)
	rand.Shuffle(len(requests), func(i, j int) { requests[i], requests[j] = requests[j], requests[i] })

	for _, r := range requests {

		var bestPlan *Plan
		var bestPlanIndex = -1

		if r.IsPartial {
			bestPlanIndex = r.Courier
			plan := plans[bestPlanIndex]
			for c := 0; c < 100; c++ {
				index := RandomRange(0, plan.Length()+1)
				newPlan := plan.Copy()
				newPlan.Insert(r.Drop, index)
				newPlan.ComputeMetrics()
				if newPlan.Feasible {
					bestPlan = &newPlan
					break
				}
			}
		} else {
			for c := 0; c < 100; c++ {
				pi := RandomRange(0, len(plans))
				i := RandomRange(0, plans[pi].Length()+1)
				j := RandomRange(i+1, plans[pi].Length()+2)
				newPlan := plans[pi].Copy()
				newPlan.Insert(r.Pickup, i)
				newPlan.Insert(r.Drop, j)
				newPlan.ComputeMetrics()
				bestPlanIndex = pi
				if newPlan.Feasible {
					bestPlan = &newPlan
					break
				}
			}
		}

		if bestPlan == nil {
			return nil
		}

		plans[bestPlanIndex] = bestPlan
	}

	solution.ComputeCost()

	return solution
}

func DummySolution() *Solution {
	solution := EmptySolution(globalInstance.NumPlansToCreate)
	plans := solution.Plans

	requests := append([]*Request{}, globalInstance.Requests...)

	for i, r := range requests {
		if r.IsPartial {
			plans[r.Courier].Append(r.Drop)
			plans[r.Courier].ComputeMetrics()
		} else {
			planIdx := i % globalInstance.NumPlansToCreate
			plans[planIdx].Append(r.Pickup)
			plans[planIdx].Append(r.Drop)
			plans[planIdx].ComputeMetrics()
		}
	}

	solution.ComputeCost()

	return solution
}
