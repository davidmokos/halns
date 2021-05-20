package solver

import (
	"math/rand"
	"time"
)

type InsertionHeuristics struct{}

func (insertion InsertionHeuristics) String() string {
	return "Insertion Heuristics"
}

func (InsertionHeuristics) Solve(instance *VRPInstance) (*Solution, error) {
	globalInstance = instance
	rand.Seed(time.Now().UnixNano())
	solution := InsertionHeuristicsSolution()
	return solution, nil
}
