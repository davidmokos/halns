package solver

type LocalSearch2OptOperator struct {}

func (op LocalSearch2OptOperator) Apply(solution *Solution) *Solution {
	newSolution := solution.Copy()
	rndPlanIdx, tmpPlan := newSolution.RandomNotEmptyPlan()

	for i := 0; i < tmpPlan.Length() - 1; i++ {
		for j := i + 1; j < tmpPlan.Length(); j++ {
			newPlan := op.swap(tmpPlan, i, j)
			if newPlan.GetCost() < tmpPlan.GetCost() && (newPlan.Feasible || !tmpPlan.Feasible) {
				tmpPlan = newPlan
			}
		}
	}

	newSolution.Plans[rndPlanIdx] = tmpPlan
	newSolution.ComputeCost()
	return &newSolution
}

func (op LocalSearch2OptOperator) swap(plan *Plan, from int, to int) *Plan {

	middlePart := make([]*Action, 0, to - from + 1)
	for i := to; i >= from; i-- {
		middlePart = append(middlePart, plan.Actions[i])
	}

	dropOffs := make(map[*Request]int)
	for i, a := range middlePart {
		if a.Type == Drop {
			dropOffs[a.Request] = i
		} else {
			dropIdx, ok := dropOffs[a.Request]
			if ok {
				middlePart[i], middlePart[dropIdx] = middlePart[dropIdx], middlePart[i]
			}
		}
	}

	newPlan := EmptyPlan(plan.Courier)
	for i, a := range plan.Actions {
		if i >= from && i <= to {
			newPlan.Append(middlePart[i - from])
		} else {
			newPlan.Append(a)
		}
	}

	newPlan.ComputeMetrics()
	return &newPlan
}