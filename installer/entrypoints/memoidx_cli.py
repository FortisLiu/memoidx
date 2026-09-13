"""PyInstaller entrypoint for the MemoIdx CLI.

The filename deliberately does not match the ``memoidx`` package name.  A
same-named entrypoint can shadow the package in a one-file PyInstaller build.
"""

from memoidx.cli import main


raise SystemExit(main())
