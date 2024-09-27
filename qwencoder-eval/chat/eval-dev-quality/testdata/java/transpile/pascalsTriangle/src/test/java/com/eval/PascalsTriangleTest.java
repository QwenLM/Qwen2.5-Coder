package com.eval;

import org.junit.jupiter.api.*;
import static org.junit.jupiter.api.Assertions.*;
import org.apache.commons.lang3.builder.EqualsBuilder;

public class PascalsTriangleTest {
	@Test
	public void generateTriangle1() {
		PascalsTriangle p = new PascalsTriangle();
		int rows = -1;
		assertThrows(IllegalArgumentException.class, () -> {
			p.generateTriangle(rows);
		});
	}

	@Test
	public void generateTriangle2() {
		PascalsTriangle p = new PascalsTriangle();
		int rows = 0;
		int[][] expected = {};
		int[][] actual = p.generateTriangle(rows);

		assertTrue(EqualsBuilder.reflectionEquals(expected, actual, false, null, true));
	}

	@Test
	public void generateTriangle3() {
		PascalsTriangle p = new PascalsTriangle();
		int rows = 1;
		int[][] expected = { { 1 } };
		int[][] actual = p.generateTriangle(rows);

		assertTrue(EqualsBuilder.reflectionEquals(expected, actual, false, null, true));
	}

	@Test
	public void generateTriangle4() {
		PascalsTriangle p = new PascalsTriangle();
		int rows = 5;
		int[][] expected = { { 1 }, { 1, 1 }, { 1, 2, 1 }, { 1, 3, 3, 1 }, { 1, 4, 6, 4, 1 } };
		int[][] actual = p.generateTriangle(rows);

		assertTrue(EqualsBuilder.reflectionEquals(expected, actual, false, null, true));
	}
}
