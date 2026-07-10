// MBIST Top Module Design
//
// Implement a Memory Built-In-Self-Test (MBIST) controller for a
// 64 x 8-bit single-port SRAM.
//
// Normal mode (default, before a self-test is triggered):
//   - csin/rwbarin/address/datain drive a normal synchronous read/write
//     of the module's internal memory, like a plain single-port SRAM.
//   - dataout reflects the memory's read data.
//
// Self-test mode (triggered by a `start` pulse):
//   - The module must autonomously sweep every address of its internal
//     memory using a sequence of test data patterns, writing each pattern
//     and reading it back to verify the memory responds correctly,
//     without requiring any further external stimulus besides the clock.
//   - `fail` must be asserted while a self-test read-back mismatch is
//     detected (only while `opr` is high), and must stay deasserted
//     whenever the memory behaves correctly.
//   - Once the self-test sweep completes, normal-mode access must resume
//     working correctly.
//
// You may structure the internal implementation however you like (a
// single module, or a decomposition into helper submodules of your own
// design) as long as the `bist` module below keeps exactly this port
// list.
module bist #(parameter size = 6, parameter length = 8) (

  input logic start, rst, clk, csin, rwbarin, opr,
  input logic [size-1:0] address,
  input logic [length-1:0] datain,
  output logic [length-1:0] dataout,
  output logic fail

);

  // TODO: implement the MBIST controller and its internal memory.
  assign fail    = 1'b0;
  assign dataout = '0;

endmodule
