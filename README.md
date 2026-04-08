# partstoob

Experimental branch porting `archinstoo` to run from **any Linux host** (not just Arch ISOs).

| Host | `arch-install-scripts` | `pacman` | Script | Tested |
|------|------------------------|----------|--------|--------|
| Alpine | ✅ | ✅ | [ALP](./ALP) | ✅ |
| Debian | ✅ | ✅ | [DEB](./DEB) | ⚠️ |
| Fedora | ✅ | ✅ | [FED](./FED) | ⚠️ |
| NixOS | ✅ | ✅ | [NIX](./NIX) | ✅ |

For distros that do not package `arch-install-scripts`:

coreutils
util-linux
awk
bash
asciidoc

```shell
git clone --depth 1 https://gitlab.archlinux.org/archlinux/arch-install-scripts.git
cd arch-install-scripts && make PREFIX=/usr/local install
```

See [BOOTSTRAP.md](.github/BOOTSTRAP.md) for details on how this branch is possible.
