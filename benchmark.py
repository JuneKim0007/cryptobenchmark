import shutil
from subprocess import TimeoutExpired, Popen, PIPE
from pylab import *
import time
import os, json
import argparse
import re
import threading
from com.dtmilano.android.viewclient import ViewClient
from termcolor import colored

LOCAL_CFG_FILENAME = "CryptoBenchmark.config"
DEVICE_CFG_FILENAME = LOCAL_CFG_FILENAME #"CryptoBenchmark.config"

#CMD="adb shell am instrument -w -m  -e debug false -e class 'com.example.cryptobenchmark.MeasureDigestTest' com.example.cryptobenchmark.test/android.support.test.runner.AndroidJUnitRunner"
CMD="adb shell am instrument -w -m -e debug false -e class 'com.example.cryptobenchmark.{test_class}' {test_package}/{test_runner}"

LOW_BATTERY_LEVEL=31


def is_screen_unlocked():
    """Checks if screen is unlocked.
    Returns:
        bool: True if unlocked, False otherwise.
    """
    res = execute_shell_command("pyanadroid -dev is_screen_unlocked", args=[])
    is_locked = "true" in res[1].lower()
    return is_locked

def unlock_screen(pwd=None):
    """unlock device screen.
    Tries several approaches to unlock screen. It starts by trying to press lock button, followed by trying
    to type a password if a password is required. If none of these worked, tries to press menu button and finally,
    it tries to perform a swipe up.
    Args:
        pwd: password to provide if devices requires password to be unlocked.
    """
    cmd = f'pyanadroid -dev unlock_screen'
    #print(args_obj.n_times)
    #for i in range(0, args_obj.n_times):
    res, o , e = execute_shell_command(cmd)
    


def has_to_click_to_install(serial_nr):
    vc = ViewClient(*ViewClient.connectToDeviceOrExit(serialno=serial_nr))
    try:
        vc.findViewByIdOrRaise('com.google.securitycenter:id/name')
    except:
        try:
            vc.findViewByIdOrRaise('com.miui.securitycenter:id/name')
        except:
            return False
    return True


def click_to_install(serial_nr):
    vc = ViewClient(*ViewClient.connectToDeviceOrExit(serialno=serial_nr))
    res = vc.findViewByIdOrRaise('android:id/button2')
    res.touch()


def background_installer():
    serial_nr = get_device_serial()
    print(f"serial: {serial_nr}")
    time.sleep(2)
    if has_to_click_to_install(serial_nr):
        click_to_install(serial_nr)


def get_device_serial():
    res, o, e = execute_shell_command("adb devices | awk 'NR==2 {print $1}'")
    return o.strip()


def execute_shell_command(cmd, args=[], timeout=None):
    command = cmd + " " + " ".join(args) if len(args) > 0 else cmd
    out = bytes()
    err = bytes()
    #print(command)
    proc = Popen(command, stdout=PIPE, stderr=PIPE, shell=True)
    try:
        out, err = proc.communicate(timeout=timeout)
    except TimeoutExpired as e:
        print("command " + cmd + " timed out")
        out = e.stdout if e.stdout is not None else out
        err = e.stderr if e.stderr is not None else err
        proc.kill()
        proc.returncode = 1
    return proc.returncode, out.decode("utf-8", errors='replace'), err.decode("utf-8", errors='replace')


def measure(args_obj):
    #arch -x86_64 python anadroid/main.py -t Custom -cmd "ls -al; sleep 30"'
    cmd_prefix = f'pyanadroid -run -t Custom --n_times {args_obj.n_test_times}  -cmd'
    cmd = f'{cmd_prefix} \"{build_exec_cmd(args_obj)}\"'
    print(f"performing command: {cmd}")
    start=time.time()
    res, o , e = execute_shell_command(cmd)
    print(f"elapsed time: {time.time() - start} secs")
    print(res)
    #print(o)
    #print(e)
    if res != 0:
        print(o)
        print(e)
        raise Exception(f"Error while running cmd {CMD}")
    '''else:
        res_files0 = list(filter(lambda x: '0' in x, fetch_res_files(results_dir="anadroid_results/custom_test_results")))
        for f in res_files0:
            shutil.move(f, f.replace('0', f'{i}'))'''
    time.sleep(args_obj.sleep_time)


def fetch_res_files(results_dir=""):
    return [os.path.join(results_dir, x) for x in os.listdir(results_dir) if 'manafa_res' in x or '.logcat' in x or '_state' ]


def parse_json(filepath):
    js = {}
    with open(filepath, 'r') as j:
        js = json.load(j)
    return js

def extract_values_from_files(files):
    rm_val = " " #"MeasureSymmetricTest_test_"
    function_dict = {}
    jsons = [parse_json(x) for x in files if '.json' in x and 'resume' in x]
    for j_file in jsons:
        if not 'invoked_methods' in j_file:
            continue
        #print(json.dumps(j_file['invoked_methods'], indent=1))
        for method, invs in j_file['invoked_methods'].items():
            mname = method.replace(rm_val, "")
            for invok in invs.values():
                print(invok)
                if 'elapsed_time' in invok:
                    function_dict[mname] = {'times': [invok['elapsed_time']], 'energies': [invok['cpu']]} if mname not in function_dict else {'times': function_dict[mname]['times'] + [invok['elapsed_time']] , 'energies': function_dict[mname]['energies'] + [invok['cpu']]}
    return function_dict


def build_apks(args_obj):
    print("building")
    res, o , e = execute_shell_command(build_build_cmd(args_obj))
    if res == 1:
        print(res)
        print(o)
        print(e)
        print(colored("build failed. Interrupting procedure",'red'))
        exit(-1)
    #print(o)

def install_apks(build_type="debug", accept_install=False, retry=True, install_main=True, install_test=True):
    if install_main:
        if accept_install:
            unlocked = is_screen_unlocked()
            if not unlocked:
                unlock_screen()
            thread1 = threading.Thread(target=background_installer)
            thread1.start()
        print("installing main apk")
        res, o , e = execute_shell_command(f"adb install -g -r app/build/outputs/apk/{build_type.lower()}/app-{build_type.lower()}*")
        print(res)
        if res != 0 and retry:
            install_apks(build_type, accept_install=True, retry=False)
    if accept_install:
        unlocked = is_screen_unlocked()
        if not unlocked:
            unlock_screen()
        thread2 = threading.Thread(target=background_installer)
        thread2.start()
    print("installing test apk")
    res, o , e = execute_shell_command(f"adb install -g -r app/build/outputs/apk/androidTest/{build_type.lower()}/app-{build_type.lower()}*")
    print(res)
    if res != 0 and retry:
        unlock_screen()
        install_apks(build_type, accept_install=True, retry=False, install_main=False)
    #print(o)
    #print(o)
    #print(e)
    

def uninstall_apks(args_obj):
    print("uninstalling apks")
    execute_shell_command("adb shell pm uninstall com.example.cryptobenchmark")
    execute_shell_command(f"adb shell pm uninstall {args_obj.test_package}")


def gen_run_id(args_obj):
    _ , device_name, _ = execute_shell_command("adb shell getprop ro.product.model")
    device_name = device_name.strip().replace(" ", "")
    return f'{device_name}_{args_obj.test_class}_{args_obj.provider}_{args_obj.algorithm}_{args_obj.key_len}_{args_obj.input_size}_{args_obj.algorithm_mode + args_obj.padding}_{args_obj.keyspec}'



def already_measured_run(run_id):
    return os.path.exists(run_id) and os.path.isdir(run_id)


def save_res_in_id_folder(run_id, file_list):
    print(f"lista files: {file_list}")
    if not os.path.exists(run_id):
        os.mkdir(run_id)
    for f in file_list:
        shutil.copy(f, os.path.join(run_id, os.path.basename(f)))
    pull_config_file(run_id)


def check_installation():
    _, o, _ = execute_shell_command("adb shell pm list packages | grep benchmark")
    #print(o)
    if len(str(o).split('package')) <= 2:
        raise Exception("APKs were not installed.")

def get_battery_level():
    x = execute_shell_command("pyanadroid --device get_battery_level")
    return int(x[1].strip()) if x[0] == 0 else 0


def push_config_file():
    execute_shell_command(f"adb push {LOCAL_CFG_FILENAME} /sdcard/{DEVICE_CFG_FILENAME}")


def pull_config_file(target_dir=""):
    execute_shell_command(f"adb pull /sdcard/{DEVICE_CFG_FILENAME} {os.path.join(target_dir, LOCAL_CFG_FILENAME)}")


def validate_apks_installed():
    res, o, _ = execute_shell_command("adb shell pm list packages | grep benchmark")
    return res == 0 and o.count('package:') > 1


def setup(args_obj):
    if get_battery_level() <= LOW_BATTERY_LEVEL:
        bat_level = get_battery_level()
        print(colored(f"low battery: {bat_level}% {'' if bat_level != 0 else '(Disconnected)'}. Aborting", 'red'))
        exit(0)
    save_config_file(args_obj)
    push_config_file()
    are_apks_installed = validate_apks_installed()
    if args_obj.build or not are_apks_installed:
        build_apks(args_obj)
    if args_obj.install or not are_apks_installed:
        try:
            execute_shell_command("pyanadroid --device unlock_screen")
            install_apks(args_obj.build_type)
            check_installation()
        except Exception:
            install_apks(args_obj.build_type)
            check_installation()


def validate_start():
    # validate bluetooth is off
    res = execute_shell_command("pyanadroid  --device \"device_state bluetooth\"")
    assert int(res[1].strip()) == 0, "Error: " + res[2]
    # validate conn is wifi
    res = execute_shell_command("pyanadroid  --device conn_type")
    assert 'wifi' in res[1].strip().lower(), "Error: " + res[2]
    # validate installation
    res = execute_shell_command("adb shell pm list packages | grep cryptobenchmark")
    pkgs_count = res[1].count('package:')
    extra_info = 'androidtest apk' if  not 'test' in res[1] else 'main apk'
    assert pkgs_count > 1, f"APKS not installed. Missing {2- pkgs_count} apk. Missing " + extra_info


def has_enough_tests(run_id, n_times):
    return len([x for x in os.listdir(run_id) if 'logresume.json' in x]) >= n_times

def main(args_obj):
    setup(args_obj)
    if not args_obj.skip_validation:
        validate_start()
    run_id = gen_run_id(args_obj)
    if (already_measured_run(run_id) and not args_obj.repeat_measurements 
            and has_enough_tests(run_id, args_obj.n_test_times)):
        print(colored(f"run {run_id} already measured. Aborting", 'yellow'))
        exit(0)
    clean_up()
    measure(args_obj)
    analyze_results(run_id)
    if args_obj.uninstall:
        uninstall_apks(args_obj)


def clean_up():
    remove_all_content("anadroid_results")

def remove_all_content(directory):
    """
    Remove all files and subdirectories within a directory.
    
    Parameters:
        directory (str): The path to the directory.
    """
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        if os.path.isfile(item_path):
            os.remove(item_path)
        elif os.path.isdir(item_path):
            remove_all_content(item_path)
            os.rmdir(item_path)
    

def analyze_results(run_id):
    files = fetch_res_files(results_dir="anadroid_results/custom_test_results")
    fc = extract_values_from_files(files)
    save_res_in_id_folder(run_id, files)
    print(json.dumps(fc, indent=1))



def build_exec_cmd(args_obj):
    return CMD.format(test_class=args_obj.test_class, 
    test_runner=args_obj.test_runner,
    test_package=args_obj.test_package)


def build_build_cmd(args_obj):
    prop_keys = get_keys_of_prop_file()
    prop_fmt_keys = list(filter(lambda x: x.upper() in prop_keys, args_obj.__dict__.keys()))
    res = " ".join([f"-P{k.upper()}={args_obj.__dict__[k]}" for k in prop_fmt_keys])
    cmd = f"./gradlew assemble{args_obj.build_type} assembleAndroidTest {res} -DtestBuildType={args_obj.build_type.lower()}"
    print(f"build command: {cmd}")
    return cmd


def save_config_file(args_obj):
    with open(DEVICE_CFG_FILENAME, 'w') as f:
        f.write('\n'.join([f"{k.upper()}={v}" for k,v in args_obj.__dict__.items()]))


def get_configs():
    with open(DEVICE_CFG_FILENAME, 'r') as f:
        return {x.split('=')[0].lower(): x.split('=')[1] for x in f.readlines() if '=' in x}

def fetch_from_gradle_prop_file(key, default_val):
    with open('gradle.properties') as f:
        for line in f:
                # Split the line into a key-value pair
                try:
                    k, v = line.strip().split('=')
                    if k == key and v != '':
                        return v
                except:
                    continue   
        # If no matching key is found, return the default value
        return default_val


def get_keys_of_prop_file():
    x = []
    with open('gradle.properties') as f:
        for line in f:
                # Split the line into a key-value pair
                try:
                    k = line.strip().split('=')[0]
                    x.append(k)
                except:
                    continue
        return x


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--build", help="build", action='store_true', default=False)
    parser.add_argument("-bt", "--build_type", help="build type", type=str, choices=['Debug', 'Release'], default="Release")
    parser.add_argument("-i", "--install", help="install apks", action='store_true', default=False)
    parser.add_argument("-u", "--uninstall", help="uninstall apks", action='store_true', default=False)
    parser.add_argument("-c", "--test_class", help="test class", default="DigestTest", type=str)
    parser.add_argument("-r", "--test_runner", help="unit test runner", default="androidx.test.runner.AndroidJUnitRunner", choices=["android.support.test.runner.AndroidJUnitRunner", "androidx.test.runner.AndroidJUnitRunner", "androidx.test.ext.junit.runners.AndroidJUnit4"])
    parser.add_argument("-tp", "--test_package", help="test package",  default="com.example.cryptobenchmark.test")
    parser.add_argument("-ntt", "--n_test_times", help="times to repeat each test execution",  default=1, type=int)
    parser.add_argument("-nt", "--n_times", help="times to repeat each algorithm execution",  default=1, type=int)
    parser.add_argument("-s", "--sleep_time", help="time to sleep betweeen each execution",  default=3, type=int)
    parser.add_argument("-pv", "--provider", help="crypto provider", default=fetch_from_gradle_prop_file("PROVIDER", "AndroidOpenSSL"), type=str)
    parser.add_argument("-is", "--input_size", help="input size",  default=fetch_from_gradle_prop_file("INPUT_SIZE", 128), type=int)
    parser.add_argument("-kl", "--key_len", help="key length",  default=fetch_from_gradle_prop_file("KEY_LEN", 128), type=int)
    parser.add_argument("-a", "--algorithm", help="algorithm to execute",  default=fetch_from_gradle_prop_file("ALGORITHM", ""), type=str)
    parser.add_argument("-m", "--algorithm_mode", help="algorithm mode",  default=fetch_from_gradle_prop_file("MODE", ""), type=str)
    parser.add_argument("-pd", "--padding", help="algorithm padding",  default=fetch_from_gradle_prop_file("PADDING", ""), type=str)
    parser.add_argument("-ks", "--keyspec", help="keyspec",  default=fetch_from_gradle_prop_file("WITH_KEY_SPEC", 0), type=int)
    parser.add_argument("-rp", "--repeat_measurements", help="repeat measurements",  action='store_true', default=False)
    parser.add_argument("-skv", "--skip_validation", help="skip start validation",  action='store_true', default=False)
    args = parser.parse_args()
    print(args.__dict__)
    main(args_obj=args)
