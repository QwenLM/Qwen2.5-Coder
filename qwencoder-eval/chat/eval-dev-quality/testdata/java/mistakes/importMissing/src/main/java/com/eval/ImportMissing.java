package com.eval;

public class ImportMissing {
	public static int importMissing(List<Integer> input) {
		int sum = 0;

		for (Integer i : input) {
			sum += i;
		}

		return sum;
	}
}
