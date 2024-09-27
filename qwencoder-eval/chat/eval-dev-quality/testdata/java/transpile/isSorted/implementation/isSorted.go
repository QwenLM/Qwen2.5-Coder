package isSorted

func isSorted(a []int) bool {
	i := 0
	for i < len(a)-1 && a[i] <= a[i+1] {
		i++
	}

	return i == len(a)-1
}
