import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.*;
import java.util.*;
import java.util.jar.*;
import javax.tools.*;

/** Generatore degli autori, da avviare dalla radice del repository con un JDK. */
public final class Build {
    private static final String ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
    private static final int[] PERMUTATION = {7, 2, 10, 0, 5, 9, 1, 11, 4, 8, 6, 3};
    private static final int[] KEY = {0x31, 0x5A, 0x17, 0x6C};

    private static void require(boolean condition, String message) {
        if (!condition) throw new IllegalStateException(message);
    }

    private static String sha256(byte[] data) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(data));
    }

    private static String grouped(String value) {
        return value.substring(0, 4) + "-" + value.substring(4, 8) + "-" + value.substring(8);
    }

    private static String canonical(Path privateDir) throws Exception {
        Path config = privateDir.resolve("scenario.properties");
        require(!Files.isSymbolicLink(config), "Configurazione privata: collegamento inatteso.");
        if (!Files.exists(config)) {
            SecureRandom random = new SecureRandom();
            StringBuilder value = new StringBuilder();
            for (int i = 0; i < 12; i++) value.append(ALPHABET.charAt(random.nextInt(ALPHABET.length())));
            String code = value.toString();
            Files.writeString(config, "code=" + code + "\nflag=CRCTF{" + code + "}\n",
                    StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW);
        }
        Properties properties = new Properties();
        try (Reader reader = Files.newBufferedReader(config, StandardCharsets.UTF_8)) {
            properties.load(reader);
        }
        String code = properties.getProperty("code", "");
        require(code.matches("[A-Z0-9]{12}"), "Formato del codice privato non valido; file conservato.");
        require(("CRCTF{" + code + "}").equals(properties.getProperty("flag")),
                "Flag privata incoerente; file conservato.");
        return code;
    }

    private static void compile(List<Path> sources, Path destination) throws Exception {
        JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();
        require(compiler != null, "Serve un JDK, non soltanto un JRE.");
        try (StandardJavaFileManager files = compiler.getStandardFileManager(null, Locale.ROOT,
                StandardCharsets.UTF_8)) {
            boolean ok = compiler.getTask(null, files, null,
                    List.of("--release", "17", "-encoding", "UTF-8", "-g", "-proc:none",
                            "-Xlint:all", "-Werror", "-d", destination.toString()),
                    null, files.getJavaFileObjectsFromPaths(sources)).call();
            require(ok, "Compilazione non riuscita.");
        }
    }

    private record Result(int status, String output) { }

    private static Result execute(List<String> arguments, String input) throws Exception {
        String executable = System.getProperty("os.name").startsWith("Windows") ? "java.exe" : "java";
        List<String> command = new ArrayList<>();
        command.add(Path.of(System.getProperty("java.home"), "bin", executable).toString());
        command.addAll(arguments);
        Process process = new ProcessBuilder(command).redirectErrorStream(true).start();
        try (Writer writer = new OutputStreamWriter(process.getOutputStream(), StandardCharsets.UTF_8)) {
            writer.write(input);
        }
        String output = new String(process.getInputStream().readAllBytes(), StandardCharsets.UTF_8);
        return new Result(process.waitFor(), output);
    }

    private static void entry(JarOutputStream jar, String name, byte[] data) throws IOException {
        JarEntry entry = new JarEntry(name);
        entry.setTime(0L);
        jar.putNextEntry(entry);
        jar.write(data);
        jar.closeEntry();
    }

    private static void createJar(Path classes, Path target, String canonical) throws Exception {
        try (JarOutputStream jar = new JarOutputStream(Files.newOutputStream(target))) {
            String manifest = "Manifest-Version: 1.0\r\nMain-Class: girello.j2.Main\r\n\r\n";
            entry(jar, "META-INF/MANIFEST.MF", manifest.getBytes(StandardCharsets.UTF_8));
            for (String name : List.of("Main", "LicenseValidator", "CodeTransformer")) {
                byte[] bytes = Files.readAllBytes(classes.resolve("girello/j2/" + name + ".class"));
                require(bytes.length > 8 && (bytes[6] & 255) == 0 && (bytes[7] & 255) == 61,
                        "Bytecode diverso dal target Java 17.");
                String content = new String(bytes, StandardCharsets.ISO_8859_1);
                require(!content.contains(canonical) && !content.contains(grouped(canonical))
                                && !content.contains("CRCTF{" + canonical + "}"),
                        "Valore canonico presente in chiaro nel bytecode.");
                entry(jar, "girello/j2/" + name + ".class", bytes);
            }
        }
        try (JarFile jar = new JarFile(target.toFile())) {
            Set<String> expected = Set.of("META-INF/MANIFEST.MF", "girello/j2/Main.class",
                    "girello/j2/LicenseValidator.class", "girello/j2/CodeTransformer.class");
            Set<String> actual = new HashSet<>();
            Enumeration<JarEntry> entries = jar.entries();
            while (entries.hasMoreElements()) {
                JarEntry e = entries.nextElement();
                require(actual.add(e.getName()), "Voce duplicata nel JAR.");
                try (InputStream stream = jar.getInputStream(e)) { stream.readAllBytes(); }
            }
            require(actual.equals(expected), "Contenuto JAR inatteso.");
        }
    }

    public static void main(String[] args) throws Exception {
        require(args.length == 0, "Eseguire senza argomenti dalla radice del repository.");
        Path root = Path.of("").toAbsolutePath().normalize();
        Path challenge = root.resolve("jeopardy/challenges/j2-verifica-licenza");
        Path author = challenge.resolve("author");
        require(Files.exists(root.resolve(".git")) && Files.isRegularFile(author.resolve("src/Main.java")),
                "Eseguire dalla radice del repository Girello.");
        require(ToolProvider.getSystemJavaCompiler() != null, "Serve un JDK con compilatore.");

        Path artifacts = root.resolve("artifacts/j2");
        Path privateDir = artifacts.resolve("private");
        Path build = artifacts.resolve("build");
        for (Path p : List.of(root.resolve("artifacts"), artifacts, privateDir, build)) {
            require(!Files.isSymbolicLink(p), "Directory di output: collegamento inatteso.");
        }
        Files.createDirectories(privateDir);
        Files.createDirectories(build);
        String code = canonical(privateDir);
        Path work = Files.createTempDirectory(build, "work-");
        Path classes = Files.createDirectories(work.resolve("classes"));

        StringJoiner expected = new StringJoiner(", ");
        for (int i = 0; i < 12; i++) {
            int mixed = code.charAt(PERMUTATION[i]) ^ KEY[i % KEY.length];
            expected.add(Integer.toString((mixed + 19 + 7 * i) & 255));
        }
        String template = Files.readString(author.resolve("src/LicenseValidator.java.template"));
        require(template.split("__EXPECTED_VALUES__", -1).length == 2, "Segnaposto template inatteso.");
        Path validator = work.resolve("LicenseValidator.java");
        Files.writeString(validator, template.replace("__EXPECTED_VALUES__", expected.toString()));
        List<Path> sources = List.of(author.resolve("src/Main.java"),
                author.resolve("src/CodeTransformer.java"), validator, author.resolve("BuildChecks.java"));
        compile(sources, classes);

        Result checks = execute(List.of("-cp", classes.toString(), "girello.j2.BuildChecks"), code + "\n");
        require(checks.status() == 0, "Controlli automatici non superati:\n" + checks.output());
        System.out.print(checks.output());
        Path temporaryJar = work.resolve("verifica-licenza.jar");
        createJar(classes, temporaryJar, code);
        Result valid = execute(List.of("-jar", temporaryJar.toString()), grouped(code) + "\n");
        require(valid.status() == 0 && valid.output().contains("Licenza valida."),
                "JAR: percorso valido non riuscito.");
        char alternative = code.charAt(0) == 'A' ? 'B' : 'A';
        Result invalid = execute(List.of("-jar", temporaryJar.toString()),
                grouped(alternative + code.substring(1)) + "\n");
        require(invalid.status() == 1 && invalid.output().contains("Licenza non valida."),
                "JAR: codice errato non rifiutato.");
        Result empty = execute(List.of("-jar", temporaryJar.toString()), "");
        require(empty.status() == 1, "JAR: EOF non gestito.");

        byte[] jarBytes = Files.readAllBytes(temporaryJar);
        String checksum = sha256(jarBytes);
        StringBuilder report = new StringBuilder();
        report.append("JDK di build: ").append(System.getProperty("java.runtime.version")).append('\n');
        report.append("Destinazione: --release 17; class major version 61\n");
        report.append(checks.output());
        report.append("JAR: input corretto, input errato ed EOF verificati\n");
        report.append("JAR: tre classi applicative e manifest; nessun materiale privato\n");
        report.append("Ricostruzione con decompilatore: DA VERIFICARE\n");
        report.append("Dimensione JAR: ").append(jarBytes.length).append(" byte\n");
        report.append("SHA256 JAR: ").append(checksum).append('\n');
        for (String file : List.of("author/Build.java", "author/BuildChecks.java",
                "author/src/Main.java", "author/src/CodeTransformer.java",
                "author/src/LicenseValidator.java.template", "player/README.txt")) {
            report.append(sha256(Files.readAllBytes(challenge.resolve(file))))
                    .append("  ").append(file).append('\n');
        }
        Files.move(temporaryJar, build.resolve("verifica-licenza.jar"), StandardCopyOption.REPLACE_EXISTING);
        Files.writeString(build.resolve("SHA256SUMS"), checksum + "  verifica-licenza.jar\n");
        Files.writeString(build.resolve("build-report.txt"), report.toString());
        // La directory work conserva i sorgenti generati e le classi per le verifiche degli autori.
        System.out.println("JAR creato: artifacts/j2/build/verifica-licenza.jar");
        System.out.println("SHA256: " + checksum);
        System.out.println("Rapporto: artifacts/j2/build/build-report.txt");
        System.out.println("Configurazione privata conservata; codice e flag non vengono stampati.");
        System.out.println("Prossimo controllo: ricostruzione statica dal solo JAR con Vineflower.");
    }
}
