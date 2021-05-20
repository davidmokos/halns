package solver

import (
	"fmt"
	"strings"
)

type PlanInsertion struct {
	request *Request
	pickIdx int
	dropIdx int
}

type PlanMetrics struct {
	Etas     []int64
	Duration int64
	Distance int64
	Feasible bool
	Penalty  int64
}

func (planMetrics *PlanMetrics) GetCost() int64 {
	return planMetrics.Penalty + planMetrics.Distance/2
}

type Plan struct {
	Actions        []*Action
	Courier        int
	needsRecompute bool
	PlanMetrics
	bestPosition map[*Request]planPosition
}

func EmptyPlan(courier int) Plan {
	return Plan{
		Courier: courier,
	}
}

func (plan *Plan) cachedBestPosition(request *Request) *planPosition {
	if plan.needsRecompute {
		return nil
	}
	if val, ok := plan.bestPosition[request]; ok {
		return &val
	}
	return nil
}

func (plan *Plan) cacheBestPosition(request *Request, position planPosition) {
	if plan.bestPosition == nil {
		plan.bestPosition = make(map[*Request]planPosition)
	}
	plan.bestPosition[request] = position
}

func (plan *Plan) RandomAction() *Action {
	if len(plan.Actions) == 0 {
		return nil
	}
	rndIndex := RandomRange(0, len(plan.Actions))
	return plan.Actions[rndIndex]
}

func (plan *Plan) Length() int {
	return len(plan.Actions)
}

func (plan *Plan) LastEta() int64 {
	if len(plan.Etas) == 0 {
		return 0
	}
	return plan.Etas[len(plan.Etas)-1]
}


type getMetricsFun func(insertion *PlanInsertion, maxCost int64) (PlanMetrics, bool)

func (plan *Plan) InsertionCost(insertion *PlanInsertion, maxCost int64, getMetrics getMetricsFun) (int64, bool, bool) {
	planMetrics, finished := getMetrics(insertion, maxCost)
	return planMetrics.GetCost() - plan.GetCost(), planMetrics.Feasible, finished
}

func (plan *Plan) GetCost() int64 {
	if plan.needsRecompute {
		plan.ComputeMetrics()
	}
	return plan.PlanMetrics.GetCost()
}

func (plan *Plan) CopyWithoutRequests(set *RequestSet) Plan {
	newActions := make([]*Action, 0)
	for _, a := range plan.Actions {
		if !set.Contains(a.Request) {
			newActions = append(newActions, a)
		}
	}
	return Plan{
		Actions:        newActions,
		Courier:        plan.Courier,
		needsRecompute: true,
	}
}

func (plan *Plan) Copy() Plan {
	newActions := make([]*Action, len((*plan).Actions))
	copy(newActions, (*plan).Actions)
	newEtas := make([]int64, len((*plan).Etas))
	copy(newEtas, (*plan).Etas)
	planMetrics := PlanMetrics{
		Etas:     newEtas,
		Duration: plan.PlanMetrics.Duration,
		Distance: plan.PlanMetrics.Distance,
		Feasible: plan.PlanMetrics.Feasible,
		Penalty:  plan.PlanMetrics.Penalty,
	}

	return Plan{
		Actions:        newActions,
		Courier:        plan.Courier,
		needsRecompute: plan.needsRecompute,
		PlanMetrics:    planMetrics,
	}
}

func (plan *Plan) String() string {
	var b strings.Builder
	for _, a := range (*plan).Actions {
		actionType := "P"
		if a.Type == Drop {
			actionType = "D"
		} else if a.Type == Start {
			actionType = "S"
		} else if a.Type == End {
			actionType = "E"
		}
		_, _ = fmt.Fprintf(&b, "%s %d, ", actionType, a.Node)
	}
	_, _ = fmt.Fprintf(&b, "Cost %d ", plan.GetCost())
	if plan.needsRecompute {
		_, _ = fmt.Fprintf(&b, "❗️")
	} else {
		_, _ = fmt.Fprintf(&b, "✅")
	}

	return b.String()
}

func (plan *Plan) FindPickup(request *Request) int {
	for i, a := range (*plan).Actions {
		if a.Request == request && a.Type == Pickup {
			return i
		}
	}
	panic("Could not find pickup in plan")
}

func (plan *Plan) FindDrop(request *Request) int {
	for i, a := range (*plan).Actions {
		if a.Request == request && a.Type == Drop {
			return i
		}
	}
	panic("Could not find drop in plan")
}

func (plan *Plan) Append(action *Action) {
	(*plan).Actions = append((*plan).Actions, action)
	plan.needsRecompute = true
}

func (plan *Plan) Remove(request *Request) {
	if !request.IsPartial {
		index := plan.FindPickup(request)
		(*plan).Actions = append((*plan).Actions[:index], (*plan).Actions[index+1:]...)
	}
	index := plan.FindDrop(request)
	(*plan).Actions = append((*plan).Actions[:index], (*plan).Actions[index+1:]...)
	plan.needsRecompute = true
}

func (plan *Plan) Insert(action *Action, position int) {
	last := len((*plan).Actions) - 1
	if position > last {
		(*plan).Actions = append((*plan).Actions, action)
	} else {
		(*plan).Actions = append((*plan).Actions, (*plan).Actions[last])
		copy((*plan).Actions[position+1:], (*plan).Actions[position:last])
		(*plan).Actions[position] = action
	}
	plan.needsRecompute = true
}

func (plan *Plan) ComputeMetrics() {
	if !plan.needsRecompute {
		return
	}
	planMetrics, _ := plan.getMetricsWithEtas(nil, 0)
	plan.needsRecompute = false
	plan.PlanMetrics = planMetrics
	plan.bestPosition = make(map[*Request]planPosition)
}

func (plan *Plan) getMetricsWithEtas(insertion *PlanInsertion, maxCost int64) (PlanMetrics, bool) {
	if plan.Length() == 0 {
		return PlanMetrics{
			Etas:     nil,
			Duration: 0,
			Distance: 0,
			Feasible: true,
			Penalty:  0,
		}, true
	}
	var capacity int
	if globalInstance.CapacityEnabled {
		capacity = globalInstance.CourierCapacities[plan.Courier] - globalInstance.StartUtilizations[plan.Courier]
	}
	planIt := NewPlanIterator(plan, globalInstance, plan.Courier, insertion)

	metrics := PlanMetrics{
		Etas:     nil,
		Duration: 0,
		Distance: 0,
		Feasible: true,
		Penalty:  0,
	}

	var currentAction = planIt.Next()
	var startEta = currentAction.TimeWindowList.MaxFromTime
	var eta = startEta

	for {
		eta = Max(eta, currentAction.TimeWindowList.MaxFromTime)

		if insertion == nil && currentAction.Type != Start && currentAction.Type != End {
			metrics.Etas = append(metrics.Etas, eta)
		}

		if eta > currentAction.TimeWindowList.MinToTime{
			metrics.Feasible = metrics.Feasible && currentAction.TimeWindowList.IsArrivalFeasible(eta)
			metrics.Penalty += currentAction.TimeWindowList.GetPenaltyForArrivalAt(eta)
		}

		if globalInstance.CapacityEnabled {
			capacity -= currentAction.Demand
			if capacity < 0 {
				metrics.Feasible = false
			}
		}
		if !planIt.HasNext() {
			break
		}
		nextAction := planIt.Next()
		metrics.Distance += globalInstance.CarDistanceMatrix[currentAction.Node][nextAction.Node]

		eta += globalInstance.CarDurationMatrix[currentAction.Node][nextAction.Node]
		currentAction = nextAction
		if maxCost > 0 && (metrics.GetCost() - plan.GetCost()) > maxCost {
			return PlanMetrics{}, false
		}
	}
	metrics.Duration = eta - startEta

	return metrics, true
}


func (plan *Plan) getMetricsWithCapacity(insertion *PlanInsertion, maxCost int64) (PlanMetrics, bool) {
	metrics := PlanMetrics{
		Etas:     nil,
		Duration: 0,
		Distance: 0,
		Feasible: true,
		Penalty:  0,
	}

	var capacity int
	capacity = globalInstance.CourierCapacities[plan.Courier] - globalInstance.StartUtilizations[plan.Courier]
	planIt := NewPlanIterator(plan, globalInstance, plan.Courier, insertion)

	var currentAction = planIt.Next()
	var startEta = currentAction.TimeWindowList.MaxFromTime
	var eta = startEta

	for {
		eta = Max(eta, currentAction.TimeWindowList.MaxFromTime)

		if eta > currentAction.TimeWindowList.MinToTime{
			metrics.Feasible = metrics.Feasible && currentAction.TimeWindowList.IsArrivalFeasible(eta)
			metrics.Penalty += currentAction.TimeWindowList.GetPenaltyForArrivalAt(eta)
		}

		if globalInstance.CapacityEnabled {
			capacity -= currentAction.Demand
			if capacity < 0 {
				metrics.Feasible = false
			}
		}
		if !planIt.HasNext() {
			break
		}
		nextAction := planIt.Next()
		metrics.Distance += globalInstance.CarDistanceMatrix[currentAction.Node][nextAction.Node]

		eta += globalInstance.CarDurationMatrix[currentAction.Node][nextAction.Node]
		currentAction = nextAction
		if maxCost > 0 && (metrics.GetCost() - plan.GetCost()) > maxCost {
			return PlanMetrics{}, false
		}
	}
	metrics.Duration = eta - startEta

	return metrics, true
}


func (plan *Plan) getMetrics(insertion *PlanInsertion, maxCost int64) (PlanMetrics, bool) {
	metrics := PlanMetrics{
		Etas:     nil,
		Duration: 0,
		Distance: 0,
		Feasible: true,
		Penalty:  0,
	}

	planIt := NewPlanIterator(plan, globalInstance, plan.Courier, insertion)

	var currentAction = planIt.Next()
	var startEta = currentAction.TimeWindowList.MaxFromTime
	var eta = startEta

	for {
		eta = Max(eta, currentAction.TimeWindowList.MaxFromTime)

		if eta > currentAction.TimeWindowList.MinToTime{
			metrics.Feasible = metrics.Feasible && currentAction.TimeWindowList.IsArrivalFeasible(eta)
			metrics.Penalty += currentAction.TimeWindowList.GetPenaltyForArrivalAt(eta)
		}

		if !planIt.HasNext() {
			break
		}
		nextAction := planIt.Next()
		metrics.Distance += globalInstance.CarDistanceMatrix[currentAction.Node][nextAction.Node]

		eta += globalInstance.CarDurationMatrix[currentAction.Node][nextAction.Node]
		currentAction = nextAction

		if maxCost > 0 && (metrics.GetCost() - plan.GetCost()) > maxCost {
			return PlanMetrics{}, false
		}
	}
	metrics.Duration = eta - startEta

	return metrics, true
}
