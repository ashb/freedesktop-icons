import ctypes
import mmap
import pathlib
import struct
from functools import cache

import attr


@attr.s(auto_attribs=True, hash=False)
class GtkIconCache:
    theme_dir: pathlib.Path = attr.ib(converter=pathlib.Path)

    class Header(ctypes.BigEndianStructure):
        _fields_ = [
            ('version_major', ctypes.c_uint16),
            ('version_minor', ctypes.c_uint16),
            ('hash_offset', ctypes.c_uint32),
            ('dir_list_offset', ctypes.c_uint32),
        ]

        @property
        def version(self):
            return (self.version_major, self.version_minor)

    def __hash__(self):
        return self.data.__hash__()

    def __attrs_post_init__(self):
        self.fh = open(self.theme_dir / "icon-theme.cache", "rb")
        self.data = mmap.mmap(self.fh.fileno(), 0, access=mmap.ACCESS_READ)
        # ctypes cant re-use read-only buffers, but this is only 12 bytes
        self.header = self.Header.from_buffer_copy(self.data[0 : ctypes.sizeof(self.Header)])

        self._check_version()

        self.num_hash_buckets = self._read_uint32(self.header.hash_offset)
        self.num_dirs = self._read_uint32(self.header.dir_list_offset)

    def _check_version(self):
        if self.header.version_major != 1:
            raise RuntimeWarning(f'{self.theme_dir / "icon-theme.cache"} is major version {self.header.version_major} is unsupported')

    @cache
    def _dir_name_from_index(self, index):
        if index >= self.num_dirs:
            raise ValueError(f'dir_index {index} is too large!')

        offset = self._read_uint32(self.header.dir_list_offset + 4 + (index * 4))
        return self._read_cstring(offset)

    def _read_uint16(self, offset):
        return struct.unpack(">H", self.data[offset : offset + 2])[0]

    def _read_uint32(self, offset):
        return struct.unpack(">L", self.data[offset : offset + 4])[0]

    def _read_cstring(self, offset):
        nul_byte = self.data.find(b'\x00', offset)

        return self.data[offset:nul_byte].decode('utf-8')

    @staticmethod
    def _icon_hash_name(icon: str):
        """
        Hash a string according to the rules used in the cache file

        >>> GtkIconCache._icon_hash_name('button-ok')
        11528791
        >>> GtkIconCache._icon_hash_name('')
        0
        """
        b = icon.encode('utf-8')
        h = 0

        for p in b:
            # Need to clamp the bitshit to 32 bit unsigned integer
            h = ((h << 5) & 0xFFFFFFFF) - h + p

        return h

    def lookup(self, icon):
        hash = self._icon_hash_name(icon)

        bucket_idx = hash % self.num_hash_buckets

        # typedef struct {
        #   gint size;
        #   HashNode **nodes;
        # } HashContext;
        bucket_offset = self._read_uint32(self.header.hash_offset + 4 + (bucket_idx * 4))

        while bucket_offset >= 0 and bucket_offset < len(self.data) - 12:

            # struct _HashNode
            # {
            #   HashNode *next;
            #   gchar *name;
            #   GList *image_list;
            #   gint offset;
            # };

            name_offset = self._read_uint32(bucket_offset + 4)

            val = self._read_cstring(name_offset)
            if val == icon:
                # Found the matching bucket
                image_list_offset = self._read_uint32(bucket_offset + 8)
                list_len = self._read_uint32(image_list_offset)

                for i in range(list_len):
                    yield self._dir_name_from_index(self._read_uint16(image_list_offset + 4 + (8 * i)))

            # Read next pointer
            bucket_offset = self._read_uint32(bucket_offset)
