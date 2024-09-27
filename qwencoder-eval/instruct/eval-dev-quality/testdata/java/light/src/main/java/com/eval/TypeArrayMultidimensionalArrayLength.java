package com.eval;

class TypeArrayMultidimensionalArrayLength {
    static int typeArrayMultidimensionalArrayLength(int[][] x) {
        if (x.length == 2) {
            if (x[0].length == 2) {
                return 2;
            }

            return 1;
        }

        return 0;
    }
}
