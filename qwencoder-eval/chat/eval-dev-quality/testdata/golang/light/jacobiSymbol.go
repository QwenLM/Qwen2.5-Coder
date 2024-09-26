package light

import (
	"fmt"
)

func jacobiSymbol(k, n uint64) (int, error) {
	if k < 0 || n%2 == 0 {
		return 0, fmt.Errorf("Invalid value. k = %d, n = %d", k, n)
	}
	k %= n
	jacobi := 1
	for k > 0 {
		for k%2 == 0 {
			k /= 2
			r := n % 8
			if r == 3 || r == 5 {
				jacobi = -jacobi
			}
		}
		temp := n
		n = k
		k = temp
		if k%4 == 3 && n%4 == 3 {
			jacobi = -jacobi
		}
		k %= n
	}
	if n == 1 {
		return jacobi, nil
	}
	return 0, nil
}
