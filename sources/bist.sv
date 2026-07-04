// MBIST Top Module Design
module bist #(parameter size = 6, parameter length = 8) (

  input logic start, rst, clk, csin, rwbarin, opr,
  input logic [size-1:0] address,
  input logic [length-1:0] datain,
  output logic [length-1:0] dataout,
  output logic fail

);

  logic [size-1:0]   ramaddr;
  logic [length-1:0] data_t, ramout, ramin;
  logic [9:0]         q;
  logic               gt, eq, lt;
  logic               we, cs, cout, NbarT, ld;
  logic               phase_verify;

  // q[9:7] selects the pattern under test, q[6] selects write(0)/verify(1)
  // phase, q[5:0] sweeps every RAM address.
  assign phase_verify = q[6];

  comparator comp (
    .data_t (data_t),
    .ramout (ramout),
    .gt     (gt),
    .eq     (eq),
    .lt     (lt)
  );

  counter #(.length(10)) count (
    .d_in (10'b0),
    .clk  (clk),
    .ld   (ld),
    .u_d  (1'b1),
    .cen  (NbarT),
    .q    (q),
    .cout (cout)
  );

  multiplexer #(.WIDTH(size)) mux_addr (
    .normal_in (address),
    .bist_in   (q[size-1:0]),
    .NbarT     (NbarT),
    .out       (ramaddr)
  );

  multiplexer #(.WIDTH(length)) mux_data (
    .normal_in (datain),
    .bist_in   (data_t),
    .NbarT     (NbarT),
    .out       (ramin)
  );

  decoder dec (
    .q      (q[9:7]),
    .data_t (data_t)
  );

  controller contr (
    .start (start),
    .rst   (rst),
    .clk   (clk),
    .cout  (cout),
    .NbarT (NbarT),
    .ld    (ld)
  );

  sram sram1 (
    .ramaddr (ramaddr),
    .ramin   (ramin),
    .rwbar   (we),
    .clk     (clk),
    .cs      (cs),
    .ramout  (ramout)
  );

  // In self-test mode the BIST engine drives the SRAM directly; in normal
  // mode the external csin/rwbarin control the SRAM.
  assign we = NbarT ? phase_verify : rwbarin;
  assign cs = NbarT ? 1'b1         : csin;

  always_ff @(posedge clk) begin
    if (rst) begin
      fail <= 1'b0;
    end else if (NbarT && opr && phase_verify && !eq) begin
      fail <= 1'b1;
    end else begin
      fail <= 1'b0;
    end
  end

  assign dataout = ramout;

endmodule

//Comparator Module
module comparator(

  input logic [7:0] data_t,
  input logic [7:0] ramout,
  output logic gt, eq, lt

);

  assign gt = (data_t > ramout);
  assign eq = (data_t == ramout);
  assign lt = (data_t < ramout);

endmodule

//Counter Module
module counter #(parameter length = 10) (

  input logic [length-1:0] d_in,
  input logic clk, ld, u_d, cen,
  output logic [length-1:0] q,
  output logic cout

);

  logic [length:0] cnt;

  always_ff @(posedge clk) begin
    if (ld) begin
      cnt <= {1'b0, d_in};
    end else if (cen) begin
      if (u_d) begin
        cnt <= cnt + 1'b1;
      end else begin
        cnt <= cnt - 1'b1;
      end
    end
  end

  assign q    = cnt[length-1:0];
  assign cout = cnt[length];

endmodule

//Multiplexer module
module multiplexer #(parameter WIDTH = 8) (

  input logic [WIDTH-1:0] normal_in,
  input logic [WIDTH-1:0] bist_in,
  input logic NbarT,
  output logic [WIDTH-1:0] out


);

  assign out = NbarT ? bist_in : normal_in;

endmodule

//Decoder Module
module decoder(

  input logic [2:0] q,
  output logic [7:0] data_t

);

  always_comb begin

    case (q)
      3'b000: data_t = 8'b10101010;
      3'b001: data_t = 8'b01010101;
      3'b010: data_t = 8'b11110000;
      3'b011: data_t = 8'b00001111;
      3'b100: data_t = 8'b00000000;
      3'b101: data_t = 8'b11111111;
      3'b110: data_t = 8'b11001100;
      3'b111: data_t = 8'b00110011;
    endcase

  end

endmodule


//Controller Module
module controller (

  input  logic start, rst, clk, cout,
  output logic NbarT, ld

);

  typedef enum logic {RESET, TEST} state_t;

  state_t current_state, next_state;

  always_ff @(posedge clk or posedge rst) begin
    if (rst) begin
      current_state <= RESET;
    end else begin
      current_state <= next_state;
    end
  end

  always_comb begin
    case (current_state)

      RESET: begin
        if (start) next_state = TEST;
        else next_state = RESET;
      end

      TEST: begin
        if (cout) next_state = RESET;
        else next_state = TEST;
      end

      default: next_state = RESET;

    endcase
  end

  assign NbarT = (current_state == TEST);
  assign ld    = (current_state == RESET);

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

  always_ff @(posedge clk) begin
    if (cs) begin
      addr_reg <= ramaddr;
    end

    if (cs && !rwbar) begin
      ram[ramaddr] <= ramin;
    end
  end

  assign ramout = (cs && rwbar) ? ram[addr_reg] : 8'b0;

endmodule
