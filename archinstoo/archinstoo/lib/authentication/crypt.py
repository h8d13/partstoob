import ctypes
import ctypes.util
import secrets
import string
from typing import cast

from archinstoo.lib.output import debug

# Base64-like alphabet used by crypt() salt strings
SALT_CHARS = string.ascii_letters + string.digits + './'


def _load_crypt_lib() -> ctypes.CDLL:
	"""Load a library containing crypt(). Tries libcrypt first, then libc."""
	# glibc systems (including NixOS) have crypt in libcrypt
	for name in ('crypt', 'libcrypt.so.2', 'libcrypt.so.1'):
		try:
			path = ctypes.util.find_library(name) or name
			lib = ctypes.CDLL(path)
			lib.crypt  # check symbol exists
			return lib
		except (OSError, AttributeError):
			continue

	# musl systems have crypt in libc
	libc_path = ctypes.util.find_library('c')
	if libc_path:
		return ctypes.CDLL(libc_path)

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
