package solver

type VRPInstance struct {
	Actions           []*Action
	Requests          []*Request
	CarDistanceMatrix [][]int64
	CarDurationMatrix [][]int64
	NumPlansToCreate  int
	Starts            []int
	Ends              []int
	CourierCapacities []int
	StartUtilizations []int
	CapacityEnabled   bool
	TimeLimit         int64
}

func CreateInstance(instance VRPInstanceInterface) *VRPInstance {

	actionsLength := len(instance.CarDurationMatrix)
	actions := make([]*Action, actionsLength)

	capacityEnabled := len(instance.CourierCapacities) != 0

	for _, n := range instance.PickupNodes {
		demand := 0
		if capacityEnabled {
			demand = instance.NodeDemands[n]
		}
		actions[n] = &Action{
			TimeWindowList: CreateTimeWindowList(),
			Node:           n,
			Type:           Pickup,
			ServiceTime:    instance.PickupServiceTime,
			Request:        nil,
			Demand:         demand,
		}
	}
	for _, n := range instance.DropNodes {
		demand := 0
		if capacityEnabled {
			demand = instance.NodeDemands[n]
		}
		actions[n] = &Action{
			TimeWindowList: CreateTimeWindowList(),
			Node:           n,
			Type:           Drop,
			ServiceTime:    instance.DropServiceTime,
			Request:        nil,
			Demand:         demand,
		}
	}
	for i, n := range instance.Starts {
		demand := 0
		if capacityEnabled {
			demand = -instance.StartUtilizations[i]
		}
		actions[n] = &Action{
			TimeWindowList: CreateTimeWindowList(),
			Node:           n,
			Type:           Start,
			ServiceTime:    0,
			Request:        nil,
			Demand:         demand,
		}
	}
	for _, n := range instance.Ends {
		actions[n] = &Action{
			TimeWindowList: CreateTimeWindowList(),
			Node:           n,
			Type:           End,
			ServiceTime:    0,
			Request:        nil,
			Demand:         0,
		}
	}

	for _, tw := range instance.TimeWindows {
		actions[tw.Node].TimeWindowList.Add(tw)
	}

	requestsLength := len(instance.DeliveriesInProgress) + len(instance.DeliveriesNotStarted)
	requests := make([]*Request, 0, requestsLength)
	for _, d := range instance.DeliveriesInProgress {
		r := Request{
			IsPartial: true,
			Pickup:    nil,
			Drop:      actions[d[1]],
			Courier:   d[0],
		}
		requests = append(requests, &r)
		actions[d[1]].Request = &r
	}
	for _, d := range instance.DeliveriesNotStarted {
		r := Request{
			IsPartial: false,
			Pickup:    actions[d[0]],
			Drop:      actions[d[1]],
			Courier:   0,
		}
		requests = append(requests, &r)
		actions[d[0]].Request = &r
		actions[d[1]].Request = &r
	}

	distanceMatrix := convertMatrixToInt64(instance.CarDistanceMatrix)
	durationMatrix := convertMatrixToInt64(instance.CarDurationMatrix)

	for _, node := range instance.Starts {
		addServiceTimeToDurationMatrix(durationMatrix, &instance, node, false, false)
	}

	for _, node := range instance.PickupNodes {
		addServiceTimeToDurationMatrix(durationMatrix, &instance, node, true, false)
	}

	for _, node := range instance.DropNodes {
		addServiceTimeToDurationMatrix(durationMatrix, &instance, node, false, true)
	}

	return &VRPInstance{
		Actions:           actions,
		Requests:          requests,
		CarDistanceMatrix: distanceMatrix,
		CarDurationMatrix: durationMatrix,
		NumPlansToCreate:  instance.NumPlansToCreate,
		Starts:            instance.Starts,
		Ends:              instance.Ends,
		CourierCapacities: instance.CourierCapacities,
		StartUtilizations: instance.StartUtilizations,
		CapacityEnabled:   capacityEnabled,
		TimeLimit:         int64(instance.TimeLimit),
	}
}

func addServiceTimeToDurationMatrix(durationMatrix [][]int64, instance *VRPInstanceInterface, node int, isPickup bool, isDrop bool) {

	for _, pickupNode := range instance.PickupNodes {
		if !isPickup || durationMatrix[node][pickupNode] != 0 {
			durationMatrix[node][pickupNode] += int64(instance.PickupServiceTime)
		}
	}

	for _, dropNode := range instance.DropNodes {
		if !isDrop || durationMatrix[node][dropNode] != 0 {
			durationMatrix[node][dropNode] += int64(instance.DropServiceTime)
		}
	}
}

func convertMatrixToInt64(matrix [][]float64) [][]int64 {
	newMatrix := make([][]int64, len(matrix))
	for i, v := range matrix {
		newMatrix[i] = convertVectorToInt64(v)
	}
	return newMatrix
}

func convertVectorToInt64(ar []float64) []int64 {
	newArray := make([]int64, len(ar))
	for i, v := range ar {
		newArray[i] = int64(v)
	}
	return newArray
}
