# SPDX-License-Identifier: MIT
# Mount the TF card (4-bit SDMMC) at /sd and list it.
import os
import board
import sdioio
import storage

sd = sdioio.SDCard(
    clock=board.SD_CLK,
    command=board.SD_CMD,
    data=[board.SD_D0, board.SD_D1, board.SD_D2, board.SD_D3],
    frequency=25_000_000,
)
storage.mount(storage.VfsFat(sd), "/sd")
print(os.listdir("/sd"))
