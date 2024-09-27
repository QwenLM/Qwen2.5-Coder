package com.eval;

class BinarySearch {
	static int binarySearch(int[] a, int x) {
		int index = -1;

		int min = 0;
		int max = a.length - 1;

		while (index == -1 && min <= max) {
			int m = (min + max) / 2;

			if (x == a[m]) {
				index = m;
			} else if (x < a[m]) {
				max = m - 1;
			} else {
				min = m + 1;
			}
		}

		return index;
	}
}
