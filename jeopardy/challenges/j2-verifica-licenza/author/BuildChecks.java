package girello.j2;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.Locale;

/** Controlli degli autori: questa classe non viene inclusa nel JAR pubblico. */
public final class BuildChecks {
    private static int checks;

    private static void check(boolean condition, String message) {
        if (!condition) {
            throw new IllegalStateException(message);
        }
        checks++;
    }

    private static String grouped(String normalized) {
        return normalized.substring(0, 4) + "-" + normalized.substring(4, 8)
                + "-" + normalized.substring(8);
    }

    public static void main(String[] args) throws Exception {
        String canonical = new BufferedReader(new InputStreamReader(
                System.in, StandardCharsets.UTF_8)).readLine();
        check(canonical != null && canonical.matches("[A-Z0-9]{12}"),
                "Configurazione privata non valida.");
        String correct = grouped(canonical);
        check(LicenseValidator.isValid(correct), "Codice canonico rifiutato.");
        check(LicenseValidator.isValid(correct.toLowerCase(Locale.ROOT)),
                "Normalizzazione minuscole non valida.");
        check(LicenseValidator.normalize(correct).equals(canonical),
                "Normalizzazione differente dalla configurazione.");

        String[] malformed = {null, "", canonical, " " + correct, correct + " ",
                correct + "\n", correct.replace('-', '_'), correct.replace('-', '\u2013'),
                correct.substring(1), correct + "A", "AAAA-AAAA-AAA!",
                "\uFF21AAA-AAAA-AAAA", "\u0131AAA-AAAA-AAAA", "\u00DFSSS-SSSS-SSSS"};
        for (String value : malformed) {
            check(!LicenseValidator.isValid(value), "Input malformato accettato.");
        }
        String alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
        for (int i = 0; i < canonical.length(); i++) {
            for (char candidate : alphabet.toCharArray()) {
                if (candidate != canonical.charAt(i)) {
                    char[] changed = canonical.toCharArray();
                    changed[i] = candidate;
                    check(!LicenseValidator.isValid(grouped(new String(changed))),
                            "Mutazione del codice accettata.");
                }
            }
        }
        Locale original = Locale.getDefault();
        try {
            Locale.setDefault(Locale.forLanguageTag("tr-TR"));
            check(LicenseValidator.normalize("iiii-iiii-iiii").equals("IIIIIIIIIIII"),
                    "Normalizzazione dipendente dalla lingua del sistema.");
        } finally {
            Locale.setDefault(original);
        }
        System.out.println("Controlli automatici superati: " + checks);
    }
}