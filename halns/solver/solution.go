package solver

import (
	"fmt"
	"math/rand"
	"strings"
)

type Solution struct {
	Plans             []*Plan
	UnplannedRequests RequestSet
	Cost              int64
	feasible          bool
}

func EmptySolution(numPlans int) *Solution {
	plans := make([]*Plan, 0, numPlans)
	for i := 0; i < numPlans; i++ {
		plans = append(plans, &Plan{
			Courier: i,
		})
	}
	return &Solution{
		Plans:             plans,
		UnplannedRequests: make(RequestSet),
		Cost:              0,
		feasible:          true,
	}
}

func (solution *Solution) RandomNotEmptyPlan() (int, *Plan) {
	if len(solution.Plans) == 0 {
		panic("trying to gen a random plan when no plans exist")
	}
	planIndexes := make([]int, 0, len(solution.Plans))
	for i := range solution.Plans {
		planIndexes = append(planIndexes, i)
	}
	rand.Shuffle(len(planIndexes), func(i, j int) { planIndexes[i], planIndexes[j] = planIndexes[j], planIndexes[i] })
	for _, i := range planIndexes {
		if solution.Plans[i].Length() > 0 {
			return i, solution.Plans[i]
		}
	}
	return -1, nil
}

func (solution *Solution) RandomPlan() *Plan {
	if len(solution.Plans) == 0 {
		panic("trying to gen a random plan when no plans exist")
	}
	rndPlanIndex := RandomRange(0, len(solution.Plans))
	return solution.Plans[rndPlanIndex]
}

func (solution *Solution) ToSolutionInterface() VRPSolutionInterface {
	plans := make([][]int, len(solution.Plans))
	for i, p := range solution.Plans {
		actions := make([]int, 0, p.Length()+2)
		actions = append(actions, globalInstance.Starts[i])
		for _, a := range p.Actions {
			actions = append(actions, a.Node)
		}
		actions = append(actions, globalInstance.Ends[i])
		plans[i] = actions
	}
	return VRPSolutionInterface{
		Plans: plans,
		Etas:  [][]float64{},
		Etds:  [][]float64{},
	}
}

func (solution *Solution) Copy() Solution {
	plans := make([]*Plan, 0, len(solution.Plans))
	for _, p := range solution.Plans {
		newPlan := p.Copy()
		plans = append(plans, &newPlan)
	}
	return Solution{
		Plans:             plans,
		UnplannedRequests: solution.UnplannedRequests.Copy(),
		Cost:              solution.Cost,
		feasible:          solution.feasible,
	}
}

func (solution *Solution) CopyPlans() []*Plan {
	plans := make([]*Plan, 0, len(solution.Plans))
	for _, p := range solution.Plans {
		newPlan := p.Copy()
		plans = append(plans, &newPlan)
	}
	return plans
}

func (solution *Solution) ComputeCost() {
	var cost int64 = 0
	feasible := true
	for _, p := range solution.Plans {
		if p.needsRecompute {
			p.ComputeMetrics()
		}
		if !p.Feasible {
			feasible = false
		}
		planCost := p.GetCost()
		cost += planCost
	}
	solution.Cost = cost
	solution.feasible = feasible
}

func (solution *Solution) String() string {
	var b strings.Builder
	_, _ = fmt.Fprintf(&b, "Solution:\n")
	for _, p := range solution.Plans {
		_, _ = fmt.Fprintf(&b, "  Courier %d: %s\n", p.Courier, p.String())
	}
	_, _ = fmt.Fprintf(&b, "Unplanned Requests: %s\n", solution.UnplannedRequests.String())
	_, _ = fmt.Fprintf(&b, "Cost: %d\n", solution.Cost)
	return b.String()
}

func (solution *Solution) MaxPlanLength() int {
	var maxLength = 0
	for _, p := range solution.Plans {
		if p.Length() > maxLength {
			maxLength = p.Length()
		}
	}
	return maxLength
}

func (solution *Solution) sanityCheck() {
	allRequests := RequestSetFromList(globalInstance.Requests)
	for _, p := range solution.Plans {
		pickups := NewRequestSet()
		dropoffs := NewRequestSet()
		for _, a := range p.Actions {
			if a.Type == Pickup {
				if pickups.Contains(a.Request) {
					panic("Pickup is twice in plan")
				}
				if dropoffs.Contains(a.Request) {
					panic("Drop is before pickup")
				}
				pickups.Add(a.Request)
			} else if a.Type == Drop {
				if dropoffs.Contains(a.Request) {
					panic("Drop is twice in plan")
				}
				if a.Request.IsPartial {
					if pickups.Contains(a.Request) {
						panic("Partial request has a pickup. This should never happen.")
					}
				} else {
					if !pickups.Contains(a.Request) {
						panic("Drop is missing a pickup")
					}
				}
				dropoffs.Add(a.Request)
				allRequests.Delete(a.Request)
			}
		}
	}
	union := solution.UnplannedRequests.Union(&allRequests)
	if union.Size() != allRequests.Size() || union.Size() != solution.UnplannedRequests.Size(){
		panic("Not all requests planned?")
	}
}
