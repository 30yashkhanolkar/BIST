from __future__ import annotations

import os
from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb_tools.runner import get_runner


LANGUAGE = os.getenv("HDL_TOPLEVEL_LANG", "verilog").lower().strip()

# Generous upper bound on how many cycles a correct self-test sweep of a
# 64-location memory can take (any reasonable march-style algorithm over a
# handful of test patterns finishes well within this), while still being
# fast to simulate.
SELF_TEST_CYCLES = 2000

# Normal-mode writes/reads don't have to be single-cycle-latency -- a
# fully-registered-output SRAM (address register, then a separate output
# register) is just as valid a design as a same-cycle combinational read
# from a registered address. We give a small, bounded window for either
# convention to settle, rather than demanding one specific pipeline depth.
WRITE_SETTLE_CYCLES = 2
READ_LATENCY_CYCLES = 3


async def _write(dut, address, data):
    dut.csin.value = 1
    dut.rwbarin.value = 0
    dut.address.value = address
    dut.datain.value = data
    for _ in range(WRITE_SETTLE_CYCLES):
        await RisingEdge(dut.clk)


async def _read_and_check(dut, address, expected, message):
    dut.csin.value = 1
    dut.rwbarin.value = 1
    dut.address.value = address
    for _ in range(READ_LATENCY_CYCLES):
        await RisingEdge(dut.clk)
        try:
            value = int(dut.dataout.value)
        except ValueError:
            continue
        if value == expected:
            return
    try:
        actual_str = hex(int(dut.dataout.value))
    except ValueError:
        actual_str = str(dut.dataout.value)
    assert False, (
        f"{message}: expected {hex(expected)}, got {actual_str} within "
        f"{READ_LATENCY_CYCLES} cycles of the read being issued"
    )


@cocotb.test()
async def bist_test(dut):
    """MBIST functionality test (black-box: only touches declared ports)."""

    clock = Clock(dut.clk, 10, unit="us")
    cocotb.start_soon(clock.start(start_high=False))

    dut.rst.value = 1
    dut.start.value = 0
    dut.csin.value = 0
    dut.rwbarin.value = 1
    dut.opr.value = 0
    dut.address.value = 0
    dut.datain.value = 0

    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)

    dut.rst.value = 0

    # NORMAL SRAM WRITE + READ
    await _write(dut, 5, 0xA5)
    await _read_and_check(dut, 5, 0xA5, "Normal-mode read after write to address 5")

    # Write another location
    await _write(dut, 12, 0x3C)
    await _read_and_check(dut, 12, 0x3C, "Normal-mode read after write to address 12")

    # Enter MBIST mode
    dut.start.value = 1
    await RisingEdge(dut.clk)
    dut.start.value = 0

    # Let the self-test run long enough to sweep every address with every
    # test pattern, using only the documented `fail` port -- no
    # internal-signal probing.
    for i in range(SELF_TEST_CYCLES):
        await RisingEdge(dut.clk)
        assert dut.fail.value == 0, f"Memory BIST reported failure at cycle {i}."

    # Once the self-test sweep has finished, normal-mode access must work
    # correctly again -- this catches designs that never release control
    # back to the external interface (or leave stale BIST state behind).
    await _write(dut, 30, 0x7E)
    await _read_and_check(
        dut, 30, 0x7E, "Normal-mode read after self-test completed"
    )


def test_simple_bist_hidden_runner():
    sim = os.getenv("SIM", "icarus")
    proj_path = Path(__file__).resolve().parent.parent
    sources = [proj_path / "sources/bist.sv"]

    runner = get_runner(sim)
    runner.build(
        sources=sources,
        hdl_toplevel="bist",
        always=True,
        timescale=("1us", "1ns"),
    )
    runner.test(hdl_toplevel="bist", test_module="test_simple_bist_hidden")
