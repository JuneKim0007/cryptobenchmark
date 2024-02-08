import json, os
import shutil
from pylab import *
import time
from collections import OrderedDict
import re
import argparse
from functools import reduce


def has_error_on_method(m_id, log_file):

    #print("--")
    #print(log_file)
    pattern = f'(?s)>{m_id}(.*?)<{m_id}'
    with open(log_file, 'r') as file:
        content = file.read()
        matches = re.findall(r""+pattern, content)
    #print(matches)
    return len(list(filter(lambda x: 'xception' 
                           in str(x) or 'error' in str(x).lower(), matches))) > 0
    

    
def process_config_folder(fldr):
    """checks if results dir contains valid results by inspecting logfile 
    and checking for missing result files. produces .validated files with valid method calls"""
    files = [os.path.join(fldr, x) for x in os.listdir(fldr) if '_resume' in x and '.validated' not in x]
    valids = 0
    for file in files:
        if os.path.exists(file + ".validated"):
            continue
        test_id = file.split("_")[-1].replace(".json", "")
        matching_logcat_files =  [os.path.join(fldr, x) for x in os.listdir(fldr) if test_id in x and 'logcat' in x]
        if len(matching_logcat_files) == 0:
            os.remove(file)
            continue
        valids +=1
        matching_logcat_file = matching_logcat_files[0]
        #invoked_m_info = extract_values_from_files([file])
        json_content = parse_json(file)
        for method_inv in list(json_content['invoked_methods'].keys()):
            # assume that errors occur on all tests
            if has_error_on_method(method_inv, matching_logcat_file):
                print(f"exec invalida: {method_inv}")
                json_content['invoked_methods'].pop(method_inv)
                continue
            for indiv_exec in list(json_content['invoked_methods'][method_inv].keys()):
                is_unchecked = 'checked' in json_content['invoked_methods'][method_inv][indiv_exec] and not json_content['invoked_methods'][method_inv][indiv_exec]['checked']
                if is_unchecked:
                    json_content['invoked_methods'][method_inv].pop(indiv_exec)

        with open(file + '.validated', 'w') as jfile:
            json.dump(json_content, jfile, indent=1)
    return len(json_content['invoked_methods']) > 0 if valids > 0 else True

def parse_json(filepath):
    js = {}
    with open(filepath, 'r') as j:
        js = json.load(j)
    return js

'''
def extract_values_from_files(files):
    rm_val = "" #"MeasureSymmetricTest_test_"
    function_dict = {}
    jsons = [parse_json(x) for x in files if '.json' in x and 'validated' in x]
    for j_file in jsons:
        #print(json.dumps(j_file['invoked_methods'], indent=1))
        for method, invs in j_file['invoked_methods'].items():
            mname = method.replace(rm_val, "")
            for invok in invs.values():
                #print(invok)
                if 'elapsed_time' in invok:
                    function_dict[mname] = {'times': [invok['elapsed_time']], 'energies': [invok['cpu']]} if mname not in function_dict else {'times': function_dict[mname]['times'] + [invok['elapsed_time']] , 'energies': function_dict[mname]['energies'] + [invok['cpu']]}
    return function_dict'''

def extract_values_from_files(files):
    function_dict = {}
    jsons = [(parse_json(x), x) for x in files if '.json' in x]
    for (j_file, jfilename) in jsons:
        basedir = os.path.dirname(jfilename)
        rm_val = "" if len(basedir.split("_")) == 1 else basedir.split("_")[1] + "_" + ("" if 'test' not in basedir else "test") 
        rm_vals = ["_0_2048", "_ECBPKCS1PADDING_0"]
        #print(json.dumps(j_file['invoked_methods'x], indent=1))
        for method, invs in j_file['invoked_methods'].items():
            #print(f"metodo {method}")
            run_id = " ".join(basedir.split("_")[-4:]) if len(basedir.split("_")) <= 7 else "_".join(basedir.split("_")[-5:]) 
            mname = " ".join((reduce(lambda s, sub: s.replace(sub, ''), rm_vals, method  + run_id )).split("_")[2:])
            print(f"metodo {method} - {mname}")
            for invok in invs.values():
                #print(invok)
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


def extract_type_from_testclassname(testclassname):
    "splits word by uppercase letters"
    return ' '.join(re.findall(r'[A-Z][a-z]*', testclassname)[1:-1])
    
def plot_res(unsorted_res, test_type=""):
    filtro = ""
    res =  OrderedDict(sorted(unsorted_res.items(), key=lambda t: t[0]))
    res =  OrderedDict(sorted(unsorted_res.items(), key=lambda t: "".join(reversed(t[0].split(" ")[-2:])), reverse=True))
    keys = [ x for x in list(res.keys()) if filtro in x]
    print(keys)
    times = [ b['times'] for a,b in res.items() if filtro in a]
    consumptions = [ b['energies'] for a,b in res.items() if filtro in a]
    for x, y in unsorted_res.items():
        print(f"{x} - {len(y['energies'])}")
    gen_box_plot(keys, times, f"{test_type} - Elapsed Time " + filtro)
    gen_box_plot(keys, consumptions, f"{test_type} - Energy")

def plot_execs(execs):
    if len(execs) == 0:
        return
    print(execs)
    test_types = set(map(lambda x: x.split("/")[-1].split("_")[1], execs)) if len(execs) > 1 else [execs[0].split("_")[1]]
    print(f"{len(test_types)} test types: {test_types}")
    for test_type in test_types:
        files = []
        for exec_dir in execs:
            files += [os.path.join(exec_dir, x) for x in os.listdir(exec_dir) if '_resume' in x and test_type in exec_dir]
        fc = extract_values_from_files(files)
        plot_res(fc, extract_type_from_testclassname(test_type))
    
def main(basedir, device, provider, algorithm, primitive):
    bdir = '.' if basedir is None else basedir
    good_execs = []
    list_of_runs = [ os.path.join(bdir, x) for x in os.listdir(bdir) if 'Measure' in x and os.path.isdir(os.path.join(bdir, x)) ] if not 'Measure' in bdir else [bdir]
    print(list_of_runs)
    list_of_runs = filter(lambda x: primitive in x and device in x and provider in x and algorithm in x, list_of_runs)
    for run_dir in list_of_runs:
        if process_config_folder(run_dir):
            good_execs.append(run_dir) 
    print("good execs")
    print(good_execs)
    plot_execs(good_execs)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--basedir", help="base directory to look for results", default=".")
    parser.add_argument("-d", "--device", help="device", default="")
    parser.add_argument("-pv", "--provider", help="provider", default="")
    parser.add_argument("-a", "--algorithm", help="algorithm", default="")
    parser.add_argument("-p", "--primitive", help="primitive", default="")
    args = parser.parse_args()
    main(**args.__dict__)