# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os
import shutil
from pathlib import Path
from typing import Generator

import pytest
import torch
from _pytest.fixtures import SubRequest
from _pytest.monkeypatch import MonkeyPatch

import torchgeo.datasets.utils
from torchgeo.datasets import GID15
from torchgeo.transforms import Identity


def download_url(url: str, root: str, *args: str) -> None:
    shutil.copy(url, root)


class TestGID15:
    @pytest.fixture(params=["train", "val", "test"])
    def dataset(
        self,
        monkeypatch: Generator[MonkeyPatch, None, None],
        tmp_path: Path,
        request: SubRequest,
    ) -> GID15:
        monkeypatch.setattr(  # type: ignore[attr-defined]
            torchgeo.datasets.utils, "download_url", download_url
        )
        md5 = "3d5b1373ef9a3084ec493b9b2056fe07"
        monkeypatch.setattr(GID15, "md5", md5)  # type: ignore[attr-defined]
        url = os.path.join("tests", "data", "gid15", "gid-15.zip")
        monkeypatch.setattr(GID15, "url", url)  # type: ignore[attr-defined]
        root = str(tmp_path)
        split = request.param
        transforms = Identity()
        return GID15(root, split, transforms, download=True, checksum=True)

    def test_getitem(self, dataset: GID15) -> None:
        x = dataset[0]
        assert isinstance(x, dict)
        assert isinstance(x["image"], torch.Tensor)
        assert x["image"].shape[0] == 3

        if dataset.split != "test":
            assert isinstance(x["mask"], torch.Tensor)
            assert x["image"].shape[-2:] == x["mask"].shape[-2:]
        else:
            assert "mask" not in x

    def test_len(self, dataset: GID15) -> None:
        assert len(dataset) == 2

    def test_already_downloaded(self, dataset: GID15) -> None:
        GID15(root=dataset.root, download=True)

    def test_invalid_split(self) -> None:
        with pytest.raises(AssertionError):
            GID15(split="foo")

    def test_not_downloaded(self, tmp_path: Path) -> None:
        with pytest.raises(RuntimeError, match="Dataset not found or corrupted."):
            GID15(str(tmp_path))