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

    # NORMAL SRAM WRITE
    dut.csin.value = 1
    dut.rwbarin.value = 0
    dut.address.value = 5
    dut.datain.value = 0xA5
    await RisingEdge(dut.clk)

    # NORMAL SRAM READ
    dut.rwbarin.value = 1
    await RisingEdge(dut.clk)
    assert int(dut.dataout.value) == 0xA5, f"Expected 0xA5, got {hex(int(dut.dataout.value))}"

    # Write another location
    dut.rwbarin.value = 0
    dut.address.value = 12
    dut.datain.value = 0x3C
    await RisingEdge(dut.clk)
    dut.rwbarin.value = 1
    await RisingEdge(dut.clk)
    assert int(dut.dataout.value) == 0x3C

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
    dut.csin.value = 1
    dut.rwbarin.value = 0
    dut.address.value = 30
    dut.datain.value = 0x7E
    await RisingEdge(dut.clk)
    dut.rwbarin.value = 1
    await RisingEdge(dut.clk)
    assert int(dut.dataout.value) == 0x7E, (
        f"Normal-mode read after self-test completed did not return the "
        f"written value: expected 0x7E, got {hex(int(dut.dataout.value))}"
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
