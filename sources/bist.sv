// MBIST Top Module Design
module bist #(parameter size = 6, parameter length = 8) (
  
  input logic start, rst, clk, csin, rwbarin, opr,
  input logic [size-1:0] address,
  input logic [length-1:0] datain,
  output logic [length-1:0] dataout,
  output logic fail  
  
);
  
  // Internal logic
  
endmodule

//Comparator Module
module comparator(
  
  input logic [7:0] data_t,
  input logic [7:0] ramout,
  output logic gt, eq, lt
  
);
  
  // Internal logic
  
endmodule

//Counter Module
module counter #(parameter length = 10) (
  
  input logic [length-1:0] d_in,
  input logic clk, ld, u_d, cen,
  output logic [length-1:0] q,
  output logic cout
  
);
  
  // Internal logic
  
endmodule

//Multiplexer module
module multiplexer #(parameter WIDTH = 8) (
  
  input logic [WIDTH-1:0] normal_in,
  input logic [WIDTH-1:0] bist_in,
  input logic NbarT,
  output logic [WIDTH-1:0] out
               
               
);
  
 // Internal logic

endmodule

//Decoder Module
module decoder(
  
  input logic [2:0] q,
  output logic [7:0] data_t
  
);
  
  // Internal logic
  
endmodule


//Controller Module
module controller (
  
  input  logic start, rst, clk, cout,
  output logic NbarT, ld
 
);

 
  // Internal logic

endmodule

//SRAM Module
module sram(
  
  input logic [5:0] ramaddr,
  input logic [7:0] ramin,
  input logic rwbar, clk, cs,
  output logic [7:0] ramout
  
);
  
  logic [7:0] ram [63:0];
  logic [5:0] addr_reg;
  
  // Internal logic
  
endmodule
