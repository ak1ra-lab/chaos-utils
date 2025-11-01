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
        Open zstd compressed tar archive name for reading or writing.
        Appending is not allowed.
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
    with tempfile.TemporaryFile() as tmp_file:
        with pyzstd.open(
            name, level_or_option=level_or_option, zstd_dict=zstd_dict
        ) as ifh:
            shutil.copyfileobj(ifh, tmp_file)
        tmp_file.seek(0)
        with tarfile.TarFile(fileobj=tmp_file, **kwargs) as tar:
            yield tar
