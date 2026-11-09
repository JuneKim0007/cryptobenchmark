"""A provider's behaviour and a shared deviation are stated once and reach exactly the entries and builds they name."""
import shutil

import pytest
import yaml

from cryptobench.catalogue.algorithms import DIRECTORY, AlgorithmsError, load
from cryptobench.catalogue.deviations import DeviationError
from cryptobench.catalogue.views import view_for

KEYSTORE, WORKAROUND = "AndroidKeyStore @ android-26", "AndroidKeyStoreBCWorkaround @ android-{}"
PBE = "Cipher|PBEWithHmacSHA256AndAES_128"
CONSCRYPT = "BundledConscrypt @ org.conscrypt:conscrypt-android:2.5.3"


def test_a_provider_behaviour_reaches_what_it_registers_on_that_build():
    assert view_for("KeyGenerator|AES", KEYSTORE)["key"]["origin"] == "provider"
    assert view_for("KeyAgreement|ECDH", "AndroidKeyStore @ android-33")["contract"]["key"] == "provider"
    assert view_for("KeyAgreement|ECDH", KEYSTORE)["key"]["origin"] == "app"
    assert view_for("Cipher|ChaCha20", WORKAROUND.format(33))["key"]["origin"] == "app"


def test_a_behaviour_field_the_entry_does_not_hold_is_skipped():
    assert "contract" not in view_for("Cipher|RSA/ECB/OAEPPadding", WORKAROUND.format(26))


def test_an_entry_says_otherwise_build_by_build():
    for api, origin in ((26, "provider"), (30, "provider"), (33, "app"), (36, "app")):
        assert view_for("Cipher|RSA/ECB/PKCS1Padding", WORKAROUND.format(api))["key"]["origin"] == origin


def test_a_deviation_reaches_its_names_on_its_builds():
    view = view_for(PBE, CONSCRYPT)
    assert view["contract"]["output"] == {"base": "AES", "mode": "CBC", "padding": "PKCS5Padding"} and view["key"]["bytes"] == [16]
    assert view_for(PBE, "SunJCE @ jdk-25")["contract"]["key"] == "password"


@pytest.fixture
def copy_of(tmp_path):
    target = tmp_path / "algorithms"
    shutil.copytree(DIRECTORY, target)
    path = target / "deviations.yaml"
    return target, path, yaml.safe_load(path.read_text())


def _deviation(**fields):
    return {"fact": "words", "builds": ["BC @ jdk-25"], "names": ["Cipher|AES"], "set": {"key.type": "AES"}, **fields}


def test_two_deviations_stating_one_path_are_refused(copy_of):
    target, path, doc = copy_of
    doc["deviations"].update({"a.one": _deviation(), "a.two": _deviation()})
    path.write_text(yaml.safe_dump(doc))
    with pytest.raises(AlgorithmsError, match="both state key.type"):
        load(target)


def test_a_name_no_catalogue_holds_is_refused(copy_of):
    target, path, doc = copy_of
    doc["deviations"]["a.one"] = _deviation(names=["Cipher|NO-SUCH"])
    path.write_text(yaml.safe_dump(doc))
    with pytest.raises(AlgorithmsError, match="no entry of the catalogues"):
        load(target)


@pytest.mark.parametrize("change, word", [
    (lambda d: d.update(colour="red"), "no term deviation.colour"),
    (lambda d: d.update({"a.one": 1}) if False else d["deviations"].update({"a.one": _deviation(colour="red")}), "no term deviation.colour"),
    (lambda d: d["deviations"].update({"not an id": _deviation()}), "deviation.id"),
    (lambda d: d["deviations"].update({"a.one": _deviation(set={"key.origin": "colour"})}), "key.origin"),
    (lambda d: d["deviations"].update({"a.one": _deviation(builds=["BC 1.81"])}), "BC 1.81"),
])
def test_deviations_are_closed_at_load(copy_of, change, word):
    target, path, doc = copy_of
    change(doc)
    path.write_text(yaml.safe_dump(doc))
    with pytest.raises(DeviationError, match=word):
        load(target)
