// 导出指定地址区间的反汇编(泛化通用)。对付「C 反编译漏参数」时下探 ASM 核对。
// 用法: ... -postScript DumpInstructions.java <outputFile> <start> <end>

import java.io.File;
import java.io.PrintWriter;

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;

public class DumpInstructions extends GhidraScript {
    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 3) throw new IllegalArgumentException("Expected outputFile start end");
        File output = new File(args[0]);
        output.getParentFile().mkdirs();
        Address start = toAddr(args[1]);
        Address end = toAddr(args[2]);
        try (PrintWriter out = new PrintWriter(output, "UTF-8")) {
            InstructionIterator instructions = currentProgram.getListing().getInstructions(start, true);
            while (instructions.hasNext()) {
                Instruction instruction = instructions.next();
                if (instruction.getAddress().compareTo(end) > 0) break;
                out.printf("%s  %-10s %s%n", instruction.getAddress(),
                    instruction.getMnemonicString(), instruction.toString().substring(instruction.getMnemonicString().length()).trim());
            }
        }
    }
}
