# https://pyzstd.readthedocs.io/en/stable/#with-tarfile

import contextlib
import shutil
import tarfile
import tempfile
from tarfile import ReadError, TarFile

import pyzstd
from pyzstd import ZstdError, ZstdFile


class TarFileZstd(TarFile):
    OPEN_METH = {**TarFile.OPEN_METH, "zst": "zstopen"}

    @classmethod
    def zstopen(
        cls,
        name,
        mode="r",
        fileobj=None,
        level_or_option=None,
        zstd_dict=None,
        **kwargs,
    ):
        """
        Open a zstd-compressed tar archive for reading or writing.

        This classmethod extends :class:`tarfile.TarFile` with support for
        zstd-compressed tar archives using :mod:`pyzstd`. The returned object
        behaves like a standard TarFile and can be used to list and extract
        members.

        Notes:
            - Mode must be one of ``'r'``, ``'w'`` or ``'x'``; append mode is
              intentionally not supported.
            - ``fileobj`` may be a file-like object or ``None``. When a
              file-like object is provided it will be wrapped by a
              :class:`pyzstd.ZstdFile` instance.

        Args:
            name: Path-like or file-like object identifying the archive.
            mode: One of ``'r'``, ``'w'``, or ``'x'``.
            fileobj: Optional file-like object to read from or write to.
            level_or_option: Optional compression level (or options) passed
                through to :class:`pyzstd.ZstdFile`.
            zstd_dict: Optional dictionary for zstd compression/decompression.
            **kwargs: Additional arguments forwarded to :meth:`taropen`.

        Returns:
            A :class:`tarfile.TarFile` instance that can operate on the
            decompressed tarstream.

        Raises:
            ValueError: If ``mode`` is not one of the supported values.
            ReadError: If attempting to read a non-zstd file (wrapped from
                :class:`pyzstd.ZstdError` or :class:`EOFError`).
        """
        if mode not in ("r", "w", "x"):
            raise ValueError("mode must be 'r', 'w' or 'x'")

        fileobj = ZstdFile(
            fileobj or name, mode, level_or_option=level_or_option, zstd_dict=zstd_dict
        )

        try:
            tar = cls.taropen(name, mode, fileobj, **kwargs)
        except (ZstdError, EOFError) as err:
            fileobj.close()
            if mode == "r":
                raise ReadError("not a zstd file") from err
            raise
        except:
            fileobj.close()
            raise

        tar._extfileobj = False
        return tar


@contextlib.contextmanager
def ZstdTarReader(name, *, zstd_dict=None, level_or_option=None, **kwargs):
    """
    Context manager that yields a :class:`tarfile.TarFile` for a zstd
    compressed archive.

    This helper decompresses the zstd archive into a temporary file-like
    object and opens it via :class:`tarfile.TarFile`. It is useful when the
    archive consumer expects a ``tarfile`` object rather than a streaming
    wrapper. The temporary file is cleaned up automatically on exit.

    Args:
        name: Path-like or file-like object pointing to the zstd-compressed
            tar archive.
        zstd_dict: Optional dictionary for zstd decompression.
        level_or_option: Optional level or options passed to pyzstd.
        **kwargs: Forwarded to :class:`tarfile.TarFile` when opening the
            decompressed tar stream.

    Yields:
        An open :class:`tarfile.TarFile` instance for the decompressed archive.

    Example:
        >>> with ZstdTarReader('archive.tar.zst') as tar:
        ...     tar.extractall('outdir')
    """
    with tempfile.TemporaryFile() as tmp_file:
        with pyzstd.open(
            name, level_or_option=level_or_option, zstd_dict=zstd_dict
        ) as ifh:
            shutil.copyfileobj(ifh, tmp_file)
        tmp_file.seek(0)
        with tarfile.TarFile(fileobj=tmp_file, **kwargs) as tar:
            yield tar
