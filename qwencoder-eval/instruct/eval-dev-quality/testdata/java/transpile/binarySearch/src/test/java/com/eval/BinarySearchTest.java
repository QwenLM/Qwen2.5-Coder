package com.eval;

import org.junit.jupiter.api.*;
import static org.junit.jupiter.api.Assertions.*;

public class BinarySearchTest {

	@Test
	public void binarySearch1() {
		int[] a = {};
		int x = 0;
		int expected = -1;
		int actual = BinarySearch.binarySearch(a, x);

		assertEquals(expected, actual);
	}

	@Test
	public void binarySearch2() {
		int[] a = { 0 };
		int x = 5;
		int expected = -1;
		int actual = BinarySearch.binarySearch(a, x);

		assertEquals(expected, actual);
	}

	@Test
	public void binarySearch3() {
		int[] a = { 1, 2, 3, 4, 5 };
		int x = 6;
		int expected = -1;
		int actual = BinarySearch.binarySearch(a, x);

		assertEquals(expected, actual);
	}

	@Test
	public void binarySearch4() {
		int[] a = { 1, 2, 3, 4, 5 };
		int x = 3;
		int expected = 2;
		int actual = BinarySearch.binarySearch(a, x);

		assertEquals(expected, actual);
	}

	@Test
	public void binarySearch5() {
		int[] a = { 1, 5, 10, 15, 20, 25 };
		int x = 25;
		int expected = 5;
		int actual = BinarySearch.binarySearch(a, x);

		assertEquals(expected, actual);
	}
}
