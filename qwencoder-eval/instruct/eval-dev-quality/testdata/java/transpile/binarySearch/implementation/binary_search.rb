def binary_search(a, x)
	index = -1

	min = 0
	max = a.length - 1

	while index == -1 && min <= max
		m = (min + max) / 2

		if x == a[m]
			index = m
		elsif x < a[m]
			max = m - 1
		else
			min = m + 1
		end
	end

	return index
end
