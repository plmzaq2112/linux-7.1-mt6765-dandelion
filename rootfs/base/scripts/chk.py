import ctypes
lib = ctypes.CDLL("libcrypt.so.1")
lib.crypt.restype = ctypes.c_char_p
setting = b"$y$j9T$E4HnI4DZGlSUkQwnlD3rk.$"
stored = b"$y$j9T$E4HnI4DZGlSUkQwnlD3rk.$DIKBg9DJRAJssquEZ/mHdZuBoxhv1IRCuyB.5HgwvQ/"
for pw in (b"1234", b"0000", b"dandelion", b"12345"):
    h = lib.crypt(pw, setting)
    print(pw.decode(), "match" if h == stored else "no")
