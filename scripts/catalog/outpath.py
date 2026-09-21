"""The output-path option that the catalog tools share (`--out` of the extractor and of edit_blueprint.py decode, `--json` of the
validator).

The `/add-blueprint` command runs these tools under an allow rule that pins the path to its scratch directory, but a `*` in a
rule stands for any text: a command can carry the option twice (the last one wins) or a path with `..` in it and still match the
rule. This action closes both gaps in the tool itself: the option is accepted once, and a path with a `..` component is refused.
Standard library only (Python 3.11+).
"""
import argparse
from pathlib import Path


class OutPath(argparse.Action):
    """Stores the path of an output option as a Path, once, and refuses a path that has a `..` component."""

    def __call__(self, parser, namespace, values, option_string=None):
        if getattr(namespace, self.dest, None) is not None:
            parser.error(f'{option_string} was given more than once')
        path = Path(values)
        if '..' in path.parts:
            parser.error(f'{option_string}: a path with a ".." component is refused ({values})')
        setattr(namespace, self.dest, path)
