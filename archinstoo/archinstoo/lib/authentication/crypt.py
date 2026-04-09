import ctypes
import ctypes.util
import glob
import secrets
import string
from pathlib import Path
from typing import cast

from archinstoo.lib.output import debug

# Base64-like alphabet used by crypt() salt strings
SALT_CHARS = string.ascii_letters + string.digits + './'

LOGIN_DEFS = Path('/etc/login.defs')


def _try_load_crypt(path: str) -> ctypes.CDLL | None:
	"""Try to load a library and verify crypt() symbol exists."""
	try:
		lib = ctypes.CDLL(path)
		_ = lib['crypt']
		return lib
	except (OSError, KeyError):
		return None


def _load_crypt_lib() -> ctypes.CDLL:
	"""Load a library containing crypt()."""
	# Standard library names
	for name in ('crypt', 'libcrypt.so.2', 'libcrypt.so.1'):
		path = ctypes.util.find_library(name)
		if path and (lib := _try_load_crypt(path)):
			return lib
		if lib := _try_load_crypt(name):
			return lib

	# NixOS: search /nix/store for libxcrypt
	for path in glob.glob('/nix/store/*-libxcrypt-*/lib/libcrypt.so*'):
		if lib := _try_load_crypt(path):
			return lib

	# musl: crypt in libc
	libc_path = ctypes.util.find_library('c')
	if libc_path and (lib := _try_load_crypt(libc_path)):
		return lib

	raise OSError('Could not find crypt()')


def _has_crypt_gensalt(lib: ctypes.CDLL) -> bool:
	"""Check if crypt_gensalt symbol exists."""
	try:
		_ = lib['crypt_gensalt']
		return True
	except KeyError:
		return False


_crypt_lib = _load_crypt_lib()
_crypt_lib.crypt.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
_crypt_lib.crypt.restype = ctypes.c_char_p

_has_gensalt = _has_crypt_gensalt(_crypt_lib)
if _has_gensalt:
	_crypt_lib.crypt_gensalt.argtypes = [ctypes.c_char_p, ctypes.c_ulong, ctypes.c_char_p, ctypes.c_int]
	_crypt_lib.crypt_gensalt.restype = ctypes.c_char_p


def _gen_salt_chars(length: int) -> str:
	return ''.join(secrets.choice(SALT_CHARS) for _ in range(length))


def _search_login_defs(key: str) -> str | None:
	if not LOGIN_DEFS.exists():
		return None
	for line in LOGIN_DEFS.read_text().splitlines():
		line = line.strip()
		if line.startswith('#'):
			continue
		if line.startswith(key):
			return line.split()[1]
	return None


def _gen_salt(prefix: str, rounds: int) -> bytes:
	"""Generate a salt string for crypt()."""
	if _has_gensalt:
		setting = _crypt_lib.crypt_gensalt(prefix.encode(), rounds, None, 0)
		if setting:
			return cast(bytes, setting)

	# Fallback: generate salt manually
	if prefix == '$y$':
		return f'$y$j9T${_gen_salt_chars(22)}'.encode()
	if prefix == '$6$':
		return f'$6$rounds={rounds}${_gen_salt_chars(16)}'.encode()
	raise ValueError(f'Unsupported prefix: {prefix!r}')


def crypt_yescrypt(plaintext: str) -> str:
	"""
	Hash a password with yescrypt (the Arch Linux default via PAM/chpasswd).
	Falls back to SHA-512 on systems where yescrypt is not supported.
	"""
	if (value := _search_login_defs('YESCRYPT_COST_FACTOR')) is not None:
		rounds = max(3, min(11, int(value)))
	else:
		rounds = 5

	debug(f'Creating yescrypt hash with rounds {rounds}')

	salt = _gen_salt('$y$', rounds)
	crypt_hash = _crypt_lib.crypt(plaintext.encode('utf-8'), salt)

	# musl/unsupported: returns *0, *1, or doesn't start with $y$
	if crypt_hash is None or crypt_hash in (b'*0', b'*1') or not crypt_hash.startswith(b'$y$'):
		debug('yescrypt not supported, falling back to SHA-512')
		return crypt_sha512(plaintext)

	return cast(bytes, crypt_hash).decode('utf-8')


def crypt_sha512(plaintext: str, rounds: int = 5000) -> str:
	"""Hash a password with SHA-512. Works everywhere."""
	debug(f'Creating SHA-512 hash with {rounds} rounds')

	salt = _gen_salt('$6$', rounds)
	crypt_hash = _crypt_lib.crypt(plaintext.encode('utf-8'), salt)

	if crypt_hash is None:
		raise ValueError('crypt() returned NULL')

	return cast(bytes, crypt_hash).decode('utf-8')
