def is_sorted(a)
	i = 0
	while i < a.length - 1 && a[i] <= a[i + 1]
	  i += 1
	end

	return i == a.length - 1
  end
