from __future__ import annotations

import os
import random
from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb_tools.runner import get_runner


LANGUAGE = os.getenv("HDL_TOPLEVEL_LANG", "verilog").lower().strip()


@cocotb.test()
async def bist_test(dut):
    """Basic MBIST functionality test."""


    # Start 10 us clock
    clock = Clock(dut.clk, 10, unit="us")
    cocotb.start_soon(clock.start(start_high=False))

    # Reset DUT
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
    dut.rwbarin.value = 0          # Write
    dut.address.value = 5
    dut.datain.value = 0xA5

    await RisingEdge(dut.clk)

    # NORMAL SRAM READ
    dut.rwbarin.value = 1          # Read

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

   
    # Controller should enter TEST state
    for _ in range(5):
        await RisingEdge(dut.clk)

    assert dut.NbarT.value == 1, "MBIST did not enter TEST mode"

    # Observe MBIST running
    for i in range(20):

        await RisingEdge(dut.clk)

        cocotb.log.info(
            f"Cycle {i:02d} "
            f"Addr={int(dut.ramaddr.value):02d} "
            f"Pattern=0x{int(dut.data_t.value):02X} "
            f"WE={int(dut.we.value)} "
            f"FAIL={int(dut.fail.value)}"
        )


    assert dut.fail.value == 0, "Memory BIST reported failure."


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