import shutil
from subprocess import TimeoutExpired, Popen, PIPE
from pylab import *
import time
import os, json
import argparse
import re
from dotenv import dotenv_values


import requests
import threading
from com.dtmilano.android.viewclient import ViewClient
from termcolor import colored

LOCAL_CFG_FILENAME = "CryptoBenchmark.config"
DEVICE_CFG_FILENAME = LOCAL_CFG_FILENAME #"CryptoBenchmark.config"

#CMD="adb shell am instrument -w -m  -e debug false -e class 'com.example.cryptobenchmark.MeasureDigestTest' com.example.cryptobenchmark.test/android.support.test.runner.AndroidJUnitRunner"
CMD="adb shell am instrument -w -m -e debug false -e class 'com.example.cryptobenchmark.{test_class}' {test_package}/{test_runner}"
LOW_BATTERY_LEVEL=31

# Load environment variables from .env file
config = dotenv_values(".env")

REPO_NAME = "cryptobenchmark"
REPO_OWNER = "greensoftwarelab"
REPO_BRANCH = "master"
ACESS_TOKEN = config.get("GITHUB_ACCESS_TOKEN")

def check_update(repo_owner=REPO_OWNER, repo_name=REPO_NAME, branch=REPO_BRANCH, access_token=ACESS_TOKEN):
    if access_token == "":
        print("Please provide a valid access token.")
        return
    # GitHub API endpoint to get the latest commit SHA of the master branch
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/commits/{branch}"
    response = requests.get(url, headers={"Authorization": f"token {access_token}"})
    # Check if the request was successful
    if response.status_code == 200:
        # Extract the latest commit SHA
        latest_commit_sha = response.json()["sha"]
        # Get the latest commit SHA of the local repository
        local_commit = execute_shell_command("git rev-parse HEAD")[1].strip()
        print(latest_commit_sha, local_commit)
        if latest_commit_sha != local_commit:
            print("The repository is not up to date.")
        else:
            print("The repository is up to date.")
            return True
    else:
        print("Failed to fetch latest commit information.")
    return False

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

'''def measure(args_obj):
    em = HunterEManafa()
    for i in range(0, args_obj.n_times):
        em.init()
        em.start()
        res, o , e = execute_shell_command(build_exec_cmd(args_obj))
        print(res)
        print(o)
        print(e)
        if res != 0:
            raise Exception(f"Error while running cmd {CMD}")
        em.stop()
        begin = em.perf_events.events[0].time if len(em.perf_events.events) > 1 else em.bat_events.events[0].time  # first sample from perfetto
        end = em.perf_events.events[-1].time if len(em.perf_events.events) > 1 else em.bat_events.events[-1].time  # first s
        p, c, z = em.get_consumption_in_between(begin, end)
        out_file = em.save_final_report(begin)
        print(f"out file {out_file}")
        print(f"Energy consumed: {p} Joules")
        time.sleep(args_obj.sleep_time)'''


def measure(args_obj):
    #arch -x86_64 python anadroid/main.py -t Custom -cmd "ls -al; sleep 30"'
    cmd_prefix = f'pyanadroid -run -t Custom --n_times {args_obj.n_test_times}  -cmd'
    #print(args_obj.n_times)
    #for i in range(0, args_obj.n_times):
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

def gen_box_plot(key_list, list_of_lists, title="ai"):
    # eg gen_box_plot(['group1', 'group2'], [[1, 2],[3, 4]]):
    fig1, en_box = plt.subplots()
    the_list = list_of_lists
    bp_dict = en_box.boxplot(x=the_list,
                             notch=False,  # notch shape
                             vert=True,  # vertical box aligmnent
                             sym='ko',  # red circle for outliers
                             patch_artist=True,  # fill with color
                             )
    i = 0
    for line in bp_dict['medians']:
        x, y = line.get_xydata()[1]  # top of median line
        xx, yy = line.get_xydata()[0]
        text(x, y, '%.4f' % y, fontsize=5)  # draw above, centered
        # text(xx, en_box.get_ylim()[1] * 0.98, '%.2f' % np.average(list_all_samples[i]), color='darkkhaki')
        i = i + 1

        # set colors
    colors = ['lightblue', 'darkkhaki']
    i = 0
    for bplot in bp_dict['boxes']:
        i = i + 1
        bplot.set_facecolor(colors[i % len(colors)])
    xtickNames = plt.setp(en_box, xticklabels=key_list)
    plt.setp(xtickNames, rotation=90, fontsize=5)
    plt.suptitle(title)
    plt.show()


def plot_res(res):
    print(res)
    filtro = ""
    keys = [ x for x in list(res.keys()) if filtro in x]
    times = [ b['times'] for a,b in res.items() if filtro in a]
    consumptions = [ b['energies'] for a,b in res.items() if filtro in a]
    gen_box_plot(keys, times, "elapsed time " + filtro)
    gen_box_plot(keys, consumptions, "energy")
    #gen_box_plot(['aaa', 'bbb'], [[1,2],[3,5]])

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


def install_apks_pyanadroid(build_type="debug", accept_install=False, retry=True, install_main=True, install_test=True):
    if install_main:
        res, o , e = execute_shell_command(f"pyanadroid install_apk app/build/outputs/apk/{build_type.lower()}/app-{build_type.lower()}*")
        print(o)
        if res != 0 and retry:
            install_apks_pyanadroid(build_type, accept_install=True, retry=False)
    print("installing test apk")
    res, o , e = execute_shell_command(f"adb install_apk app/build/outputs/apk/androidTest/{build_type.lower()}/app-{build_type.lower()}*")
    print(res)
    if res != 0 and retry:
        install_apks_pyanadroid(build_type, accept_install=True, retry=False, install_main=False)


def uninstall_apks(args_obj):
    print("uninstalling apks")
    execute_shell_command("adb shell pm uninstall com.example.cryptobenchmark")
    execute_shell_command(f"adb shell pm uninstall {args_obj.test_package}")


def gen_run_id(args_obj):
    _ , device_name, _ = execute_shell_command("adb shell getprop ro.product.model")
    device_name = device_name.strip().replace(" ", "")
    return f'{device_name}_{args_obj.test_class}_{args_obj.provider}_{args_obj.algorithm}_{args_obj.key_len}_{args_obj.input_size}_{args_obj.algorithm_mode + args_obj.padding}_{args_obj.keyspec}'


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
    print(f"apks are {'not' if not are_apks_installed else ''} installed")
    if args_obj.build or not are_apks_installed:
        build_apks(args_obj)
    if args_obj.install or not are_apks_installed:
        try:
            execute_shell_command("pyanadroid --device unlock_screen")
            install_apks_pyanadroid(args_obj.build_type)
            check_installation()
        except Exception:
            install_apks_pyanadroid(args_obj.build_type)
            check_installation()


def validate_start():
    # validate bluetooth is off
    '''res = execute_shell_command("pyanadroid  --device \"device_state bluetooth\"")
    assert int(res[1].strip()) == 0, "Error: " + res[2]
    # validate conn is wifi
    res = execute_shell_command("pyanadroid  --device conn_type")
    assert 'wifi' in res[1].strip().lower(), colored("Error: Conn is not wifi", 'red')
    # validate installation
    res = execute_shell_command("adb shell pm list packages | grep cryptobenchmark")
    pkgs_count = res[1].count('package:')
    extra_info = 'androidtest apk' if  not 'test' in res[1] else 'main apk'
    assert pkgs_count > 1, colored(f"APKS not installed. Missing {2- pkgs_count} apk. Missing " + extra_info, 'red')
    # validate can unlock screen
    res = execute_shell_command("pyanadroid --device unlock_screen")
    time.sleep(1)
    res, o, _ = execute_shell_command("pyanadroid --device is_screen_unlocked")
    assert "true" in o.lower(), colored("Error: Unable to unlock screen. Please verify if the device can be unlocked without any passcode, pattern or biometric data", 'red')
    '''
    assert check_update(), colored("Error: Repository was updated! Please verify if you need to keep your code up to date ", 'red')

def main(args_obj):
    setup(args_obj)
    exit(0)
    validate_start()
    measure(args_obj)
    files = fetch_res_files(results_dir="anadroid_results/custom_test_results")
    print(files)
    fc = extract_values_from_files(files)
    run_id = gen_run_id(args_obj)
    save_res_in_id_folder(run_id, files)
    print(json.dumps(fc, indent=1))
    if args_obj.uninstall:
        uninstall_apks(args_obj)
    if args_obj.plot:
        plot_res(fc)


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
    parser.add_argument("-p", "--plot", help="plot results", action='store_true', default=False)
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
    args = parser.parse_args()
    print(args.__dict__)
    main(args_obj=args)
