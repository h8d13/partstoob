# partstoob

Experimental ports `archinstoo` to run from **any Linux host** (not just Arch ISOs).

> Mostly tested from smallest server type ISOs.

| Host | `arch-install-scripts` | `pacman` | Script | Tested |
|------|------------------------|----------|--------|--------|
| Alpine | ✅ | ✅ | [ALP](./ALP) | ✅ |
| Debian | ✅ | ✅ | [DEB](./DEB) | ✅ |
| Fedora | ✅ | ✅ | [FED](./FED) | ⚠️ |
| NixOS | ✅ | ✅ | [NIX](./NIX) | ✅ |
| openSUSE | ✅ | ✅ | [OPE](./OPE) | ⚠️ |

For distros that do not package `arch-install-scripts`:

coreutils
util-linux
awk
bash
asciidoc
make
mz4

```shell

sudo env | grep "PATH="

git clone --depth 1 https://gitlab.archlinux.org/archlinux/arch-install-scripts.git
cd arch-install-scripts && sudo make PREFIX=/usr/bin install

# make sure this install PREFIX location is in PATH
```

See [BOOTSTRAP.md](.github/BOOTSTRAP.md) for details on how this branch is possible.
