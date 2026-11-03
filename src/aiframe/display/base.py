"""디스플레이 공통 인터페이스.

담당: 전성재
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from PIL import Image


class Display(ABC):
    width: int
    height: int

    @abstractmethod
    def show(self, image: Image.Image) -> None:
        """1비트 이미지를 화면에 표시한다."""

    def clear(self) -> None:
        self.show(Image.new("1", (self.width, self.height), 1))

    def sleep(self) -> None:
        """저전력 모드로 전환 (E-Paper는 전원이 꺼져도 화면 유지)."""

    def close(self) -> None:
        """자원 해제."""

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
