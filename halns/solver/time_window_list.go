package solver

import "sort"

const MaxTimestampValue = 2147483647

type TimeWindowList struct {
	TimeWindows []*TimeWindowConstraint
	MaxFromTime int64
	MinToTime   int64
	Weights [][]int64
	HasToArriveBy int64
}

func CreateTimeWindowList() *TimeWindowList {
	return &TimeWindowList{
		TimeWindows: []*TimeWindowConstraint{},
		MaxFromTime: 0,
		MinToTime:   MaxTimestampValue,
		Weights:     [][]int64{},
		HasToArriveBy: MaxTimestampValue,
	}
}

type ByToTime []*TimeWindowConstraint

func (s ByToTime) Len() int {
	return len(s)
}

func (s ByToTime) Swap(i, j int) {
	s[i], s[j] = s[j], s[i]
}

func (s ByToTime) Less(i, j int) bool {
	return s[i].ToTime < s[j].ToTime
}


func (twList *TimeWindowList) Add(tw *TimeWindowConstraint) {
	twList.TimeWindows = append(twList.TimeWindows, tw)
	sort.Sort(ByToTime(twList.TimeWindows))

	if tw.FromTime > twList.MaxFromTime {
		twList.MaxFromTime = tw.FromTime
	}
	if tw.ToTime < twList.MinToTime {
		twList.MinToTime = tw.ToTime
	}

	if tw.IsHard && twList.HasToArriveBy > tw.ToTime {
		twList.HasToArriveBy = tw.ToTime
	}

	twList.Weights =  [][]int64{}
	var weight int64 = 0

	twList.Weights = append(twList.Weights, []int64 {0, weight})
	for _, tw := range twList.TimeWindows {
		if tw.ToTime < MaxTimestampValue {
			weight += tw.Weight
			twList.Weights = append(twList.Weights, []int64 {tw.ToTime, weight})
		}
	}
	twList.Weights = append(twList.Weights, []int64 {MaxTimestampValue, weight})
}

func (twList *TimeWindowList) IsArrivalFeasible(eta int64) bool {
	return eta <= twList.HasToArriveBy
}

func (twList *TimeWindowList) GetPenaltyForArrivalAt(eta int64) int64 {
	for idx, tw := range twList.Weights {
		if eta < tw[0] {
			return (eta - twList.Weights[idx-1][0]) * twList.Weights[idx-1][1]
		}
	}

	// we should never reach this position, as the item in the array is always weight with MaxTimestampValue
	return 0
}
