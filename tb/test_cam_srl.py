#!/usr/bin/env python
"""

Copyright (c) 2015-2016 Alex Forencich

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

"""

from myhdl import *
import os

module = 'cam_srl'
testbench = 'test_%s' % module

srcs = []

srcs.append("../rtl/%s.v" % module)
srcs.append("../rtl/priority_encoder.v")
srcs.append("%s.v" % testbench)

src = ' '.join(srcs)

build_cmd = "iverilog -o %s.vvp %s" % (testbench, src)

def bench():

    # Parameters
    DATA_WIDTH = 64
    ADDR_WIDTH = 5
    SLICE_WIDTH = 4

    # Inputs
    clk = Signal(bool(0))
    rst = Signal(bool(0))
    current_test = Signal(intbv(0)[8:])

    write_addr = Signal(intbv(0)[ADDR_WIDTH:])
    write_data = Signal(intbv(0)[DATA_WIDTH:])
    write_delete = Signal(bool(0))
    write_enable = Signal(bool(0))
    compare_data = Signal(intbv(0)[DATA_WIDTH:])

    # Outputs
    write_busy = Signal(bool(1))
    match_many = Signal(intbv(0)[2**ADDR_WIDTH:])
    match_single = Signal(intbv(0)[2**ADDR_WIDTH:])
    match_addr = Signal(intbv(0)[ADDR_WIDTH:])
    match = Signal(bool(0))

    # DUT
    if os.system(build_cmd):
        raise Exception("Error running build command")

    dut = Cosimulation(
        "vvp -m myhdl %s.vvp -lxt2" % testbench,
        clk=clk,
        rst=rst,
        current_test=current_test,
        write_addr=write_addr,
        write_data=write_data,
        write_delete=write_delete,
        write_enable=write_enable,
        write_busy=write_busy,
        compare_data=compare_data,
        match_many=match_many,
        match_single=match_single,
        match_addr=match_addr,
        match=match
    )

    @always(delay(4))
    def clkgen():
        clk.next = not clk

    @instance
    def check():
        yield delay(100)
        yield clk.posedge
        rst.next = 1
        yield clk.posedge
        rst.next = 0
        yield clk.posedge
        yield delay(100)
        yield clk.posedge

        while write_busy:
            yield clk.posedge
        yield clk.posedge

        yield clk.posedge
        print("test 1: write")
        current_test.next = 1

        # write some data
        write_addr.next = 0
        write_data.next = 0x0123456789ABCDEF
        write_delete.next = 0
        write_enable.next = 1
        yield clk.posedge
        write_enable.next = 0
        yield clk.posedge
        while write_busy:
            yield clk.posedge

        write_addr.next = 1
        write_data.next = 0x1111111111111111
        write_delete.next = 0
        write_enable.next = 1
        yield clk.posedge
        write_enable.next = 0
        yield clk.posedge
        while write_busy:
            yield clk.posedge

        write_addr.next = 2
        write_data.next = 0x2222222222222222
        write_delete.next = 0
        write_enable.next = 1
        yield clk.posedge
        write_enable.next = 0
        yield clk.posedge
        while write_busy:
            yield clk.posedge

        yield delay(100)

        yield clk.posedge
        print("test 2: match")
        current_test.next = 2

        compare_data.next = 0x0123456789ABCDEF
        yield clk.posedge
        yield clk.posedge
        assert match
        assert match_many == 1 << 0;
        assert match_single == 1 << 0;
        assert match_addr == 0;

        compare_data.next = 0x1111111111111111
        yield clk.posedge
        yield clk.posedge
        assert match
        assert match_many == 1 << 1;
        assert match_single == 1 << 1;
        assert match_addr == 1;
        
        compare_data.next = 0x2222222222222222
        yield clk.posedge
        yield clk.posedge
        assert match
        assert match_many == 1 << 2;
        assert match_single == 1 << 2;
        assert match_addr == 2;

        yield delay(100)

        yield clk.posedge
        print("test 3: match multiple")
        current_test.next = 3

        write_addr.next = 22
        write_data.next = 0x2222222222222222
        write_delete.next = 0
        write_enable.next = 1
        yield clk.posedge
        write_enable.next = 0
        yield clk.posedge
        while write_busy:
            yield clk.posedge
        
        compare_data.next = 0x2222222222222222
        yield clk.posedge
        yield clk.posedge
        assert match
        assert match_many == 1 << 2 | 1 << 22;
        assert match_single == 1 << 2;
        assert match_addr == 2;

        yield delay(100)

        yield clk.posedge
        print("test 4: delete")
        current_test.next = 4

        write_addr.next = 0
        write_data.next = 0
        write_delete.next = 1
        write_enable.next = 1
        yield clk.posedge
        write_enable.next = 0
        yield clk.posedge
        while write_busy:
            yield clk.posedge
        
        compare_data.next = 0x0123456789ABCDEF
        yield clk.posedge
        yield clk.posedge
        assert not match

        yield delay(100)

        yield clk.posedge
        print("test 5: isolation")
        current_test.next = 5

        write_addr.next = 0
        write_data.next = 0x0000000000000000
        write_delete.next = 0
        write_enable.next = 1
        yield clk.posedge
        write_enable.next = 0
        yield clk.posedge
        while write_busy:
            yield clk.posedge

        write_addr.next = 1
        write_data.next = 0x0000000000000001
        write_delete.next = 0
        write_enable.next = 1
        yield clk.posedge
        write_enable.next = 0
        yield clk.posedge
        while write_busy:
            yield clk.posedge

        write_addr.next = 2
        write_data.next = 0x0000000000000002
        write_delete.next = 0
        write_enable.next = 1
        yield clk.posedge
        write_enable.next = 0
        yield clk.posedge
        while write_busy:
            yield clk.posedge
        
        compare_data.next = 0x0000000000000000
        yield clk.posedge
        yield clk.posedge
        assert match
        assert match_many == 1 << 0;
        assert match_single == 1 << 0;
        assert match_addr == 0;
        
        compare_data.next = 0x0000000000000001
        yield clk.posedge
        yield clk.posedge
        assert match
        assert match_many == 1 << 1;
        assert match_single == 1 << 1;
        assert match_addr == 1;
        
        compare_data.next = 0x0000000000000002
        yield clk.posedge
        yield clk.posedge
        assert match
        assert match_many == 1 << 2;
        assert match_single == 1 << 2;
        assert match_addr == 2;

        write_addr.next = 1
        write_data.next = 0
        write_delete.next = 1
        write_enable.next = 1
        yield clk.posedge
        write_enable.next = 0
        yield clk.posedge
        while write_busy:
            yield clk.posedge
        
        compare_data.next = 0x0000000000000000
        yield clk.posedge
        yield clk.posedge
        assert match
        assert match_many == 1 << 0;
        assert match_single == 1 << 0;
        assert match_addr == 0;
        
        compare_data.next = 0x0000000000000001
        yield clk.posedge
        yield clk.posedge
        assert not match
        
        compare_data.next = 0x0000000000000002
        yield clk.posedge
        yield clk.posedge
        assert match
        assert match_many == 1 << 2;
        assert match_single == 1 << 2;
        assert match_addr == 2;

        yield delay(100)

        raise StopSimulation

    return dut, clkgen, check

def test_bench():
    sim = Simulation(bench())
    sim.run()

if __name__ == '__main__':
    print("Running test...")
    test_bench()
