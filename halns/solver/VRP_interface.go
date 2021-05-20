package solver

import (
	"fmt"
	"time"
)

type TimeWindowConstraint struct {
	Node     int   `json:"node"`
	IsHard   bool  `json:"is_hard"`
	FromTime int64 `json:"from_time"`
	ToTime   int64 `json:"to_time"`
	Weight   int64 `json:"weight"`
}

func (tw TimeWindowConstraint) String() string {
	var fromTime = ""
	if tw.FromTime > 0 {
		tm := time.Unix(tw.FromTime, 0)
		fromTime = fmt.Sprintf("%02d:%02d",
			tm.Hour(), tm.Minute())
	}
	var toTime = ""
	if tw.ToTime < MaxTimestampValue {
		tm := time.Unix(tw.ToTime, 0)
		toTime = fmt.Sprintf("%02d:%02d",
			tm.Hour(), tm.Minute())
	}
	var isHard = "soft"
	if tw.IsHard {
		isHard = "hard"
	}
	return fmt.Sprintf("node %d: %s -> %s | %s | %d", tw.Node, fromTime, toTime, isHard, tw.Weight)
}

type VRPInstanceInterface struct {
	CarDistanceMatrix    [][]float64             `json:"car_distance_matrix"`
	CarDurationMatrix    [][]float64             `json:"car_duration_matrix"`
	NumPlansToCreate     int                     `json:"num_plans_to_create"`
	Starts               []int                   `json:"starts"`
	Ends                 []int                   `json:"ends"`
	PickupNodes          []int                   `json:"pickup_nodes"`
	DropNodes            []int                   `json:"drop_nodes"`
	DeliveriesNotStarted [][2]int                `json:"deliveries_not_started"`
	DeliveriesInProgress [][2]int                `json:"deliveries_in_progress"`
	TimeWindows          []*TimeWindowConstraint `json:"time_windows"`
	PickupServiceTime    int                     `json:"pickup_service_time"`
	DropServiceTime      int                     `json:"drop_service_time"`
	PreviousPlans        [][]int                 `json:"previous_plans,omitempty"`
	CourierCapacities    []int                   `json:"courier_capacities,omitempty"`
	StartUtilizations    []int                   `json:"start_utilizations,omitempty"`
	NodeDemands          []int                   `json:"node_demands,omitempty"`
	TimeLimit            int                     `json:"time_limit,omitempty"`
}

type VRPSolutionInterface struct {
	Plans [][]int     `json:"plans"`
	Etas  [][]float64 `json:"etas"`
	Etds  [][]float64 `json:"etds"`
}
