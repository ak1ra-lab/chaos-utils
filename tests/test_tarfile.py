import io
import tarfile
from unittest.mock import patch

import pytest
import pyzstd

from chaos_utils.tarfile import TarFileZstd, ZstdTarReader


@pytest.fixture
def sample_tar(tmp_path):
    """
    Create a tar file with two files for testing.
    """
    tar_path = tmp_path / "test.tar"
    with tarfile.open(tar_path, "w") as tar:
        info = tarfile.TarInfo("foo.txt")
        data = b"hello foo"
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))

        info = tarfile.TarInfo("bar.txt")
        data = b"hello bar"
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))
    return tar_path


@pytest.fixture
def sample_tar_zst(tmp_path, sample_tar):
    """
    Compress the tar file to zst format using pyzstd.
    """
    zst_path = tmp_path / "test.tar.zst"
    with open(sample_tar, "rb") as f_in, pyzstd.open(zst_path, "wb") as f_out:
        f_out.write(f_in.read())
    return zst_path


def test_tarfilezstd_read(sample_tar_zst):
    """
    Test reading zst-compressed tar archive with TarFileZstd.
    """
    with TarFileZstd.zstopen(sample_tar_zst, "r") as tar:
        names = tar.getnames()
        assert "foo.txt" in names
        assert "bar.txt" in names
        foo = tar.extractfile("foo.txt").read()
        bar = tar.extractfile("bar.txt").read()
        assert foo == b"hello foo"
        assert bar == b"hello bar"


def test_tarfilezstd_write(tmp_path):
    """
    Test writing zst-compressed tar archive with TarFileZstd.
    """
    zst_path = tmp_path / "out.tar.zst"
    with TarFileZstd.zstopen(zst_path, "w") as tar:
        info = tarfile.TarInfo("abc.txt")
        data = b"abc123"
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))
    # Check if zst_path can be read
    with TarFileZstd.zstopen(zst_path, "r") as tar:
        assert tar.getnames() == ["abc.txt"]
        assert tar.extractfile("abc.txt").read() == b"abc123"


def test_zstdtarreader(sample_tar_zst):
    """
    Test reading zst-compressed tar archive with ZstdTarReader.
    """
    with ZstdTarReader(sample_tar_zst) as tar:
        names = tar.getnames()
        assert set(names) == {"foo.txt", "bar.txt"}
        assert tar.extractfile("foo.txt").read() == b"hello foo"


def test_tarfilezstd_invalid_mode(tmp_path):
    """
    Test TarFileZstd.zstopen with invalid mode and invalid file.
    """
    zst_path = tmp_path / "fail.tar.zst"
    with open(zst_path, "wb") as f:
        f.write(b"notazst")
    with pytest.raises(ValueError):
        TarFileZstd.zstopen(zst_path, "a")
    with pytest.raises(tarfile.ReadError):
        TarFileZstd.zstopen(zst_path, "r")


def test_zstopen_bare_except_closes_fileobj(tmp_path):
    """An unexpected exception during taropen triggers the bare except clause,
    closing the ZstdFile and re-raising the original error."""
    zst_path = tmp_path / "dummy.tar.zst"
    # Create a valid zst file so ZstdFile opens without error
    import io

    import pyzstd

    buf = io.BytesIO()
    with pyzstd.open(buf, "wb") as f:
        f.write(b"not a tar archive")
    zst_path.write_bytes(buf.getvalue())

    with patch.object(TarFileZstd, "taropen", side_effect=RuntimeError("unexpected")):
        with pytest.raises(RuntimeError, match="unexpected"):
            TarFileZstd.zstopen(zst_path, "r")


def test_zstopen_zstd_error_in_write_mode_reraises(tmp_path):
    """ZstdError during taropen in write mode re-raises (not wrapped in ReadError)."""
    from pyzstd import ZstdError

    zst_path = tmp_path / "new.tar.zst"

    with patch.object(TarFileZstd, "taropen", side_effect=ZstdError("zstd bad")):
        with pytest.raises(ZstdError, match="zstd bad"):
            TarFileZstd.zstopen(zst_path, "w")
