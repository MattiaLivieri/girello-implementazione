package girello.j2;

public final class CodeTransformer {
    private static final int[] PERMUTATION = {7, 2, 10, 0, 5, 9, 1, 11, 4, 8, 6, 3};
    private static final int[] KEY = {0x31, 0x5A, 0x17, 0x6C};

    private CodeTransformer() { }

    static int[] permute(String normalized) {
        if (normalized.length() != PERMUTATION.length) {
            throw new IllegalArgumentException("Lunghezza del codice non valida.");
        }
        int[] result = new int[PERMUTATION.length];
        for (int i = 0; i < result.length; i++) {
            result[i] = normalized.charAt(PERMUTATION[i]);
        }
        return result;
    }

    static int[] encode(int[] values) {
        if (values.length != PERMUTATION.length) {
            throw new IllegalArgumentException("Lunghezza del codice non valida.");
        }
        int[] result = new int[values.length];
        for (int i = 0; i < result.length; i++) {
            int mixed = values[i] ^ KEY[i % KEY.length];
            result[i] = (mixed + 19 + 7 * i) & 0xFF;
        }
        return result;
    }
}
