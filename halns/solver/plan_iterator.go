package solver

type PlanIterator struct {
	plan     *Plan
	courier  int
	index    int
	planIndex    int
	instance *VRPInstance

	insertion   *PlanInsertion

	length int
}

func NewPlanIterator(plan *Plan, instance *VRPInstance, courier int, insertion *PlanInsertion) *PlanIterator {
	length := plan.Length() + 2
	if insertion != nil {
		if insertion.request.IsPartial {
			length += 1
		} else {
			length += 2
		}
	}

	return &PlanIterator{
		plan: plan,
		instance: instance,
		courier: courier,
		index: 0,
		planIndex: 0,
		insertion: insertion,
		length: length,
	}
}

func (iter *PlanIterator) Next() *Action {
	var ret *Action
	if iter.index == 0 {
		ret = iter.instance.Actions[iter.instance.Starts[iter.courier]]
	} else if iter.index == iter.length - 1 {
		ret = iter.instance.Actions[iter.instance.Ends[iter.courier]]
	} else {
		if iter.insertion != nil && !iter.insertion.request.IsPartial && iter.insertion.pickIdx == iter.index - 1 {
			ret = iter.insertion.request.Pickup
		} else if iter.insertion != nil && iter.insertion.dropIdx == iter.index - 1  {
			ret = iter.insertion.request.Drop
		} else{
			ret = iter.plan.Actions[iter.planIndex]
			iter.planIndex++
		}
	}
	iter.index++
	return ret
}

func (iter *PlanIterator) HasNext() bool {
	return iter.index < iter.length
}