# How to Rime with Weasel

## Preparation

  - Install **Visual Studio 2017** or newer version for *Desktop development in C++*
    with components *ATL*, *MFC*

  - Install dev tools: `git`, `clang-format(>=18.0.0)`

  - Download third-party libraries: `boost(>=1.78.0)`

Optional:

  - install `bash` via *Git for Windows*, for installing data files with `plum`;
  - install [NSIS](http://nsis.sourceforge.net/Download) for creating installer.

## Checkout source code

Make sure all git submodules are checked out recursively.

```batch
git clone --recursive https://github.com/rime/weasel.git
```

## Build and Install Weasel

Locate `weasel` source directory.

### Setup build environment

Edit your build environment settings in `env.bat`.
You can create the file by copying `env.bat.template` in the source tree.

Make sure `BOOST_ROOT` is set to the existing path `X:\path\to\boost_<version>`.

When using a different version of Visual Studio or platform toolset, un-comment
lines to set corresponding variables.

Alternatively, start a *Developer Command Prompt* window and set environment
variables directly in the console, before invocation of `build.bat`:

```batch
set BOOST_ROOT=X:\path\to\boost_N_NN_N
```

Get prebuilt librime files(headers, libs, pdb and opencc files) with `get-rime.ps1` in `weasel` source directory
```cmd
powershell .\get-rime.ps1 -use dev
```



