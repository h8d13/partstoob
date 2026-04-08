import ctypes
import ctypes.util
import secrets
import string
from typing import cast

from archinstoo.lib.output import debug

# Base64-like alphabet used by crypt() salt strings
SALT_CHARS = string.ascii_letters + string.digits + './'


def _load_libc() -> ctypes.CDLL:
	"""Load libc which contains crypt() on all platforms."""
	libc_path = ctypes.util.find_library('c')
	if libc_path:
		return ctypes.CDLL(libc_path)
	raise OSError('Could not find libc')


libc = _load_libc()
libc.crypt.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
libc.crypt.restype = ctypes.c_char_p


def _gen_salt_chars(length: int) -> str:
	return ''.join(secrets.choice(SALT_CHARS) for _ in range(length))


def crypt_sha512(plaintext: str, rounds: int = 5000) -> str:
	"""Hash a password with SHA-512. Works everywhere."""
	debug(f'Creating SHA-512 hash with {rounds} rounds')

	salt = f'$6$rounds={rounds}${_gen_salt_chars(16)}'.encode()
	crypt_hash = libc.crypt(plaintext.encode('utf-8'), salt)

	if crypt_hash is None:
		raise ValueError('crypt() returned NULL')

	return cast(bytes, crypt_hash).decode('utf-8')
