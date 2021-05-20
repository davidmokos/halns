package main

import (
	"C"
	"encoding/json"
	"fmt"
	"github.com/godeliver/golang-planner/solver"
	"time"
)

func deserializeInstance(input *C.char) (*solver.VRPInstance, error) {
	vrpInterfaceJson := C.GoString(input)
	vrpInterface := solver.VRPInstanceInterface{}
	if err := json.Unmarshal([]byte(vrpInterfaceJson), &vrpInterface); err != nil {
		return nil, err
	}
	vrpInstance := solver.CreateInstance(vrpInterface)
	return vrpInstance, nil
}

func serializeSolution(solution solver.Solution) *C.char {
	solutionInterface := solution.ToSolutionInterface()
	vrpSolutionJson, err := json.Marshal(solutionInterface)
	if err != nil {
		return C.CString(err.Error())
	}
	return C.CString(string(vrpSolutionJson))
}

func solve(input *C.char, s solver.Solver) *C.char {
	vrpInstance, err := deserializeInstance(input)
	if err != nil {
		return C.CString(err.Error())
	}
	fmt.Printf("%s started\n", s.String())
	start := time.Now()
	vrpSolution, err := s.Solve(vrpInstance)
	fmt.Printf("%s finished in %s seconds\n", s.String(), time.Since(start))
	if err != nil {
		return C.CString(err.Error())
	}
	return serializeSolution(*vrpSolution)
}

//export GOInsertionHeuristics
func GOInsertionHeuristics(input *C.char) *C.char {
	planner := solver.InsertionHeuristics{}
	return solve(input, planner)
}

//export JackpotHeuristics
func JackpotHeuristics(input *C.char) *C.char {
	planner := solver.JackpotHeuristics{}
	return solve(input, planner)
}

//export HALNS
func HALNS(input *C.char) *C.char {
	planner := solver.HALNS{}
	return solve(input, planner)
}

func main() {}
