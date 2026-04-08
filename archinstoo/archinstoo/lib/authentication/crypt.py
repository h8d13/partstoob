import ctypes
import ctypes.util
import glob
import secrets
import string
from typing import cast

from archinstoo.lib.output import debug

# Base64-like alphabet used by crypt() salt strings
SALT_CHARS = string.ascii_letters + string.digits + './'


def _try_load_crypt(path: str) -> ctypes.CDLL | None:
	"""Try to load a library and verify crypt() symbol exists."""
	try:
		lib = ctypes.CDLL(path)
		# Actually verify the symbol by looking it up
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


_crypt_lib = _load_crypt_lib()
_crypt_lib.crypt.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
_crypt_lib.crypt.restype = ctypes.c_char_p


def _gen_salt_chars(length: int) -> str:
	return ''.join(secrets.choice(SALT_CHARS) for _ in range(length))


def crypt_sha512(plaintext: str, rounds: int = 5000) -> str:
	"""Hash a password with SHA-512. Works everywhere."""
	debug(f'Creating SHA-512 hash with {rounds} rounds')

	salt = f'$6$rounds={rounds}${_gen_salt_chars(16)}'.encode()
	crypt_hash = _crypt_lib.crypt(plaintext.encode('utf-8'), salt)

	if crypt_hash is None:
		raise ValueError('crypt() returned NULL')

	return cast(bytes, crypt_hash).decode('utf-8')
