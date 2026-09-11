package girello.j2;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;

public final class Main {
    private Main() { }

    public static void main(String[] args) throws IOException {
        if (args.length != 0) {
            System.err.println("Avvia senza argomenti e inserisci il codice quando richiesto.");
            System.exit(2);
        }
        System.out.println("J2 - Verifica licenza");
        System.out.println("Formato: XXXX-XXXX-XXXX; lettere ASCII e cifre, senza spazi.");
        System.out.print("Codice: ");
        System.out.flush();
        BufferedReader input = new BufferedReader(
                new InputStreamReader(System.in, StandardCharsets.UTF_8));
        String code = input.readLine();
        if (LicenseValidator.isValid(code)) {
            System.out.println("Licenza valida.");
        } else {
            System.out.println("Licenza non valida.");
            System.exit(1);
        }
    }
}
