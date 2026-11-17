"""One interface to every path the Python modules use: `from cryptobench.shared import paths`. Roots, repo locations, packaged data,
user and host locations, settings-relative values, the results tree and device folders; a place changes here or nowhere."""
from .device_dirs import DeviceDirs
from .host import android_env, android_home, home, platform_tools, user_cache, user_devices, user_global
from .imports import add_app_imports, with_app_imports
from .names import *  # noqa: F401,F403
from .packaged import *  # noqa: F401,F403
from .repo import Repo, repo
from .results import Results, finished
from .roots import BENCHMARK_ROOT_ENV, CODE_ROOT_ENV, PIPELINE, benchmark_root, checkout_of, code_root
from .run_tree import (Analysis, AppTree, Charts, CheckFolder, Configuration, Discovery, GroupingTree, InteropFolder, Logs, Measurement, Preparation,
                       Review, RunTree, Scoped, app_dir)
from .settings import against, in_temp
