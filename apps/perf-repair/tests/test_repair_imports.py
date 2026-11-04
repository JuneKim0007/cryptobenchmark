from perfrepair.repair.dependencies import dependencies, load
from perfrepair.repair.imports import used_imports
from perfrepair.source import language

JAVA = ["import java.util.Arrays;", "import javax.crypto.Cipher;", "import static a.b.Hex.encode;", "import a.b.Unused;",
        "import c.d.*;", "import androidx.annotation.NonNull;"]


def pruned(function, imports, lang=language.JAVA):
    names = load(lang.name)
    deps = dependencies(function, lang, imports, names)
    return used_imports(imports, [function], lang, names, deps)


def test_only_imports_whose_names_the_function_uses_are_kept():
    f = "@NonNull byte[] f(byte[] in) throws Exception {\n  return encode(Cipher.getInstance(\"AES\").doFinal(in));\n}\n"
    assert pruned(f, JAVA) == ["import javax.crypto.Cipher;", "import static a.b.Hex.encode;"]


def test_a_wildcard_stays_only_while_a_name_is_unresolved():
    f = "byte[] f(byte[] in) throws Exception {\n  return Helper.go(Arrays.copyOf(in, 1));\n}\n"
    assert pruned(f, JAVA) == ["import java.util.Arrays;", "import c.d.*;"]


def test_kotlin_keeps_aliases_extensions_and_operator_conventions():
    imports = ["import a.b.Hex as H", "import a.b.toHex", "import a.b.getValue", "import a.b.Unused"]
    f = "fun f(b: ByteArray): String {\n  val k by lazy { b }\n  return H.x(k).toHex()\n}\n"
    assert pruned(f, imports, language.KOTLIN) == imports[:3]
