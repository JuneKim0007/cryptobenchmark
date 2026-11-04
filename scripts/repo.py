"""The repository root every script resolves its paths against."""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
