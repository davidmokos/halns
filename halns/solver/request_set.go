package solver

import (
	"fmt"
	"strings"
)

type RequestSet map[*Request]bool

func NewRequestSet() RequestSet {
	return make(RequestSet)
}

func RequestSetFromList(requests []*Request) RequestSet {
	ret := make(RequestSet)
	for _, r := range requests {
		ret.Add(r)
	}
	return ret
}

func (requestSet *RequestSet) Add(request *Request) {
	(*requestSet)[request] = true
}

func (requestSet *RequestSet) Delete(request *Request) {
	delete(*requestSet, request)
}

func (requestSet *RequestSet) Size() int {
	return len(*requestSet)
}

func (requestSet *RequestSet) Intersection(another *RequestSet) RequestSet {
	newSet := make(RequestSet)
	for r := range *requestSet {
		if another.Contains(r) {
			newSet.Add(r)
		}
	}
	return newSet
}

func (requestSet *RequestSet) Union(another *RequestSet) RequestSet {
	newSet := make(RequestSet)
	for r := range *requestSet {
		newSet.Add(r)
	}
	for r := range *another {
		newSet.Add(r)
	}
	return newSet
}

func (requestSet *RequestSet) Contains(request *Request) bool {
	_, ok := (*requestSet)[request]
	return ok
}

func (requestSet *RequestSet) Copy() RequestSet {
	newRequestSet := make(RequestSet)
	for k := range *requestSet {
		newRequestSet[k] = true
	}
	return newRequestSet
}

func (requestSet *RequestSet) AddAll(another *RequestSet) {
	for k := range *another {
		requestSet.Add(k)
	}
}

func (requestSet *RequestSet) ToList() []*Request {
	requestList := make([]*Request, 0, requestSet.Size())
	for r := range *requestSet {
		requestList = append(requestList, r)
	}
	return requestList
}

func (requestSet *RequestSet) String() string {
	var b strings.Builder
	for r := range *requestSet {
		_, _ = fmt.Fprintf(&b, "%s, ", r)
	}
	s := b.String()
	if b.Len() > 2 {
		s = s[:b.Len()-2]
	}
	return s
}
