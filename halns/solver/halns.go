package solver

import (
	"fmt"
	"math"
	"math/rand"
	"time"
)

var globalInstance *VRPInstance

type Solver interface {
	Solve(instance *VRPInstance) (*Solution, error)
	String() string
}

type HALNS struct {}

func (halns HALNS) String() string {
	return "HALNS"
}

func (halns HALNS) Solve(instance *VRPInstance) (*Solution, error) {
	globalInstance = instance
	rand.Seed(time.Now().UnixNano())
	solution := halns.mainLoop()
	return solution, nil
}

func (halns HALNS) mainLoop() *Solution {
	removalRoulette := CreateRemovalRoulette()
	insertionRoulette := CreateInsertionRoulette()
	localSearchRoulette := CreateLocalSearchRoulette()
	crossoverRoulette := CreateCrossoverRoulette()

	var currentSolution *Solution = InsertionHeuristicsSolution()
	var bestSolution *Solution = currentSolution

	fmt.Printf("Insertion Heuristics Cost: %d\n", currentSolution.Cost)

	var removeCount = 1
	var foundFeasible = false
	var foundCurrent = false
	var foundBest = false
	var temperature float64 = maxTemperature
	var temperatureBest float64 = 0
	var startTime = time.Now().Unix()

	for i := 0; i < maxIterations; i++ {
		if foundBest {
			removeCount = 1
		} else {
			removeCount = 2
		}

		removed := removalRoulette.PerformRemoval(currentSolution, removeCount)
		inserted := insertionRoulette.PerformInsertion(removed)
		foundFeasible, foundCurrent, foundBest = false, false, false

		if true {
			if inserted.Cost < currentSolution.Cost || halns.isSolutionAccepted(inserted, currentSolution, temperature) {
				currentSolution = inserted
				if inserted.Cost < currentSolution.Cost {
					foundCurrent = true
				} else {
					foundFeasible = true
				}
			} else if inserted.Cost > currentSolution.Cost {
				// or inserted = ... ?
				currentSolution = crossoverRoulette.PerformCrossover(bestSolution, InsertionHeuristicsSolution())
			}
			if inserted.Cost < bestSolution.Cost {
				bestSolution = inserted
				foundBest = true
				temperatureBest = temperature
			} else if float64(inserted.Cost) < float64(bestSolution.Cost)*1.02 {
				localSearchSolution := localSearchRoulette.PerformLocalSearch(inserted)
				if localSearchSolution.Cost < bestSolution.Cost {
					bestSolution = localSearchSolution
					foundBest = true
					temperatureBest = temperature
				}
			}
		}

		if globalInstance.TimeLimit > 0 && time.Now().Unix() - startTime > globalInstance.TimeLimit {
			break
		}

		temperature = temperature * coolingRate
		if temperature < 0.01 {
			temperatureBest = temperatureBest * 2
			temperature = math.Min(maxTemperature, temperatureBest)
		}

		removalRoulette.updateScores(foundCurrent, foundBest, foundFeasible)
		insertionRoulette.updateScores(foundCurrent, foundBest, foundFeasible)

		if i % nSeq == 0 && i != 0 {
			fmt.Printf("iteration %d: best: %d\n", i, bestSolution.Cost)
			removalRoulette.updateProbabilities()
			insertionRoulette.updateProbabilities()
		}

	}
	fmt.Printf("best: %d\n", bestSolution.Cost)

	return bestSolution
}

func (halns HALNS) isSolutionAccepted(new *Solution, current *Solution, temperature float64) bool {
	rnd := RandomFloatRange(0, 1)
	if new != current {
		return rnd < math.Exp(- (float64(new.Cost) - float64(current.Cost)) / temperature)
	}
	return false
}
