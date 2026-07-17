// 按入口地址导出反编译结果(泛化通用,无项目特有内容)。
// 用法: ... -postScript ExportFunctionsByAddress.java <outputDir> <addr1> [<addr2> ...]

import java.io.File;
import java.io.PrintWriter;

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;

public class ExportFunctionsByAddress extends GhidraScript {
    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length < 2) throw new IllegalArgumentException("Expected outputDir and addresses");
        File outputDir = new File(args[0]);
        outputDir.mkdirs();
        DecompInterface decompiler = new DecompInterface();
        decompiler.toggleCCode(true);
        decompiler.toggleSyntaxTree(true);
        if (!decompiler.openProgram(currentProgram)) throw new IllegalStateException("Cannot open program");
        try {
            for (int i = 1; i < args.length; ++i) {
                Address address = toAddr(args[i]);
                Function function = currentProgram.getFunctionManager().getFunctionAt(address);
                if (function == null) {
                    function = currentProgram.getFunctionManager().getFunctionContaining(address);
                }
                File output = new File(outputDir, args[i] + ".c");
                try (PrintWriter out = new PrintWriter(output, "UTF-8")) {
                    if (function == null) {
                        out.println("// No function found at " + address);
                        continue;
                    }
                    DecompileResults result = decompiler.decompileFunction(function, 120, monitor);
                    out.println("// requested: " + address);
                    out.println("// entry: " + function.getEntryPoint());
                    out.println("// name: " + function.getSymbol().getName(true));
                    out.println("// prototype: " + function.getPrototypeString(false, false));
                    out.println();
                    if (result.decompileCompleted() && result.getDecompiledFunction() != null) {
                        out.println(result.getDecompiledFunction().getC());
                    } else {
                        out.println("// error: " + result.getErrorMessage());
                    }
                }
            }
        } finally {
            decompiler.dispose();
        }
    }
}
