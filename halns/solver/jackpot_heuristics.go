package solver

import (
	"math"
	"math/rand"
	"time"
)

type JackpotHeuristics struct{}

func (JackpotHeuristics) String() string {
	return "Jackpot Heuristics"
}

func (JackpotHeuristics) Solve(instance *VRPInstance) (*Solution, error) {
	globalInstance = instance
	rand.Seed(time.Now().UnixNano())

	var bestCost int64 = math.MaxInt64
	var bestSolution *Solution = nil
	var startTime = time.Now().Unix()

	for {
		solution := InsertionHeuristicsSolution()
		if solution.Cost < bestCost {
			bestCost = solution.Cost
			bestSolution = solution
		}
		if globalInstance.TimeLimit > 0 && time.Now().Unix() - startTime > globalInstance.TimeLimit {
			break
		}
	}

	return bestSolution, nil
}
