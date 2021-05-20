package solver

import (
	"math/rand"
)

func Max(x, y int64) int64 {
	if x < y {
		return y
	}
	return x
}

func InsertInPlace(a *[]int, c int, i int) {
	last := len(*a) - 1
	if i > last {
		*a = append(*a, c)
	} else {
		*a = append(*a, (*a)[last])
		copy((*a)[i+1:], (*a)[i:last])
		(*a)[i] = c
	}
}

func Insert(a []int, c int, i int) []int {
	var ret []int
	for idx, v := range a {
		if i == idx {
			ret = append(ret, c)
		}
		ret = append(ret, v)
	}
	if i >= len(a) {
		ret = append(ret, c)
	}
	return ret
}

func Shuffle(a []int) []int {
	ret := append([]int{}, a...)
	rand.Shuffle(len(ret), func(i, j int) { ret[i], ret[j] = ret[j], ret[i] })
	return ret
}

func RandomRange(min int, max int) int {
	return rand.Intn(max - min) + min
}

func RandomFloatRange(min, max float64) float64 {
	return min + rand.Float64() * (max - min)
}

