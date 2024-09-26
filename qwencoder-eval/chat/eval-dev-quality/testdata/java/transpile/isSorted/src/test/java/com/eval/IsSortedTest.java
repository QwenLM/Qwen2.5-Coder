package com.eval;

import org.junit.jupiter.api.*;
import static org.junit.jupiter.api.Assertions.*;

public class IsSortedTest {

	@Test
	public void isSorted1() {
		int[] a = {};
		boolean actual = IsSorted.isSorted(a);

		assertFalse(actual);
	}

	@Test
	public void isSorted2() {
		int[] a = { 5, 4, 3, 2, 1 };
		boolean actual = IsSorted.isSorted(a);

		assertFalse(actual);
	}

	@Test
	public void isSorted3() {
		int[] a = { 0 };
		boolean actual = IsSorted.isSorted(a);

		assertTrue(actual);
	}

	@Test
	public void isSorted4() {
		int[] a = { 1, 2, 3, 4, 5 };
		boolean actual = IsSorted.isSorted(a);

		assertTrue(actual);
	}

	@Test
	public void isSorted5() {
		int[] a = { 1, 2, 10, 11, 20, 21 };
		boolean actual = IsSorted.isSorted(a);

		assertTrue(actual);
	}
}
