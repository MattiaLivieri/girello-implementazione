import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.time.LocalDateTime;
import java.util.Arrays;
import java.util.Enumeration;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;
import java.util.zip.ZipOutputStream;

/** Confeziona il JAR J2 collaudato e le istruzioni per i partecipanti. */
public final class Package {
    private static void require(boolean condition, String message) {
        if (!condition) throw new IllegalStateException(message);
    }

    private static String hash(byte[] data) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(data));
    }

    private static void verify(Path archive, Map<String, byte[]> expected) throws Exception {
        try (ZipFile zip = new ZipFile(archive.toFile())) {
            Set<String> names = new HashSet<>();
            Enumeration<? extends ZipEntry> entries = zip.entries();
            while (entries.hasMoreElements()) {
                ZipEntry entry = entries.nextElement();
                String name = entry.getName();
                require(names.add(name) && expected.containsKey(name) && !entry.isDirectory(),
                        "Voce inattesa o duplicata nel pacchetto: " + name);
                try (InputStream input = zip.getInputStream(entry)) {
                    require(Arrays.equals(input.readAllBytes(), expected.get(name)),
                            "Contenuto diverso per " + name);
                }
            }
            require(names.equals(expected.keySet()), "File mancanti nel pacchetto.");
        }
    }

    public static void main(String[] args) throws Exception {
        require(args.length == 1 && args[0].matches("[0-9a-fA-F]{64}"),
                "Uso dalla radice del repository: java percorso/Package.java SHA256_JAR_VALIDATO");
        Path root = Path.of("").toAbsolutePath().normalize();
        Path challenge = root.resolve("jeopardy/challenges/j2-verifica-licenza");
        Path jar = root.resolve("artifacts/j2/build/verifica-licenza.jar");
        Path readme = challenge.resolve("player/README.txt");
        require(Files.exists(root.resolve(".git")) && Files.isRegularFile(readme),
                "Eseguire dalla radice del repository Girello.");
        require(Files.isRegularFile(jar) && !Files.isSymbolicLink(jar), "JAR non disponibile.");

        byte[] jarBytes = Files.readAllBytes(jar);
        String jarHash = hash(jarBytes);
        require(jarHash.equalsIgnoreCase(args[0]),
                "Il JAR non coincide con quello collaudato. Nessun pacchetto creato.");
        byte[] readmeBytes = Files.readAllBytes(readme);
        require(readmeBytes.length > 0, "Istruzioni per i partecipanti vuote.");
        String checksums = jarHash + "  verifica-licenza.jar\n"
                + hash(readmeBytes) + "  README.txt\n";

        Map<String, byte[]> content = new LinkedHashMap<>();
        content.put("verifica-licenza.jar", jarBytes);
        content.put("README.txt", readmeBytes);
        content.put("SHA256SUMS", checksums.getBytes(StandardCharsets.US_ASCII));

        Path release = root.resolve("artifacts/j2/release");
        require(!Files.isSymbolicLink(release), "Directory release: collegamento inatteso.");
        Files.createDirectories(release);
        Path archive = release.resolve("j2-verifica-licenza.zip");
        Path checksum = release.resolve("j2-verifica-licenza.zip.sha256");
        require(!Files.isSymbolicLink(archive) && !Files.isSymbolicLink(checksum),
                "File di rilascio: collegamento inatteso.");
        boolean reused = Files.exists(archive);
        if (reused) {
            verify(archive, content);
        } else {
            require(!Files.exists(checksum), "Checksum preesistente senza il relativo ZIP.");
            Path temporary = Files.createTempFile(release, ".j2-", ".tmp");
            try {
                try (ZipOutputStream zip = new ZipOutputStream(Files.newOutputStream(temporary))) {
                    for (Map.Entry<String, byte[]> item : content.entrySet()) {
                        ZipEntry entry = new ZipEntry(item.getKey());
                        entry.setTimeLocal(LocalDateTime.of(2026, 1, 1, 0, 0));
                        zip.putNextEntry(entry);
                        zip.write(item.getValue());
                        zip.closeEntry();
                    }
                }
                verify(temporary, content);
                Files.move(temporary, archive);
            } finally {
                Files.deleteIfExists(temporary);
            }
        }
        String archiveHash = hash(Files.readAllBytes(archive));
        String externalChecksum = archiveHash + "  j2-verifica-licenza.zip\n";
        if (Files.exists(checksum)) {
            require(Files.readString(checksum).equals(externalChecksum),
                    "Checksum esterno incoerente; file conservato.");
        } else {
            Files.writeString(checksum, externalChecksum, StandardOpenOption.CREATE_NEW);
        }
        System.out.println(reused ? "Pacchetto esistente verificato, senza sovrascrittura."
                : "Pacchetto creato e verificato.");
        System.out.println("File: artifacts/j2/release/j2-verifica-licenza.zip");
        System.out.println("Contenuto: verifica-licenza.jar, README.txt, SHA256SUMS");
        System.out.println("Dimensione: " + Files.size(archive) + " byte");
        System.out.println("SHA256 JAR: " + jarHash);
        System.out.println("SHA256 ZIP: " + archiveHash);
        System.out.println("Checksum ZIP conservato separatamente nei materiali degli autori.");
    }
}